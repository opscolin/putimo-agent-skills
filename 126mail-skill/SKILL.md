---
name: mail-skill
description: Use when needing to read emails via IMAP protocol, including fetching recent emails by days or reading specific email content with attachments information. Supports 126 mail, enterprise mail (qiye.163.com), and any IMAP-compatible email service.
---

# Mail Skill

## Overview

读取邮箱邮件，基于 IMAP 协议，支持多种邮箱服务：

| 邮箱类型 | IMAP 地址 |
|----------|-----------|
| 网易 126 | imap.126.com |
| 163 邮箱 | imap.163.com |
| 网易企业邮箱 | imaphz.qiye.163.com |
| QQ 邮箱 | imap.qq.com |

## When to Use

- 需要查看邮箱的最近 N 天邮件
- 需要读取某封邮件的完整内容
- 需要了解邮件是否有附件

## Prerequisites

需要安装依赖:

```bash
pip install imapclient python-dotenv
```

需要在 `~/.claude/skills/mail-skill/` 目录下创建 `.env` 文件配置邮箱账号：

```bash
cd ~/.claude/skills/mail-skill/
touch .env
```

`.env` 文件内容（根据你的邮箱类型选择对应的 IMAP 地址）：

```env
# IMAP 服务器地址
MAIL_IMAP_ADDR=imap.qq.com

# 邮箱地址
MAIL_USER_ADDR=your_email@qq.com

# 授权码（不是登录密码）
MAIL_USER_PASSWORD=your_auth_code
```

**授权码获取方式：**

| 邮箱类型 | 获取路径 |
|----------|----------|
| 126/163 | 登录邮箱 → 设置 → POP3/SMTP/IMAP → 开启 IMAP 服务 → 生成授权码 |
| 网易企业邮箱 | 登录邮箱网页版 → 设置 → POP3/SMTP/IMAP → 生成授权码 |
| QQ 邮箱 | 设置 → 账户 → POP3/SMTP服务 → 开启服务 → 生成授权码 |

## Core Functions

### 1. 获取最近 N 天邮件列表

```python
from mail126 import fetch_recent_emails_126

emails = fetch_recent_emails_126(email_addr, password, days=7)
```

返回邮件列表，每封邮件包含 **5 个必需字段**：
- `uid`: 邮件唯一标识
- `subject`: 邮件主题
- `from`: 发件人
- `date`: 收件时间 (datetime)
- `has_attachment`: 是否有附件 (bool)

可选字段：
- `attachments`: 附件文件名列表
- `cc`: 抄送地址列表

### 2. 读取单封邮件内容

```python
from mail126 import fetch_email_content_126

content = fetch_email_content_126(email_addr, password, uid)
```

返回邮件内容，包含：
- `subject`: 主题
- `from`: 发件人
- `date`: 时间
- `body`: 纯文本正文
- `html_body`: HTML 正文
- `attachments`: 附件列表

## Quick Reference

| 功能 | 函数 | 必需参数 |
|------|------|----------|
| 最近 N 天邮件 | `fetch_recent_emails_126` | email_addr, password, days |
| 单封邮件内容 | `fetch_email_content_126` | email_addr, password, uid |

## Common Mistakes

### 1. 使用登录密码而非授权码

邮箱必须使用授权码登录，授权码需要在邮箱设置中生成：
- 登录邮箱 → 设置 → POP3/SMTP/IMAP → 开启服务 → 生成授权码

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

load_dotenv('/Users/colinspace/.claude/skills/mail-skill/.env')

email_addr = os.getenv('MAIL_USER_ADDR')
password = os.getenv('MAIL_USER_PASSWORD')

# 获取最近 7 天的邮件
emails = fetch_recent_emails_126(email_addr, password, days=7)

for email in emails:
    print(f"主题: {email['subject']}")
    print(f"发件人: {email['from']}")
    print(f"时间: {email['date']}")
    print(f"有附件: {email['has_attachment']}")
    print('---')

# 读取特定邮件内容
content = fetch_email_content_126(email_addr, password, uid=12345)
print(content['body'])
```

## .env 配置文件

在 `~/.claude/skills/mail-skill/` 目录下创建 `.env` 文件：

```bash
cd ~/.claude/skills/mail-skill/
touch .env
```

编辑 `.env` 文件，添加以下配置：

```env
# IMAP 服务器地址
MAIL_IMAP_ADDR=imaphz.qiye.163.com

# 邮箱地址
MAIL_USER_ADDR=your_email@company.com

# 授权码（不是登录密码）
MAIL_USER_PASSWORD=your_auth_code
```

**注意：** `.env` 文件包含敏感信息，不要提交到 git 仓库。

## Environment Variables

从 `.env` 文件加载环境变量：

```python
from dotenv import load_dotenv
import os

load_dotenv('/Users/colinspace/.claude/skills/mail-skill/.env')

email_addr = os.getenv('MAIL_USER_ADDR')
password = os.getenv('MAIL_USER_PASSWORD')
imap_server = os.getenv('MAIL_IMAP_ADDR')
```

安装 dotenv：
```bash
pip install python-dotenv
```