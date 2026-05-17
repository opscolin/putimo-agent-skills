#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云账单明细数据导出工具

从腾讯云 API 获取账单明细数据并保存为 CSV 文件
支持分页获取全部数据

环境变量:
    TENCENTCLOUD_SECRET_ID: 腾讯云 Secret ID
    TENCENTCLOUD_SECRET_KEY: 腾讯云 Secret Key

Usage:
    # 生成指定月份的账单明细 (月份格式：YYYY-MM)
    python tencent_billing_product_summary.py 2026-02
    
    # 生成上个月的账单明细
    python tencent_billing_product_summary.py last
    
    # 生成当前月份的账单明细
    python tencent_billing_product_summary.py current
    
    # 指定每页数量
    python tencent_billing_product_summary.py 2026-02 --limit 500
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


def get_output_filename(month: str, summary_type: str = 'product') -> str:
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


def fetch_product_summary(month: str, output_dir: str = '.', limit: int = 1000) -> str:
    """
    获取账单明细数据并保存为 CSV (支持分页)
    
    Args:
        month: YYYY-MM 格式的月份
        output_dir: 输出目录
        limit: 每页数量
    
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
        
        # 生成输出文件
        output_file = os.path.join(output_dir, get_output_filename(month, 'product'))
        
        total_count = 0
        offset = 0
        first_page = True
        
        print(f"正在获取明细数据...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入表头
            f.write("产品名称,产品编码,子产品名称,子产品编码,资源别名,资源 ID,付费模式,原价,实际费用,现金支付,折扣,账单类型\n")
            
            while True:
                # 构建请求
                req = models.DescribeBillResourceSummaryRequest()
                params = {
                    "Offset": offset,
                    "Limit": limit,
                    "Month": month,
                    "NeedRecordNum": 1 if first_page else 0
                }
                req.from_json_string(json.dumps(params))
                
                # 发送请求
                resp = client.DescribeBillResourceSummary(req)

                # 获取总记录数 (仅第一页)
                # 尝试不同的属性名来获取总记录数
                if first_page:
                    # 尝试多种方式获取 Total (腾讯云 API 返回的是 Total 不是 TotalCount)
                    if hasattr(resp, 'Total'):
                        total_count = resp.Total
                    elif hasattr(resp, 'TotalCount'):
                        total_count = resp.TotalCount
                    elif hasattr(resp, '_total'):
                        total_count = resp._total
                    else:
                        # 从响应 JSON 中获取
                        resp_json = json.loads(resp.to_json_string())
                        total_count = resp_json.get('Total', resp_json.get('TotalCount', 0))
                    print(f"总记录数：{total_count}")
                    first_page = False

                # 获取当前页记录
                resource_summary_set = resp.ResourceSummarySet if hasattr(resp, 'ResourceSummarySet') else []

                # 写入数据行
                count = 0
                for item in resource_summary_set:
                    # 处理字段中的逗号，用引号包裹
                    fields = [
                        str(getattr(item, 'BusinessCodeName', '') or '').replace('"', '""'),
                        str(getattr(item, 'BusinessCode', '') or '').replace('"', '""'),
                        str(getattr(item, 'ProductCodeName', '') or '').replace('"', '""'),
                        str(getattr(item, 'ProductCode', '') or '').replace('"', '""'),
                        str(getattr(item, 'ResourceName', '') or '').replace('"', '""'),
                        str(getattr(item, 'ResourceId', '') or '').replace('"', '""'),
                        str(getattr(item, 'PayModeName', '') or '').replace('"', '""'),
                        str(getattr(item, 'TotalCost', '') or ''),
                        str(getattr(item, 'RealTotalCost', '') or ''),
                        str(getattr(item, 'CashPayAmount', '') or ''),
                        str(getattr(item, 'Discount', '') or ''),
                        str(getattr(item, 'ActionTypeName', '') or '').replace('"', '""')
                    ]
                    f.write(','.join(f'"{field}"' if ',' in field or '"' in field else field for field in fields) + '\n')
                    count += 1

                offset += limit
                processed = min(offset, total_count) if total_count > 0 else offset
                print(f"已获取 {processed}/{total_count if total_count > 0 else '?'} 条记录...")

                # 判断是否还有更多数据
                if count < limit or (total_count > 0 and offset >= total_count):
                    break
        
        print(f"✓ 已生成账单明细文件：{output_file}")
        return output_file
        
    except TencentCloudSDKException as err:
        print(f"✗ API 调用失败：{err}")
        raise


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='腾讯云账单明细数据导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成上个月的账单明细
    python tencent_billing_product_summary.py last
    
    # 生成指定月份的账单明细
    python tencent_billing_product_summary.py 2026-02
    
    # 指定每页数量
    python tencent_billing_product_summary.py 2026-02 --limit 500
    
    # 生成到指定目录
    python tencent_billing_product_summary.py 2026-02 -o /path/to/output
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
    
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='每页记录数 (默认：1000，最大：1000)'
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
        print(f"正在获取 {month} 的账单明细数据...")
        
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 限制 limit 最大值
        limit = min(args.limit, 1000)
        
        # 获取并保存数据
        output_file = fetch_product_summary(month, args.output_dir, limit)
        
        print(f"\n完成！文件已保存到：{output_file}")
        
    except ValueError as e:
        print(f"✗ 参数错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 执行失败：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
