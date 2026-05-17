#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云/腾讯云账单对比分析报告生成器

自动生成指定月份的账单对比分析报告

环境变量:
    腾讯云：TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY
    阿里云：ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET

Usage:
    # 生成上个月的对比报告 (对比上个月和上上个月)
    python generate_billing_report.py
    
    # 生成指定月份的对比报告
    python generate_billing_report.py 2026-02
    
    # 指定云厂商 (aliyun 或 tencent)
    python generate_billing_report.py 2026-02 --cloud aliyun
    
    # 生成报告并发送邮件
    python generate_billing_report.py 2026-02 --send-email
"""

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


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


def get_previous_month(month: str) -> str:
    """
    获取上一个月
    
    Args:
        month: YYYY-MM 格式的月份
    
    Returns:
        上一个月的 YYYY-MM 格式
    """
    dt = datetime.strptime(month, '%Y-%m')
    if dt.month == 1:
        prev_dt = dt.replace(year=dt.year - 1, month=12)
    else:
        prev_dt = dt.replace(month=dt.month - 1)
    return prev_dt.strftime('%Y-%m')


def month_to_short(month: str) -> str:
    """
    转换 YYYY-MM 为 YYYYMM
    
    Args:
        month: YYYY-MM 格式的月份
    
    Returns:
        YYYYMM 格式的月份
    """
    return month.replace('-', '')


def get_file_prefix(cloud_vendor: str) -> str:
    """
    获取文件前缀
    
    Args:
        cloud_vendor: 云厂商 (aliyun 或 tencent)
    
    Returns:
        文件前缀
    """
    return 'aliyun' if cloud_vendor == 'aliyun' else 'tencent'


def check_or_generate_summary(month: str, output_dir: str = '.', cloud_vendor: str = 'tencent') -> tuple:
    """
    检查是否存在账单汇总文件，不存在则生成
    
    Args:
        month: YYYY-MM 格式的月份
        output_dir: 输出目录
        cloud_vendor: 云厂商 (aliyun 或 tencent)
    
    Returns:
        (business_file, product_file) 路径元组
    """
    month_short = month_to_short(month)
    file_prefix = get_file_prefix(cloud_vendor)
    
    business_file = os.path.join(output_dir, f"{file_prefix}_billing_{month_short}_business_summary.csv")
    product_file = os.path.join(output_dir, f"{file_prefix}_billing_{month_short}_product_summary.csv")

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查并生成 business_summary
    if not os.path.exists(business_file):
        print(f"文件不存在，正在生成 {month} 的账单汇总...")
        summary_script = f"{file_prefix}_billing_business_summary.py"
        subprocess.run(
            [sys.executable, os.path.join(script_dir, summary_script), month, '-o', output_dir],
            check=True,
            cwd=output_dir if output_dir != '.' else None
        )
    else:
        print(f"✓ 账单汇总文件已存在：{business_file}")

    # 检查并生成 product_summary
    if not os.path.exists(product_file):
        print(f"文件不存在，正在生成 {month} 的账单明细...")
        summary_script = f"{file_prefix}_billing_product_summary.py"
        subprocess.run(
            [sys.executable, os.path.join(script_dir, summary_script), month, '-o', output_dir],
            check=True,
            cwd=output_dir if output_dir != '.' else None
        )
    else:
        print(f"✓ 账单明细文件已存在：{product_file}")
    
    return business_file, product_file


def generate_report(current_month: str, output_dir: str = '.', cloud_vendor: str = 'tencent') -> str:
    """
    生成账单对比分析报告
    
    Args:
        current_month: YYYY-MM 格式的目标月份
        output_dir: 输出目录
        cloud_vendor: 云厂商 (aliyun 或 tencent)
    
    Returns:
        生成的报告文件路径
    """
    previous_month = get_previous_month(current_month)
    file_prefix = get_file_prefix(cloud_vendor)
    
    print("=" * 70)
    print(f"{cloud_vendor.upper()} 账单对比分析报告生成器")
    print("=" * 70)
    print(f"云厂商：{cloud_vendor}")
    print(f"目标月份：{current_month}")
    print(f"对比月份：{previous_month}")
    print("=" * 70)
    
    # 1. 确保两个月份的数据文件都存在
    print("\n[步骤 1/4] 检查并生成账单数据文件...")
    check_or_generate_summary(previous_month, output_dir, cloud_vendor)
    check_or_generate_summary(current_month, output_dir, cloud_vendor)
    
    # 2. 使用 AI 生成报告 (读取 prompt 并调用 AI)
    print("\n[步骤 2/4] 分析数据并生成报告...")

    # 读取 prompt 文件 (从脚本所在目录的 references 子目录读取)
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # prompt_file = os.path.join(script_dir, 'references', 'report_template.md')

    skill_path = Path(__file__).resolve().parent.parent
    prompt_file = os.path.join(skill_path, 'references', 'report_template.md')

    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # 调用 AI 生成报告
    report_content = analyze_and_generate_report(
        previous_month,
        current_month,
        output_dir, cloud_vendor
    )

    # 保存报告
    report_filename = f"{file_prefix}_billing_report_{month_to_short(current_month)}.md"
    report_path = os.path.join(output_dir, report_filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"✓ 报告已生成：{report_path}")

    return report_path


def analyze_and_generate_report(previous_month: str, current_month: str, output_dir: str, cloud_vendor: str = "aliyun") -> str:
    """
    分析账单数据并生成报告内容

    Args:
        previous_month: YYYY-MM 格式的上个月
        current_month: YYYY-MM 格式的目标月
        output_dir: 数据文件目录

    Returns:
        Markdown 格式的报告内容
    """
    import csv

    prev_short = month_to_short(previous_month)
    curr_short = month_to_short(current_month)
    file_prefix = get_file_prefix(cloud_vendor)
    # 读取 business_summary 数据
    def read_business_summary(month_short):
        data = {}
        file_path = os.path.join(output_dir, f"{file_prefix}_billing_{month_short}_business_summary.csv")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row['分组 key']
                real_cost = float(row['实际费用']) if row['实际费用'] else 0
                original_cost = float(row['原价']) if row['原价'] else 0
                cash_cost = float(row['现金费用']) if row['现金费用'] else 0
                
                if key in data:
                    # 如果 key 已存在，累加费用（处理同一产品有多个计费项的情况）
                    data[key]['original_cost'] += original_cost
                    data[key]['real_cost'] += real_cost
                    data[key]['cash_cost'] += cash_cost
                else:
                    data[key] = {
                        'name': row['分组名称'],
                        'original_cost': original_cost,
                        'real_cost': real_cost,
                        'cash_cost': cash_cost
                    }
        return data

    # 读取 product_summary 数据
    def read_product_summary(month_short):
        data = []
        file_path = os.path.join(output_dir, f"{file_prefix}_billing_{month_short}_product_summary.csv")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'product_name': row.get('产品名称', ''),
                    'product_code': row.get('产品编码', ''),
                    'sub_product_name': row.get('子产品名称', ''),
                    'sub_product_code': row.get('子产品编码', ''),
                    'resource_name': row.get('资源别名', ''),
                    'resource_id': row.get('资源 ID', ''),
                    'pay_mode': row.get('付费模式', ''),
                    'original_cost': float(row.get('原价', 0) or 0),
                    'real_cost': float(row.get('实际费用', 0) or 0),
                    'cash_cost': float(row.get('现金支付', 0) or 0),
                    'discount': row.get('折扣', ''),
                    'action_type': row.get('账单类型', '')
                })
        return data

    # 读取数据
    prev_business = read_business_summary(prev_short)
    curr_business = read_business_summary(curr_short)
    prev_product = read_product_summary(prev_short)
    curr_product = read_product_summary(curr_short)

    # 计算总费用
    def calc_total(data):
        total = sum(item['real_cost'] for item in data.values())
        return total

    prev_total = calc_total(prev_business)
    curr_total = calc_total(curr_business)
    total_change = curr_total - prev_total
    total_change_pct = (total_change / prev_total * 100) if prev_total > 0 else 0

    # 计算每个产品的变化
    all_products = set(prev_business.keys()) | set(curr_business.keys())
    product_changes = []
    for key in all_products:
        prev_data = prev_business.get(key, {'real_cost': 0})
        curr_data = curr_business.get(key, {'real_cost': 0})
        change = curr_data['real_cost'] - prev_data['real_cost']
        change_pct = (change / prev_data['real_cost'] * 100) if prev_data['real_cost'] > 0 else (100 if curr_data['real_cost'] > 0 else 0)
        product_changes.append({
            'key': key,
            'name': curr_data.get('name', prev_data.get('name', key)),
            'prev_cost': prev_data['real_cost'],
            'curr_cost': curr_data['real_cost'],
            'change': change,
            'change_pct': change_pct
        })

    # 排序
    product_changes.sort(key=lambda x: abs(x['change']), reverse=True)
    top_decreases = [p for p in product_changes if p['change'] < 0][:5]
    increases = [p for p in product_changes if p['change'] > 0]
    stable = [p for p in product_changes if abs(p['change_pct']) < 0.01]

    # 生成报告
    report = []
    report.append(f"# 腾讯云账单分析报告 - {previous_month} vs {current_month}\n")
    
    # 一、整体费用概览
    report.append("## 一、整体费用概览\n")
    report.append("| 月份 | 总实际费用 (RealTotalCost) |")
    report.append("|------|--------------------------|")
    report.append(f"| {previous_month} | ¥{prev_total:,.2f} |")
    report.append(f"| {current_month} | ¥{curr_total:,.2f} |")
    change_sign = "+" if total_change >= 0 else ""
    report.append(f"| **变化** | **¥{change_sign}{total_change:,.2f} ({change_sign}{total_change_pct:.2f}%)** |\n")

    # 二、产品费用变化分析
    report.append("---\n")
    report.append("## 二、产品费用变化分析 (Business Summary)\n")
    
    # 2.1 费用变化汇总表
    report.append("### 2.1 费用变化汇总表\n")
    report.append("| 产品名称 | 上月费用 | 本月费用 | 变化金额 | 变化比例 |")
    report.append("|----------|---------|---------|----------|----------|")
    for p in product_changes:
        change_sign = "+" if p['change'] >= 0 else ""
        pct_sign = "+" if p['change_pct'] >= 0 else ""
        report.append(f"| {p['name']} | ¥{p['prev_cost']:,.2f} | ¥{p['curr_cost']:,.2f} | {change_sign}¥{p['change']:,.2f} | {pct_sign}{p['change_pct']:.2f}% |")

    # 2.2 费用降低 TOP 5
    report.append("\n### 2.2 费用降低 TOP 5 (按变化金额)\n")
    report.append("| 排名 | 产品名称 | 上月费用 | 本月费用 | 变化金额 | 变化比例 |")
    report.append("|------|----------|---------|---------|----------|----------|")
    for i, p in enumerate(top_decreases, 1):
        report.append(f"| {i} | {p['name']} | ¥{p['prev_cost']:,.2f} | ¥{p['curr_cost']:,.2f} | **¥{p['change']:,.2f}** | {p['change_pct']:.2f}% |")

    # 2.3 费用增长产品
    report.append("\n### 2.3 费用增长产品\n")
    if increases:
        report.append("| 产品名称 | 上月费用 | 本月费用 | 变化金额 | 变化比例 |")
        report.append("|----------|---------|---------|----------|----------|")
        for p in increases:
            report.append(f"| {p['name']} | ¥{p['prev_cost']:,.2f} | ¥{p['curr_cost']:,.2f} | +¥{p['change']:,.2f} | +{p['change_pct']:.2f}% |")
    else:
        report.append("无增长产品\n")

    # 2.4 费用持平产品
    report.append("\n### 2.4 费用持平产品\n")
    if stable:
        report.append("| 产品名称 | 上月费用 | 本月费用 | 变化比例 |")
        report.append("|----------|---------|---------|----------|")
        for p in stable[:10]:
            report.append(f"| {p['name']} | ¥{p['prev_cost']:,.2f} | ¥{p['curr_cost']:,.2f} | {p['change_pct']:.2f}% |")
    else:
        report.append("无明显持平产品\n")

    # 三、费用变化原因分析
    report.append("---\n")
    report.append("## 三、费用变化原因分析 (Product Summary)\n")

    # 分析重点产品 (变化金额>1000 或 变化比例>20%)
    key_products = [p for p in product_changes if abs(p['change']) > 1000 or abs(p['change_pct']) > 20]
    key_products = key_products[:10]

    for p in key_products:
        report.append(f"### {p['name']} ({p['change_pct']:+.2f}%, {p['change']:+,.2f})\n")

        # 从 product_summary 中查找明细
        prev_items = [item for item in prev_product if item['product_code'] == p['key']]
        curr_items = [item for item in curr_product if item['product_code'] == p['key']]

        if prev_items or curr_items:
            # 按子产品/资源分组汇总
            def group_by_resource(items):
                groups = {}
                for item in items:
                    # 优先使用资源别名，其次使用子产品名称
                    key = item['resource_name'] or item['sub_product_name'] or item['product_name']
                    if key not in groups:
                        groups[key] = {
                            'prev': 0,
                            'curr': 0,
                            'pay_mode': item['pay_mode'],
                            'discount': item['discount']
                        }
                    # 根据月份累加
                    if item in prev_items:
                        groups[key]['prev'] += item['real_cost']
                    else:
                        groups[key]['curr'] += item['real_cost']
                return groups

            # 重新按月份分组
            prev_groups = {}
            curr_groups = {}
            
            for item in prev_items:
                key = item['resource_name'] or item['sub_product_name'] or item['product_name']
                if key not in prev_groups:
                    prev_groups[key] = 0
                prev_groups[key] += item['real_cost']
            
            for item in curr_items:
                key = item['resource_name'] or item['sub_product_name'] or item['product_name']
                if key not in curr_groups:
                    curr_groups[key] = 0
                curr_groups[key] += item['real_cost']

            all_sub_keys = set(prev_groups.keys()) | set(curr_groups.keys())
            sub_changes = []
            for key in all_sub_keys:
                prev_val = prev_groups.get(key, 0)
                curr_val = curr_groups.get(key, 0)
                change_val = curr_val - prev_val
                sub_changes.append({
                    'name': key,
                    'prev': prev_val,
                    'curr': curr_val,
                    'change': change_val
                })
            sub_changes.sort(key=lambda x: abs(x['change']), reverse=True)

            if sub_changes:
                report.append("**明细变化**:\n")
                report.append("| 计费项 | 上月费用 | 本月费用 | 变化 |")
                report.append("|--------|---------|---------|------|")
                for s in sub_changes[:10]:
                    change_sign = "+" if s['change'] > 0 else ""
                    report.append(f"| {s['name']} | ¥{s['prev']:,.2f} | ¥{s['curr']:,.2f} | {change_sign}¥{s['change']:,.2f} |")

        # 生成原因分析
        report.append(f"\n**原因分析**:\n")
        
        # 获取付费模式信息
        pay_modes = set()
        for item in prev_items + curr_items:
            if item['pay_mode']:
                pay_modes.add(item['pay_mode'])
        
        # 根据数据生成原因
        if p['change'] < 0:
            if '包年包月' in str(pay_modes):
                report.append(f"- 包年包月费用稳定，按量计费资源使用量下降\n")
            else:
                report.append(f"- 按量计费资源使用量下降\n")
            
            # 查找下降最多的子项
            if sub_changes and sub_changes[0]['change'] < 0:
                report.append(f"- 主要下降来源：{sub_changes[0]['name']} (下降 ¥{abs(sub_changes[0]['change']):,.2f})\n")
        elif p['change'] > 0:
            if '包年包月' in str(pay_modes):
                report.append(f"- 包年包月费用稳定，按量计费资源使用量增长\n")
            else:
                report.append(f"- 按量计费资源使用量增长\n")
            
            if sub_changes and sub_changes[0]['change'] > 0:
                report.append(f"- 主要增长来源：{sub_changes[0]['name']} (增长 ¥{sub_changes[0]['change']:,.2f})\n")
        else:
            report.append(f"- 费用基本持平\n")

    # 四、总结
    report.append("---\n")
    report.append("## 四、总结\n")
    
    # 4.1 费用下降主要驱动因素
    report.append("### 4.1 费用下降主要驱动因素\n")
    report.append("| 排名 | 产品 | 影响金额 | 占比 | 说明 |")
    report.append("|------|------|----------|------|------|")
    total_decrease = sum(abs(p['change']) for p in product_changes if p['change'] < 0)
    for i, p in enumerate(top_decreases[:5], 1):
        ratio = (abs(p['change']) / total_decrease * 100) if total_decrease > 0 else 0
        report.append(f"| {i} | {p['name']} | ¥{p['change']:,.2f} | {ratio:.1f}% | 费用下降 |")

    # 4.2 费用稳定/增长项
    report.append("\n### 4.2 费用稳定/增长项\n")
    report.append("| 产品 | 状态 | 说明 |")
    report.append("|------|------|------|")
    
    # 找出费用持平的包年包月产品
    for p in product_changes:
        if abs(p['change_pct']) < 1 and p['curr_cost'] > 1000:
            items = [item for item in curr_business.get(p['key'], [])]
            report.append(f"| {p['name']} | 稳定 | 费用波动小于 1% |")
    
    for p in increases[:3]:
        report.append(f"| {p['name']} | 增长 | 费用增长 {p['change_pct']:.1f}% |")

    # 4.3 建议
    report.append("\n### 4.3 建议\n")
    report.append("1. **带宽成本优化**: 共享带宽包费用下降明显，建议继续监控带宽使用效率\n")
    report.append("2. **CDN 费用关注**: CDN 费用变化与业务流量相关，需确认是否为正常业务波动\n")
    report.append("3. **存储优化**: COS 存储费用变化，建议评估数据生命周期管理策略\n")
    report.append("4. **异常费用核查**: 对费用增长超过 20% 的产品进行业务核查\n")

    report.append("\n---\n")
    report.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  \n")
    report.append(f"*数据来源：腾讯云账单 API*  \n")
    report.append(f"*对比周期：{previous_month} vs {current_month}*\n")

    return '\n'.join(report)


def send_report(report_path: str, to_addr: str = None, cc_addrs: str = None):
    """
    发送报告邮件
    
    Args:
        report_path: 报告文件路径
        to_addr: 收件人地址
        cc_addrs: 抄送人地址 (逗号分隔)
    """
    cmd = [sys.executable, 'send_billing_report.py', report_path]
    
    if to_addr:
        cmd.extend(['-t', to_addr])
    if cc_addrs:
        cmd.extend(['-c', cc_addrs])
    
    subprocess.run(cmd, check=True, cwd=os.path.dirname(os.path.abspath(__file__)) or '.')


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='腾讯云账单对比分析报告生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 生成上个月的对比报告
    python generate_billing_report.py
    
    # 生成指定月份的对比报告
    python generate_billing_report.py 2026-02
    
    # 生成报告并发送邮件
    python generate_billing_report.py 2026-02 --send-email
    
    # 指定收件人和抄送人
    python generate_billing_report.py 2026-02 --send-email -t liuchao@kongfz.com -c kfzops@kongcz.com
        """
    )
    
    parser.add_argument(
        'month',
        nargs='?',
        default='last',
        help='目标月份 (YYYY-MM 格式，或 "last" 表示上个月，默认：last)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='.',
        help='输出目录 (默认：当前目录)'
    )
    
    parser.add_argument(
        '--send-email',
        action='store_true',
        help='生成报告后发送邮件'
    )
    
    parser.add_argument(
        '-t', '--to',
        dest='to_addr',
        help='收件人邮箱地址'
    )
    
    parser.add_argument(
        '-c', '--cc',
        dest='cc_addrs',
        help='抄送人邮箱地址，多个用逗号分隔'
    )

    parser.add_argument(
        '--cloud',
        choices=['tencent', 'aliyun'],
        default='tencent',
        help='云厂商 (tencent 或 aliyun，默认：tencent)'
    )

    args = parser.parse_args()

    # 检查环境变量
    cloud_vendor = args.cloud
    if cloud_vendor == 'tencent':
        if not os.getenv("TENCENTCLOUD_SECRET_ID") or not os.getenv("TENCENTCLOUD_SECRET_KEY"):
            print("✗ 缺少环境变量：TENCENTCLOUD_SECRET_ID 或 TENCENTCLOUD_SECRET_KEY")
            print("\n请设置环境变量:")
            print("  export TENCENTCLOUD_SECRET_ID=your_secret_id")
            print("  export TENCENTCLOUD_SECRET_KEY=your_secret_key")
            sys.exit(1)
    else:  # aliyun
        if not os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID") or not os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
            print("✗ 缺少环境变量：ALIBABA_CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET")
            print("\n请设置环境变量:")
            print("  export ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id")
            print("  export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret")
            sys.exit(1)

    try:
        # 解析月份
        current_month = get_month_str(args.month)

        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)

        # 生成报告
        report_path = generate_report(current_month, args.output_dir, cloud_vendor)

        # 发送邮件
        if args.send_email:
            print("\n[步骤 3/4] 发送邮件...")
            send_report(report_path, args.to_addr, args.cc_addrs)

        print("\n" + "=" * 70)
        print("✓ 完成！")
        print("=" * 70)
        print(f"报告文件：{report_path}")

    except ValueError as e:
        print(f"✗ 参数错误：{e}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"✗ 执行失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 未知错误：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
