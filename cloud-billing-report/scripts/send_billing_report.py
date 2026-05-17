#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云平台账单分析报告邮件发送工具

将 Markdown 格式的账单分析报告转换为 HTML 并发送邮件

环境变量:
    EMAIL_HOST: SMTP 服务器地址
    EMAIL_USER: 发件人邮箱地址
    EMAIL_PASSWORD: 发件人邮箱密码/授权码
    EMAIL_FROM_NAME: 发件人显示名称

Usage:
    # 使用默认收件人
    python send_billing_report.py aliyun_billing_report_202602_v3.md
    
    # 指定收件人和抄送人
    python send_billing_report.py report.md -t liuchao@kongfz.com -c kfzops@kongcz.com,finance@kongfz.com
    
    # 指定邮件主题
    python send_billing_report.py report.md -s "自定义主题"
    
    # 从环境变量读取收件人
    export EMAIL_TO=liuchao@kongfz.com
    export EMAIL_CC=kfzops@kongcz.com,finance@kongfz.com
    python send_billing_report.py report.md
"""

import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# 导入 Markdown 转换工具
from markdown_converter import create_email_html


def send_email(to_addr: str, cc_addrs: list, subject: str, html_content: str, 
               smtp_host: str, smtp_user: str, smtp_password: str, from_name: str,
               attachment_path: str = None) -> bool:
    """
    发送 HTML 邮件
    
    Args:
        to_addr: 收件人邮箱地址
        cc_addrs: 抄送人邮箱地址列表
        subject: 邮件主题
        html_content: HTML 邮件内容
        smtp_host: SMTP 服务器地址
        smtp_user: SMTP 用户名
        smtp_password: SMTP 密码
        from_name: 发件人显示名称
        attachment_path: 附件路径（可选）
    
    Returns:
        bool: 发送成功返回 True
    """
    try:
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{smtp_user}>"
        msg['To'] = to_addr
        if cc_addrs:
            msg['Cc'] = ', '.join(cc_addrs)
        
        # 添加 HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 添加附件（如果提供）
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                filename = os.path.basename(attachment_path)
                attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(attachment)
        
        # 获取所有收件人
        all_recipients = [to_addr] + cc_addrs
        
        # 连接 SMTP 服务器并发送邮件
        print(f"正在连接 SMTP 服务器：{smtp_host}")
        server = smtplib.SMTP_SSL(smtp_host, 465, timeout=30)
        server.set_debuglevel(0)
        
        print(f"正在登录：{smtp_user}")
        server.login(smtp_user, smtp_password)
        
        print(f"正在发送邮件给：{to_addr}")
        if cc_addrs:
            print(f"抄送给：{', '.join(cc_addrs)}")
        server.sendmail(smtp_user, all_recipients, msg.as_string())
        
        server.quit()
        
        print("✓ 邮件发送成功！")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("✗ SMTP 认证失败，请检查 EMAIL_USER 和 EMAIL_PASSWORD")
        return False
    except smtplib.SMTPConnectError:
        print(f"✗ 无法连接 SMTP 服务器 {smtp_host}")
        return False
    except Exception as e:
        print(f"✗ 发送失败：{str(e)}")
        return False


def parse_email_list(email_str: str) -> list:
    """
    解析邮箱地址列表，支持逗号或分号分隔
    
    Args:
        email_str: 邮箱地址字符串 (多个地址用逗号或分号分隔)
    
    Returns:
        邮箱地址列表
    """
    if not email_str:
        return []
    
    # 替换分号为逗号，然后分割
    emails = [e.strip() for e in email_str.replace(';', ',').split(',')]
    # 过滤空地址
    return [e for e in emails if e]


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='云平台账单分析报告邮件发送工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 使用默认收件人
    python send_billing_report.py aliyun_billing_report_202602_v3.md
    
    # 指定收件人
    python send_billing_report.py report.md -t liuchao@kongfz.com
    
    # 指定收件人和多个抄送人
    python send_billing_report.py report.md -t liuchao@kongfz.com -c kfzops@kongcz.com,finance@kongfz.com
    
    # 指定邮件主题
    python send_billing_report.py report.md -s "xx月份YY云平台账单分析报告"
    
    # 从环境变量读取收件人
    export EMAIL_TO=liuchao@kongfz.com
    export EMAIL_CC=kfzops@kongcz.com,finance@kongfz.com
    python send_billing_report.py report.md
        """
    )
    
    parser.add_argument(
        'report_path',
        help='Markdown 报告文件路径'
    )
    
    parser.add_argument(
        '-t', '--to',
        dest='to_addr',
        default=None,
        help='收件人邮箱地址 (默认：liuchao@kongfz.com，或从环境变量 EMAIL_TO 读取)'
    )
    
    parser.add_argument(
        '-c', '--cc',
        dest='cc_addrs',
        default=None,
        help='抄送人邮箱地址，多个用逗号或分号分隔 (默认：kfzops@kongcz.com，或从环境变量 EMAIL_CC 读取)'
    )
    
    parser.add_argument(
        '-s', '--subject',
        default=None,
        help='邮件主题 (默认：根据报告文件名自动生成)'
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    required_envs = ['EMAIL_HOST', 'EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_FROM_NAME']
    missing_envs = [env for env in required_envs if not os.environ.get(env)]
    
    if missing_envs:
        print(f"✗ 缺少必要的环境变量：{', '.join(missing_envs)}")
        print("\n请设置以下环境变量:")
        for env in missing_envs:
            print(f"  export {env}=your_value")
        sys.exit(1)
    
    # 获取配置
    smtp_host = os.environ['EMAIL_HOST']
    smtp_user = os.environ['EMAIL_USER']
    smtp_password = os.environ['EMAIL_PASSWORD']
    from_name = os.environ['EMAIL_FROM_NAME']
    
    # 收件人和抄送人 (命令行参数 > 环境变量 > 默认值)
    to_addr = args.to_addr or os.environ.get('EMAIL_TO') or 'liuchao@kongfz.com'
    cc_str = args.cc_addrs or os.environ.get('EMAIL_CC') or 'kfzops@kongcz.com'
    cc_addrs = parse_email_list(cc_str)
    
    # 报告文件路径
    report_path = args.report_path
    if not os.path.isabs(report_path):
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), report_path)
    
    if not os.path.exists(report_path):
        print(f"✗ 报告文件不存在：{report_path}")
        sys.exit(1)
    
    # 邮件主题 (命令行参数 > 自动生成)
    subject = args.subject
    if not subject:
        # 从文件名提取月份
        filename = os.path.basename(report_path)
        month = filename.replace('.md', '').replace('aliyun_billing_report_', '')
        cloud = filename.replace('.md', '').split('_')[0]
        subject = f"{cloud} 账单分析报告 - {month}"
    
    print("=" * 70)
    print("云平台账单分析报告邮件发送工具")
    print("=" * 70)
    print(f"报告文件：{report_path}")
    print(f"收件人：{to_addr}")
    print(f"抄送：{', '.join(cc_addrs) if cc_addrs else '无'}")
    print(f"SMTP 服务器：{smtp_host}")
    print(f"发件人：{from_name} <{smtp_user}>")
    print(f"邮件主题：{subject}")
    print("=" * 70)
    
    # 读取 Markdown 报告
    print("\n正在读取报告文件...")
    with open(report_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 创建 HTML 内容（使用 markdown_converter 工具）
    print("正在生成 HTML 邮件内容...")
    html_content = create_email_html(md_content, subject=subject)
    
    # 发送邮件
    print("\n正在发送邮件...")
    success = send_email(
        to_addr=to_addr,
        cc_addrs=cc_addrs,
        subject=subject,
        html_content=html_content,
        smtp_host=smtp_host,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_name=from_name,
        attachment_path=report_path  # 附加 Markdown 原文件作为附件
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
