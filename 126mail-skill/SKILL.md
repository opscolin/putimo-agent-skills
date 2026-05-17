---
name: 126mail-skill
description: Use when needing to read emails from 126 mail (NetEase mail), including fetching recent emails by days or reading specific email content with attachments information
---

# 126 Mail Skill

## Overview

读取网易126邮箱的邮件，支持两种模式：最近N天邮件列表查询和单封邮件内容读取。基于 IMAP 协议实现。

## When to Use

- 需要查看126邮箱的最近N天邮件
- 需要读取某封邮件的完整内容
- 需要了解邮件是否有附件

## Prerequisites

需要安装依赖:

```bash
pip install imapclient python-dotenv
```

需要在 `~/.claude/skills/126mail-skill/` 目录下创建 `.env` 文件配置邮箱账号：

```bash
cd ~/.claude/skills/126mail-skill/
touch .env
```

`.env` 文件内容：

```env
MAIL_126_ADDR=your_email@126.com
MAIL_126_PASSWORD=your_auth_code
```

**授权码获取：** 登录126邮箱 → 设置 → POP3/SMTP/IMAP → 开启IMAP服务 → 生成授权码

## Core Functions

### 1. 获取最近N天邮件列表

```python
from imapclient import IMAPClient
import email
from datetime import datetime, timedelta

def fetch_recent_emails_126(
    email_addr: str,
    password: str,
    days: int = 7,
    max_count: int = 50
) -> list[dict]:
    """
    获取最近N天的邮件列表

    Args:
        email_addr: 126邮箱地址
        password: 授权码（不是登录密码）
        days: 最近天数
        max_count: 最大返回数量

    Returns:
        邮件列表，每封邮件包含: subject, from, date, has_attachment, uid
    """
    server = IMAPClient('imap.126.com', ssl=True)
    server.login(email_addr, password)

    server.select_folder('INBOX')

    since_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
    messages = server.search(['SINCE', since_date])

    emails = []
    for uid in messages[-max_count:]:
        status, msg_data = server.fetch(uid, '(ENVELOPE RFC822.SIZE)')
        raw_email = msg_data[uid][b'RFC822']
        msg = email.message_from_bytes(raw_email)

        has_attachment = any(
            part.get_content_disposition() == 'ATTACHMENT'
            for part in msg.walk()
        )

        emails.append({
            'uid': uid,
            'subject': msg['Subject'] or '(无主题)',
            'from': msg['From'],
            'date': msg['Date'],
            'has_attachment': has_attachment
        })

    server.logout()
    return emails
```

### 2. 读取单封邮件内容

```python
def fetch_email_content_126(
    email_addr: str,
    password: str,
    uid: int
) -> dict:
    """
    读取指定邮件的完整内容

    Args:
        email_addr: 126邮箱地址
        password: 授权码
        uid: 邮件UID

    Returns:
        邮件内容包含: subject, from, date, body, html_body, attachments
    """
    server = IMAPClient('imap.126.com', ssl=True)
    server.login(email_addr, password)
    server.select_folder('INBOX')

    status, msg_data = server.fetch(uid, '(RFC822)')
    raw_email = msg_data[uid][b'RFC822']
    msg = email.message_from_bytes(raw_email)

    body = ''
    html_body = ''
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            if disposition == 'ATTACHMENT':
                attachments.append({
                    'filename': part.get_filename(),
                    'size': len(part.get_payload())
                })
            elif content_type == 'text/plain':
                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
            elif content_type == 'text/html':
                html_body = part.get_payload(decode=True).decode('utf-8', errors='replace')
    else:
        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

    server.logout()

    return {
        'subject': msg['Subject'],
        'from': msg['From'],
        'date': msg['Date'],
        'body': body,
        'html_body': html_body,
        'attachments': attachments
    }
```

## Quick Reference

| 功能 | 函数 | 必需参数 |
|------|------|----------|
| 最近N天邮件 | `fetch_recent_emails_126` | email_addr, password, days |
| 单封邮件内容 | `fetch_email_content_126` | email_addr, password, uid |

## Common Mistakes

### 1. 使用登录密码而非授权码

126邮箱必须使用授权码登录，授权码需要在邮箱设置中生成：
- 登录126邮箱 → 设置 → POP3/SMTP/IMAP → 开启服务 → 生成授权码

### 2. 未处理附件判断

使用 `get_content_disposition() == 'ATTACHMENT'` 判断，不要用 `get_filename()` 因为内联附件也会返回文件名。

### 3. 编码问题

使用 `decode=True` 并指定 `errors='replace'` 处理乱码。

### 4. 文件夹选择

只支持 INBOX，不支持其他文件夹如"草稿箱"、"已发送"等。

## Usage Example

```python
from dotenv import load_dotenv
import os

load_dotenv('/Users/colinspace/.claude/skills/126mail-skill/.env')

email_addr = os.getenv('MAIL_126_ADDR')
password = os.getenv('MAIL_126_PASSWORD')

# 获取最近7天的邮件
emails = fetch_recent_emails_126(
    email_addr=email_addr,
    password=password,
    days=7
)

for email in emails:
    print(f"主题: {email['subject']}")
    print(f"发件人: {email['from']}")
    print(f"时间: {email['date']}")
    print(f"有附件: {email['has_attachment']}")
    print('---')

# 读取特定邮件内容
content = fetch_email_content_126(
    email_addr=email_addr,
    password=password,
    uid=12345
)
print(content['body'])
```

## .env 配置文件

在 `~/.claude/skills/126mail-skill/` 目录下创建 `.env` 文件：

```bash
cd ~/.claude/skills/126mail-skill/
touch .env
```

编辑 `.env` 文件，添加以下配置：

```env
MAIL_126_ADDR=your_email@126.com
MAIL_126_PASSWORD=your_auth_code
```

**注意：** `.env` 文件包含敏感信息，不要提交到 git 仓库。

## Environment Variables

从 `.env` 文件加载环境变量：

```python
from dotenv import load_dotenv
import os

load_dotenv('/Users/colinspace/.claude/skills/126mail-skill/.env')

email_addr = os.getenv('MAIL_126_ADDR')
password = os.getenv('MAIL_126_PASSWORD')
```

安装 dotenv：
```bash
pip install python-dotenv
```