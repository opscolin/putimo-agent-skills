#!/usr/bin/env python3
"""
126邮箱读取工具
基于 IMAP 协议读取网易126邮件

使用前需要：
1. 开启 IMAP 服务：登录126邮箱 -> 设置 -> POP3/SMTP/IMAP -> 开启IMAP服务
2. 获取授权码：设置中生成授权码（不是登录密码）
"""

import os
from imapclient import IMAPClient
import email
from datetime import datetime, timedelta
from typing import Optional

from imapclient import IMAPClient
import email.utils
import email.header
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def decode_imap_utf7(s: Optional[str]) -> Optional[str]:
    """将 IMAP 修改的 UTF-7 字符串转为普通字符串"""
    if not s:
        return s
    try:
        # IMAP 使用的 modified UTF-7 可以用 imaplib 的 decode 或自己实现
        # 简单方法：如果是 bytes，直接解码；但这里 s 是 str，需要转成 ascii 然后解码
        # 更严谨：使用 imapclient 自带的 decode_utf7 (但未导出)，我们手动实现
        # 参考：https://stackoverflow.com/questions/6916663/decoding-imap-modified-utf-7-to-utf-8
        import binascii
        # IMAP modified UTF-7 规则：& 开始，- 结束，中间为 base64 编码的 UTF-16BE
        result = []
        i = 0
        while i < len(s):
            if s[i] == '&':
                i += 1
                end = s.find('-', i)
                if end == -1:
                    end = len(s)
                if end == i:
                    # 空序列，代表 &
                    result.append('&')
                else:
                    # base64 解码得到 UTF-16BE 字节
                    b64 = s[i:end]
                    # 补齐缺失的 padding
                    missing = len(b64) % 4
                    if missing:
                        b64 += '=' * (4 - missing)
                    try:
                        decoded = binascii.a2b_base64(b64)
                        # 假设编码为 UTF-16BE
                        result.append(decoded.decode('utf-16be'))
                    except:
                        # 解码失败，保留原样
                        result.append(f'&{b64}-')
                i = end + 1
            else:
                j = s.find('&', i)
                if j == -1:
                    result.append(s[i:])
                    break
                result.append(s[i:j])
                i = j
        return ''.join(result)
    except Exception:
        return s

def decode_address(addr) -> str:
    """解码 Address 对象"""
    if not addr:
        return ""
    name = addr.name
    if name:
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        if name.startswith('=?'):
            name = decode_mime_word(name)
    mailbox = addr.mailbox.decode('utf-8') if isinstance(addr.mailbox, bytes) else addr.mailbox
    host = addr.host.decode('utf-8') if isinstance(addr.host, bytes) else addr.host
    email_addr = f"{mailbox}@{host}"
    if name:
        return f"{name} <{email_addr}>"
    return email_addr

import email.header

def decode_mime_word(encoded) -> str:
    """解码 MIME encoded word 如 =?UTF-8?B?xxxx?="""
    import re
    import base64
    pattern = r'=\?([^?]+)\?([BQbq])\?([^?]*)\?='
    matches = re.findall(pattern, encoded)
    result = []
    for charset, encoding, text in matches:
        if encoding.upper() == 'B':
            try:
                result.append(base64.b64decode(text + '==').decode(charset, errors='replace'))
            except:
                result.append(text)
        elif encoding.upper() == 'Q':
            try:
                result.append(bytes.fromhex(text.replace('=', '%')).decode(charset, errors='replace'))
            except:
                result.append(text)
    return ''.join(result) if result else encoded

def decode_header_value(value) -> str:
    """解码 ENVELOPE 中的字符串字段（可能 None，可能是 tuple 包含显示名和邮箱）"""
    if not value:
        return ""
    if isinstance(value, tuple):
        return decode_address(value[0]) if value else ""
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    if value.startswith('=?'):
        return decode_mime_word(value)
    return decode_imap_utf7(value)

def parse_body_structure_for_attachments(body_struct):
    """
    递归解析 BODYSTRUCTURE，返回是否有附件（bool）以及附件文件名列表（str）
    网易返回的 BODYSTRUCTURE 格式：对于 multipart 是列表，每部分又是一个列表。
    附件特征：'disposition' 字段为 'attachment' 或 'inline' 且带有 'filename' 参数。
    """
    has_attachment = False
    filenames = []
    
    if not isinstance(body_struct, (list, tuple)):
        return has_attachment, filenames
    
    # 第一项如果是字符串，表示 mime-type，那么这是一个 leaf part
    if isinstance(body_struct[0], str):
        # 基本类型：body type, subtype, 参数列表, content-id, description, encoding, size, ...
        # 附件标志通常在 disposition 里（如果存在）
        # 网易结构: [type, subtype, params, id, desc, encoding, size, ... , disposition, ...]
        # 通常 disposition 在索引 8 或更后，我们遍历查找元组类型的项
        for item in body_struct:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                # 可能是 disposition 元组，比如 ['attachment', ['filename', 'abc.pdf']]
                if item[0] in ('attachment', 'inline'):
                    has_attachment = True
                    # 提取文件名
                    if len(item) > 1 and isinstance(item[1], list):
                        for i in range(0, len(item[1]), 2):
                            if item[1][i].lower() == 'filename':
                                filenames.append(decode_imap_utf7(item[1][i+1]))
                    break
    else:
        # multipart 类型：第一个子元素是各个 part 的列表
        for part in body_struct:
            # 跳过第一项如果是数字（multipart 结构：['mixed', ...]）需要识别
            if not isinstance(part, (list, tuple)):
                continue
            sub_has, sub_names = parse_body_structure_for_attachments(part)
            has_attachment |= sub_has
            filenames.extend(sub_names)
    
    return has_attachment, filenames

def fetch_recent_emails_126(email: str, password: str, days: int = 7) -> List[Dict]:
    """
    获取最近 N 天的邮件，返回包含详细信息的字典列表。
    字段：
        'uid' : int
        'from' : str (发件人)
        'subject' : str (标题)
        'date' : datetime (收件时间)
        'has_attachment' : bool
        'attachments' : List[str] (附件文件名列表)
        'cc' : List[str] (抄送地址，每个地址为字符串)
    """
    with IMAPClient("imap.126.com", use_uid=True) as server:
        server.login(email, password)
        # 绕过 "Unsafe Login"
        server.id_({"name": "MyMailFetcher", "version": "2.0"})
        server.select_folder('INBOX')
        
        # 计算起始日期（使用 SINCE 条件，注意日期格式需要英文月份缩写）
        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        # 使用 SINCE 搜索最近邮件
        uids = server.search(['SINCE', since_date])
        
        results = []
        for uid in uids:
            # 一次性获取信封和正文结构
            data = server.fetch(uid, ['ENVELOPE', 'BODYSTRUCTURE'])
            msg_info = data[uid]
            
            envelope = msg_info.get(b'ENVELOPE')
            body_struct = msg_info.get(b'BODYSTRUCTURE')
            
            # 解析信封
            if envelope:
                # 发件人：envelope.from 是一个 tuple 的列表，取第一个
                from_tuple = envelope.from_ if envelope.from_ else None
                from_addr = decode_address(from_tuple[0]) if from_tuple else ""
                
                # 主题
                subject_raw = envelope.subject or b""
                if isinstance(subject_raw, bytes):
                    subject = decode_header_value(subject_raw.decode('utf-8'))
                else:
                    subject = decode_header_value(subject_raw)
                
                # 日期字符串
                date_str = envelope.date or ""
                # 解析为标准 datetime
                try:
                    date_obj = email.utils.parsedate_to_datetime(date_str)
                except:
                    date_obj = datetime.now()
                
                # 抄送：envelope.cc 是 list of tuples
                cc_list = []
                if envelope.cc:
                    for cc in envelope.cc:
                        cc_addr = decode_header_value(cc)
                        if cc_addr:
                            cc_list.append(cc_addr)
            else:
                from_addr = subject = date_obj = None
                cc_list = []
            
            # 解析附件信息
            has_attachment = False
            attachment_names = []
            if body_struct:
                has_attachment, attachment_names = parse_body_structure_for_attachments(body_struct)
            
            results.append({
                'uid': uid,
                'from': from_addr,
                'subject': subject,
                'date': date_obj,
                'has_attachment': has_attachment,
                'attachments': attachment_names,
                'cc': cc_list,
            })
        
        return results


def fetch_email_content_126(account: str, password: str, uid: int) -> Dict:
    """
    根据邮件 UID 获取邮件完整内容
    :param account: 邮箱账号 (例如 user@126.com)
    :param password: 授权码
    :param uid: 邮件的 UID
    :return: 包含 subject, from, date, body, html_body, attachments 的字典
    """
    with IMAPClient("imap.126.com", use_uid=True) as server:
        server.login(account, password)
        server.id_({"name": "MyMailFetcher", "version": "2.0"})
        server.select_folder('INBOX')

        msg_data = server.fetch(uid, ['RFC822'])
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
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = payload.decode(charset, errors='ignore')
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='ignore')

        return {
            'subject': decode_mime_word(msg['Subject'] or ''),
            'from': decode_mime_word(msg['From'] or ''),
            'date': msg['Date'],
            'body': body,
            'html_body': html_body,
            'attachments': attachments
        }

if __name__ == '__main__':
    from dotenv import load_dotenv

    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    email_addr = os.getenv('MAIL_126_ADDR')
    password = os.getenv('MAIL_126_PASSWORD')

    if not email_addr or not password:
        print("请设置环境变量: MAIL_126_ADDR, MAIL_126_PASSWORD")
        exit(1)

    print("=== 最近7天邮件列表 ===")
    emails = fetch_recent_emails_126(email_addr, password, days=3)
    for e in emails:
        print(f"[{e['uid']}] {e['subject']} | {e['from']} | {e['date']} | 附件: {e['has_attachment']}")

    if emails:
        print(f"\n=== 读取第 {emails[0]['uid']} 封邮件内容 ===")
        content = fetch_email_content_126(email_addr, password, emails[0]['uid'])
        print(f"主题: {content['subject']}")
        print(f"正文:\n{content['body'][:500]}...")
