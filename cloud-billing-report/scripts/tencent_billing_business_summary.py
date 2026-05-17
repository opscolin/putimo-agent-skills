#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云账单汇总数据导出工具

从腾讯云 API 获取账单汇总数据并保存为 CSV 文件

环境变量:
    TENCENTCLOUD_SECRET_ID: 腾讯云 Secret ID
    TENCENTCLOUD_SECRET_KEY: 腾讯云 Secret Key

Usage:
    # 生成指定月份的账单汇总 (月份格式：YYYY-MM)
    python tencent_billing_business_summary.py 2026-02
    
    # 生成上个月的账单汇总
    python tencent_billing_business_summary.py last
    
    # 生成当前月份的账单汇总
    python tencent_billing_business_summary.py current
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.billing.v20180709 import billing_client, models


def get_month_str(month_arg: str) -> str:
    """
    解析月份参数，返回 YYYY-MM 格式
    
    Args:
        month_arg: 月份参数 ('last', 'current', 或 'YYYY-MM')
    
    Returns:
        YYYY-MM 格式的月份字符串
    """
    today = datetime.now()
    
    if month_arg.lower() == 'last':
        # 上个月
        last_month = today - timedelta(days=today.day)
        return last_month.strftime('%Y-%m')
    elif month_arg.lower() == 'current':
        # 当前月份
        return today.strftime('%Y-%m')
    else:
        # 验证格式
        try:
            datetime.strptime(month_arg, '%Y-%m')
            return month_arg
        except ValueError:
            raise ValueError(f"无效的月份格式：{month_arg}，请使用 YYYY-MM 格式")


def get_output_filename(month: str, summary_type: str = 'business') -> str:
    """
    生成输出文件名
    
    Args:
        month: YYYY-MM 格式的月份
        summary_type: 'business' 或 'product'
    
    Returns:
        输出文件名
    """
    # 转换 YYYY-MM 为 YYYYMM
    month_short = month.replace('-', '')
    return f"tencent_billing_{month_short}_{summary_type}_summary.csv"


def fetch_business_summary(month: str, output_dir: str = '.') -> str:
    """
    获取账单汇总数据并保存为 CSV
    
    Args:
        month: YYYY-MM 格式的月份
        output_dir: 输出目录
    
    Returns:
        输出的文件路径
    """
    try:
        # 从环境变量读取密钥
        cred = credential.Credential(
            os.getenv("TENCENTCLOUD_SECRET_ID"), 
            os.getenv("TENCENTCLOUD_SECRET_KEY")
        )
        
        # 配置 HTTP 和 Client
        httpProfile = HttpProfile()
        httpProfile.endpoint = "billing.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = billing_client.BillingClient(cred, "", clientProfile)
        
        # 构建请求
        req = models.DescribeBillSummaryRequest()
        params = {
            "Month": month,
            "GroupType": "business"
        }
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        resp = client.DescribeBillSummary(req)
        
        # 生成输出文件
        output_file = os.path.join(output_dir, get_output_filename(month, 'business'))
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入表头
            f.write("分组 key,分组名称,原价,实际费用,现金费用\n")
            
            # 写入数据行
            for item in resp.SummaryDetail:
                f.write(f"{item.GroupKey},{item.GroupValue},{item.TotalCost},{item.RealTotalCost},{item.CashPayAmount}\n")
            
            # 添加月度计费精度差异行 (从 resp 中获取或计算)
            if hasattr(resp, 'BillSum') and resp.BillSum:
                # 如果有账单总额，计算差异
                pass
        
        print(f"✓ 已生成账单汇总文件：{output_file}")
        return output_file
        
    except TencentCloudSDKException as err:
        print(f"✗ API 调用失败：{err}")
        raise


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='腾讯云账单汇总数据导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成上个月的账单汇总
    python tencent_billing_business_summary.py last
    
    # 生成指定月份的账单汇总
    python tencent_billing_business_summary.py 2026-02
    
    # 生成到指定目录
    python tencent_billing_business_summary.py 2026-02 -o /path/to/output
        """
    )
    
    parser.add_argument(
        'month',
        nargs='?',
        default='last',
        help='月份 (YYYY-MM 格式，或 "last" 表示上个月，"current" 表示当前月，默认：last)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='.',
        help='输出目录 (默认：当前目录)'
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    if not os.getenv("TENCENTCLOUD_SECRET_ID") or not os.getenv("TENCENTCLOUD_SECRET_KEY"):
        print("✗ 缺少环境变量：TENCENTCLOUD_SECRET_ID 或 TENCENTCLOUD_SECRET_KEY")
        print("\n请设置环境变量:")
        print("  export TENCENTCLOUD_SECRET_ID=your_secret_id")
        print("  export TENCENTCLOUD_SECRET_KEY=your_secret_key")
        sys.exit(1)
    
    try:
        # 解析月份
        month = get_month_str(args.month)
        print(f"正在获取 {month} 的账单汇总数据...")
        
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 获取并保存数据
        output_file = fetch_business_summary(month, args.output_dir)
        
        print(f"\n完成！文件已保存到：{output_file}")
        
    except ValueError as e:
        print(f"✗ 参数错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 执行失败：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
