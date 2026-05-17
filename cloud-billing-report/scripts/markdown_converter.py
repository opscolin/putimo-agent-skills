#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML Converter Tool

将 Markdown 格式的文档转换为美观的 HTML 格式
支持标题、表格、引用、列表、代码块等常见 Markdown 语法

Usage:
    from markdown_converter import markdown_to_html
    
    with open('report.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html = markdown_to_html(md_content, title="报告标题")
"""

import re
from typing import Optional


def convert_tables_to_html(text: str) -> str:
    """
    转换 Markdown 表格为 HTML 表格
    
    Args:
        text: 包含 Markdown 表格的文本
    
    Returns:
        转换后的 HTML 文本
    """
    lines = text.split('\n')
    result = []
    in_table = False
    table_rows = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测表格行 (包含 | 的行，且不是纯分隔符)
        if '|' in line and stripped.startswith('|') and stripped.endswith('|'):
            # 检查是否是分隔行 (包含 ---)
            if re.match(r'^\|\s*[-:|]+\s*\|$', stripped):
                continue  # 跳过分隔行
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(stripped)
        else:
            if in_table and table_rows:
                # 转换表格为 HTML
                result.append(convert_table_rows_to_html(table_rows))
                in_table = False
                table_rows = []
            result.append(line)
    
    # 处理末尾的表格
    if in_table and table_rows:
        result.append(convert_table_rows_to_html(table_rows))
    
    return '\n'.join(result)


def convert_table_rows_to_html(rows: list) -> str:
    """
    将 Markdown 表格行转换为 HTML 表格
    
    Args:
        rows: Markdown 表格行列表
    
    Returns:
        HTML 表格字符串
    """
    if len(rows) < 1:
        return ''
    
    html_table = ['<table>', '<thead>', '<tr>']
    
    # 表头
    header_cells = [cell.strip() for cell in rows[0].split('|')]
    header_cells = [c for c in header_cells if c]  # 移除空单元格
    for cell in header_cells:
        html_table.append(f'<th>{cell}</th>')
    html_table.append('</tr>')
    html_table.append('</thead>')
    
    # 表体
    if len(rows) > 1:
        html_table.append('<tbody>')
        for idx, row in enumerate(rows[1:]):
            cells = [cell.strip() for cell in row.split('|')]
            cells = [c for c in cells if c]
            html_table.append('<tr>')
            for cell in cells:
                # 高亮负数和百分比
                cell_html = cell
                if '-' in cell and '¥' in cell:
                    cell_html = f'<span class="negative">{cell}</span>'
                elif '+' in cell and '¥' in cell:
                    cell_html = f'<span class="positive">{cell}</span>'
                elif re.match(r'^-?\d+\.?\d*%$', cell.strip()):
                    if cell.startswith('-'):
                        cell_html = f'<span class="negative">{cell}</span>'
                    else:
                        cell_html = f'<span class="positive">{cell}</span>'
                html_table.append(f'<td>{cell_html}</td>')
            html_table.append('</tr>')
        html_table.append('</tbody>')
    
    html_table.append('</table>')
    
    return '\n'.join(html_table)


def process_blockquotes(text: str) -> str:
    """
    处理引用块
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    lines = text.split('\n')
    result = []
    in_blockquote = False
    blockquote_content = []
    
    for line in lines:
        if line.strip().startswith('>'):
            if not in_blockquote:
                in_blockquote = True
                blockquote_content = []
            # 移除 > 符号
            content = re.sub(r'^>\s*', '', line.strip())
            blockquote_content.append(content)
        else:
            if in_blockquote and blockquote_content:
                content = ' '.join(blockquote_content)
                result.append(f'<blockquote>{content}</blockquote>')
                in_blockquote = False
                blockquote_content = []
            result.append(line)
    
    # 处理末尾的引用
    if in_blockquote and blockquote_content:
        content = ' '.join(blockquote_content)
        result.append(f'<blockquote>{content}</blockquote>')
    
    return '\n'.join(result)


def process_horizontal_rules(text: str) -> str:
    """
    处理水平分隔线 (移除或转换为样式)
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    # 移除单独的 --- 行
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # 检测分隔线 (--- 或 *** 或 ___)
        if re.match(r'^([-*_])\1{2,}$', stripped):
            continue  # 跳过分隔线
        result.append(line)
    return '\n'.join(result)


def process_lists(text: str) -> str:
    """
    处理列表 (有序和无序)
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    lines = text.split('\n')
    result = []
    in_ul = False
    in_ol = False
    list_items = []
    list_type = None
    
    for line in lines:
        stripped = line.strip()
        
        # 检测无序列表 (- 或 * 开头)
        ul_match = re.match(r'^[-*]\s+(.+)$', stripped)
        # 检测有序列表 (数字。开头)
        ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
        
        if ul_match:
            if in_ol:
                # 结束有序列表
                result.append(f'<ol>{"".join(f"<li>{item}</li>" for item in list_items)}</ol>')
                in_ol = False
                list_items = []
            if not in_ul:
                in_ul = True
                list_type = 'ul'
            list_items.append(ul_match.group(1))
        elif ol_match:
            if in_ul:
                # 结束无序列表
                result.append(f'<ul>{"".join(f"<li>{item}</li>" for item in list_items)}</ul>')
                in_ul = False
                list_items = []
            if not in_ol:
                in_ol = True
                list_type = 'ol'
            list_items.append(ol_match.group(1))
        else:
            if in_ul and list_items:
                result.append(f'<ul>{"".join(f"<li>{item}</li>" for item in list_items)}</ul>')
                in_ul = False
                list_items = []
            elif in_ol and list_items:
                result.append(f'<ol>{"".join(f"<li>{item}</li>" for item in list_items)}</ol>')
                in_ol = False
                list_items = []
            result.append(line)
    
    # 处理末尾的列表
    if in_ul and list_items:
        result.append(f'<ul>{"".join(f"<li>{item}</li>" for item in list_items)}</ul>')
    elif in_ol and list_items:
        result.append(f'<ol>{"".join(f"<li>{item}</li>" for item in list_items)}</ol>')
    
    return '\n'.join(result)


def process_inline_formatting(text: str) -> str:
    """
    处理行内格式 (加粗、斜体、代码等)
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    # 处理加粗 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # 处理斜体 *text*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    
    # 处理行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    return text


def process_paragraphs(text: str) -> str:
    """
    处理段落 - 只处理纯文本行，跳过 HTML 标签和空行
    
    Args:
        text: 文本内容
    
    Returns:
        处理后的文本
    """
    lines = text.split('\n')
    result = []
    paragraph_lines = []
    
    def flush_paragraph():
        if paragraph_lines:
            content = ' '.join(paragraph_lines)
            if content.strip():
                result.append(f'<p>{content}</p>')
            paragraph_lines.clear()
    
    # Table-related tags that should not be wrapped
    table_pattern = re.compile(r'^<(table|thead|tbody|tr|th|td|/table|/thead|/tbody|/tr)')
    
    for line in lines:
        stripped = line.strip()
        
        # 空行 - 刷新段落
        if not stripped:
            flush_paragraph()
            continue
        
        # 如果已经是 HTML 块级标签或表格相关标签，先刷新段落，然后直接添加
        if re.match(r'^<(h[1-6]|table|ul|ol|blockquote|p|div)', stripped) or table_pattern.match(stripped):
            flush_paragraph()
            result.append(stripped)
        # 普通文本 - 收集到段落
        else:
            paragraph_lines.append(stripped)
    
    # 处理末尾的段落
    flush_paragraph()
    
    return '\n'.join(result)


def markdown_to_html(md_content: str, title: Optional[str] = None, 
                     include_full_html: bool = True,
                     custom_css: Optional[str] = None) -> str:
    """
    将 Markdown 内容转换为 HTML
    
    Args:
        md_content: Markdown 内容
        title: 文档标题 (可选)
        include_full_html: 是否包含完整的 HTML 文档结构
        custom_css: 自定义 CSS (可选)
    
    Returns:
        HTML 字符串
    
    Example:
        >>> with open('report.md', 'r', encoding='utf-8') as f:
        ...     md_content = f.read()
        >>> html = markdown_to_html(md_content, title="报告标题")
    """
    html = md_content
    
    # 1. 提取并移除文档标题 (如果存在)
    if not title:
        title_match = re.search(r'^# (.+)$', html, re.MULTILINE)
        title = title_match.group(1) if title_match else "文档"
    
    # 2. 处理水平分隔线 (在表格处理之前)
    html = process_horizontal_rules(html)
    
    # 3. 处理标题 (按顺序处理，避免冲突)
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 4. 处理引用块
    html = process_blockquotes(html)
    
    # 5. 处理列表
    html = process_lists(html)
    
    # 6. 处理表格
    html = convert_tables_to_html(html)
    
    # 7. 处理行内格式
    html = process_inline_formatting(html)
    
    # 8. 处理段落
    html = process_paragraphs(html)
    
    # 9. 清理多余的空白和空段落
    html = re.sub(r'<p>\s*</p>', '', html)
    
    # 10. 如果是完整 HTML，添加文档结构
    if include_full_html:
        default_css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a73e8;
            font-size: 24px;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h2 {
            color: #1a73e8;
            font-size: 20px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
            margin-top: 30px;
        }
        h3 {
            font-size: 18px;
            color: #333;
            margin-top: 25px;
        }
        h4 {
            font-size: 16px;
            color: #555;
            margin-top: 20px;
        }
        h5 {
            font-size: 15px;
            color: #666;
            margin-top: 18px;
        }
        h6 {
            font-size: 14px;
            color: #777;
            margin-top: 16px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            text-align: left;
            padding: 12px 8px;
            border: 1px solid #dee2e6;
        }
        td {
            padding: 10px 8px;
            border: 1px solid #dee2e6;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e9ecef;
        }
        .positive {
            color: #28a745;
            font-weight: 600;
        }
        .negative {
            color: #dc3545;
            font-weight: 600;
        }
        blockquote {
            border-left: 4px solid #1a73e8;
            margin: 20px 0;
            padding: 15px 20px;
            background-color: #f8f9fa;
            color: #555;
            border-radius: 0 4px 4px 0;
        }
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        li {
            margin: 8px 0;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, Monaco, monospace;
        }
        p {
            margin: 10px 0;
            line-height: 1.8;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #888;
        }
        """
        
        if custom_css:
            default_css += custom_css
        
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{default_css}</style>
</head>
<body>
    <div class="container">
        {html}
        <div class="footer">
            <p>此邮件由系统自动发送 | 发送时间：{__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""
        return full_html
    
    return html


def create_email_html(md_content: str, subject: Optional[str] = None) -> str:
    """
    创建用于邮件发送的 HTML 内容
    
    Args:
        md_content: Markdown 内容
        subject: 邮件主题 (可选)
    
    Returns:
        完整的 HTML 邮件内容
    """
    return markdown_to_html(md_content, title=subject, include_full_html=True)


# 模块级工具函数，方便在其他模块中使用
def convert_markdown_file_to_html(input_path: str, output_path: Optional[str] = None, 
                                   title: Optional[str] = None) -> str:
    """
    将 Markdown 文件转换为 HTML 并可选保存到文件
    
    Args:
        input_path: 输入 Markdown 文件路径
        output_path: 输出 HTML 文件路径 (可选，如果不提供则返回字符串)
        title: 文档标题 (可选，默认使用 Markdown 中的第一个标题)
    
    Returns:
        HTML 字符串
    
    Example:
        >>> html = convert_markdown_file_to_html('report.md', 'report.html')
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html = markdown_to_html(md_content, title=title)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    return html


if __name__ == '__main__':
    # 简单的命令行测试
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python markdown_converter.py <input.md> [output.html]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        html = convert_markdown_file_to_html(input_file, output_file)
        if not output_file:
            print(html[:500] + "..." if len(html) > 500 else html)
        else:
            print(f"✓ Converted {input_file} to {output_file}")
    except FileNotFoundError:
        print(f"✗ File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
