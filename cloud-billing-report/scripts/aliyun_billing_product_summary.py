#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云账单明细数据导出工具

从阿里云 API 获取账单明细数据并保存为 CSV 文件
支持分页获取全部数据

环境变量:
    ALIBABA_CLOUD_ACCESS_KEY_ID: 阿里云 Access Key ID
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: 阿里云 Access Key Secret

Usage:
    # 生成指定月份的账单明细 (月份格式：YYYY-MM)
    python aliyun_billing_product_summary.py 2026-02
    
    # 生成上个月的账单明细
    python aliyun_billing_product_summary.py last
    
    # 指定每页数量
    python aliyun_billing_product_summary.py 2026-02 --limit 500
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
    # from aliyunsdkbssopenapi.request.v20171214 import QueryBillRequest
    from aliyunsdkbssopenapi.request.v20171214.DescribeInstanceBillRequest import DescribeInstanceBillRequest
except ImportError:
    print("✗ 缺少阿里云 SDK，请安装：pip install aliyun-python-sdk-bssopenapi")
    sys.exit(1)


def get_month_str(month_arg: str) -> str:
    """解析月份参数，返回 YYYY-MM 格式"""
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


def get_output_filename(month: str, summary_type: str = 'product') -> str:
    """生成输出文件名"""
    month_short = month.replace('-', '')
    return f"aliyun_billing_{month_short}_{summary_type}_summary.csv"


def fetch_product_summary(month: str, output_dir: str = '.', limit: int = 1000) -> str:
    """
    获取账单明细数据并保存为 CSV (支持分页)
    """
    try:
        # 从环境变量读取密钥
        access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        
        if not access_key_id or not access_key_secret:
            raise Exception("缺少环境变量：ALIBABA_CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        
        # 创建客户端
        client = AcsClient(access_key_id, access_key_secret, "cn-hangzhou")
        
        # 生成输出文件
        output_file = os.path.join(output_dir, get_output_filename(month, 'product'))
        
        page_num = 1
        total_count = 0
        first_page = True
        
        print(f"正在获取明细数据...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入表头
            f.write("产品名称,产品编码,子产品名称,子产品编码,资源别名,资源 ID,付费模式,原价,实际费用,现金支付,折扣,账单类型\n")
            
            while True:
                # 构建请求
                request = DescribeInstanceBillRequest()
                request.set_accept_format('json')
                request.set_BillingCycle(month)
                request.set_IsBillingItem(False)
                request.set_MaxResults(300)

                # request = QueryBillRequest.QueryBillRequest()
                # request.set_BillMonth(month)
                # request.set_PageNum(page_num)
                # request.set_PageSize(limit)
                
                # 发送请求
                response = client.do_action_with_exception(request)
                resp_json = json.loads(response)
                
                # print(resp_json)
                if not resp_json.get('Success'):
                    raise Exception(f"API 调用失败：{resp_json.get('Message', 'Unknown error')}")
                
                # 获取总记录数 (仅第一页)
                if first_page:
                    total_count = resp_json.get('Data', {}).get('TotalCount', 0)
                    print(f"总记录数：{total_count}")
                    first_page = False
                
                # 写入数据行
                # data_list = resp_json.get('Data', {}).get('Items', {}).get('BillingItem', [])
                data_list = resp_json.get('Data', {}).get('Items', [])
                count = 0
                for item in data_list:
                    # 处理字段中的逗号，用引号包裹
                    fields = [
                        str(item.get('ProductName', '') or '').replace('"', '""'),
                        str(item.get('ProductCode', '') or '').replace('"', '""'),
                        str(item.get('ProductDetail', '') or '').replace('"', '""'),
                        str(item.get('ProductType', '') or '').replace('"', '""'),
                        str(item.get('InstanceID', '') or '').replace('"', '""'),
                        str(item.get('NickName', '') or '').replace('"', '""'),
                        # Subscription：预付费。PayAsYouGo：后付费。
                        str(item.get('SubscriptionType', '') or '').replace('"', '""'),
                        str(item.get('PretaxGrossAmount', 0) or ''),
                        str(item.get('PretaxAmount', 0) or ''),
                        str(item.get('AfterDiscountAmount', 0) or ''),
                        str(item.get('DiscountRate', '') or ''),
                        str(item.get('ItemName', '') or '').replace('"', '""')
                    ]
                    f.write(','.join(f'"{field}"' if ',' in field or '"' in field else field for field in fields) + '\n')
                    count += 1
                
                processed = page_num * limit if page_num * limit < total_count else total_count
                print(f"已获取 {processed}/{total_count} 条记录...")
                
                # 判断是否还有更多数据
                if len(data_list) < limit or page_num * limit >= total_count:
                    break
                
                page_num += 1
        
        print(f"✓ 已生成账单明细文件：{output_file}")
        return output_file
        
    except (ClientException, ServerException) as err:
        print(f"✗ API 调用失败：{err}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='阿里云账单明细数据导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成上个月的账单明细
    python aliyun_billing_product_summary.py last
    
    # 生成指定月份的账单明细
    python aliyun_billing_product_summary.py 2026-02
    
    # 指定每页数量
    python aliyun_billing_product_summary.py 2026-02 --limit 500
    
    # 生成到指定目录
    python aliyun_billing_product_summary.py 2026-02 -o /path/to/output
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
    
    try:
        month = get_month_str(args.month)
        print(f"正在获取 {month} 的账单明细数据...")
        
        os.makedirs(args.output_dir, exist_ok=True)
        
        limit = min(args.limit, 1000)
        
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
