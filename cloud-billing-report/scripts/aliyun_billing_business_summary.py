#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云账单汇总数据导出工具

从阿里云 API 获取账单汇总数据并保存为 CSV 文件

环境变量:
    ALIBABA_CLOUD_ACCESS_KEY_ID: 阿里云 Access Key ID
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: 阿里云 Access Key Secret

Usage:
    # 生成指定月份的账单汇总 (月份格式：YYYY-MM)
    python aliyun_billing_business_summary.py 2026-02
    
    # 生成上个月的账单汇总
    python aliyun_billing_business_summary.py last
    
    # 生成当前月份的账单汇总
    python aliyun_billing_business_summary.py current
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
    from aliyunsdkbssopenapi.request.v20171214 import QueryAccountBillRequest
    from aliyunsdkbssopenapi.request.v20171214.QueryBillOverviewRequest import QueryBillOverviewRequest
except ImportError:
    print("✗ 缺少阿里云 SDK，请安装：pip install aliyun-python-sdk-bssopenapi")
    sys.exit(1)


def get_month_str(month_arg: str) -> str:
    """
    解析月份参数，返回 YYYY-MM 格式
    """
    today = datetime.now()
    
    if month_arg.lower() == 'last':
        last_month = today - timedelta(days=today.day)
        return last_month.strftime('%Y-%m')
    elif month_arg.lower() == 'current':
        return today.strftime('%Y-%m')
    else:
        try:
            datetime.strptime(month_arg, '%Y-%m')
            return month_arg
        except ValueError:
            raise ValueError(f"无效的月份格式：{month_arg}，请使用 YYYY-MM 格式")


def get_output_filename(month: str, summary_type: str = 'business') -> str:
    """生成输出文件名"""
    month_short = month.replace('-', '')
    return f"aliyun_billing_{month_short}_{summary_type}_summary.csv"


def fetch_business_summary(month: str, output_dir: str = '.') -> str:
    """
    获取账单汇总数据并保存为 CSV
    """
    try:
        # 从环境变量读取密钥
        access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        
        if not access_key_id or not access_key_secret:
            raise Exception("缺少环境变量：ALIBABA_CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        
        # 创建客户端
        client = AcsClient(access_key_id, access_key_secret, "cn-beijing")
        
        # 构建请求
        request = QueryBillOverviewRequest()
        request.set_accept_format('json')
        request.set_BillingCycle(month)

        # request = QueryAccountBillRequest.QueryAccountBillRequest()
        # request.set_BillingCycle(month)
        
        # 发送请求
        response = client.do_action_with_exception(request)
        resp_json = json.loads(response)
        # print(respll_json)
        if resp_json.get('Success'):
            # 生成输出文件
            output_file = os.path.join(output_dir, get_output_filename(month, 'business'))
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # 写入表头
                f.write("分组 key,分组名称,原价,实际费用,现金费用\n")
                
                # 写入数据行
                data_list = resp_json.get('Data', {}).get('Items', {}).get('Item', [])
                for item in data_list:
                    group_key = item.get('ProductCode', '')
                    group_name = item.get('ProductName', '')
                    total_cost = float(item.get('PretaxGrossAmount', 0) or 0)
                    real_cost = float(item.get('PretaxAmount', 0) or 0)
                    cash_cost = float(item.get('CashAmount', 0) or 0)
                    
                    f.write(f"{group_key},{group_name},{total_cost},{real_cost},{cash_cost}\n")
            
            print(f"✓ 已生成账单汇总文件：{output_file}")
            return output_file
        else:
            raise Exception(f"API 调用失败：{resp_json.get('Message', 'Unknown error')}")
        
    except (ClientException, ServerException) as err:
        print(f"✗ API 调用失败：{err}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='阿里云账单汇总数据导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成上个月的账单汇总
    python aliyun_billing_business_summary.py last
    
    # 生成指定月份的账单汇总
    python aliyun_billing_business_summary.py 2026-02
    
    # 生成到指定目录
    python aliyun_billing_business_summary.py 2026-02 -o /path/to/output
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
    
    try:
        month = get_month_str(args.month)
        print(f"正在获取 {month} 的账单汇总数据...")
        
        os.makedirs(args.output_dir, exist_ok=True)
        
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
