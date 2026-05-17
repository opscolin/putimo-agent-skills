---
name: cloud-billing-report
description: 云平台账单对比分析报告生成技能，目前支持'阿里云'和'腾讯云'。自动从阿里云/腾讯云 API 获取账单数据，对比两个月份的费用变化，生成详细分析报告并通过邮件发送。使用场景：生成月度账单汇总/明细文件、对比分析费用变化、发送 HTML 格式报告邮件给指定收件人。
---
# 云平台账单对比分析报告生成技能


## 核心功能

1. **账单数据获取**: 从阿里云/腾讯云 Billing API 获取指定月份的账单汇总和明细数据
2. **对比分析**: 自动对比两个月（上月 vs 本月）的费用变化
3. **报告生成**: 生成 Markdown 格式的详细分析报告
4. **邮件发送**: 将报告转换为 HTML 并发送给指定收件人

## 快速开始

### 前置准备

确保已设置以下环境变量：

```bash
# 阿里云 API 密钥（从 https://ram.console.aliyun.com/manage/ak 获取）
export ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret

# 腾讯云 API 密钥（从 https://console.cloud.tencent.com/cam/capi 获取）
export TENCENTCLOUD_SECRET_ID=your_secret_id
export TENCENTCLOUD_SECRET_KEY=your_secret_key

# 邮件发送配置
export EMAIL_HOST=smtp.qq.com
export EMAIL_USER=your-email@company.com
export EMAIL_PASSWORD=your_auth_code
export EMAIL_FROM_NAME=云平台账单报告
```

### 基本用法

```bash
# 进入技能目录
cd ~/Documents/AI-Skills/colinspace-skills/skills/cloud-billing-report

# 生成上个月的对比报告（对比上月和上上月，默认是云平台是腾讯云）
# 生成的 CSV 和 Markdown 文件会保存在当前工作目录下
python scripts/generate_billing_report.py

# 生成指定月份的报告
python scripts/generate_billing_report.py 2026-02

# 生成指定云平台的报告
python scripts/generate_billing_report.py 2026-02 --cloud aliyun

# 生成指定云平台的报告并发送邮件
python scripts/generate_billing_report.py 2026-02 --cloud aliyun --send-email 

# 指定收件人和抄送人
python scripts/generate_billing_report.py 2026-02 --send-email -t liuchao@company.com -c ops@company.com,finance@company.com

# 指定输出目录（生成的文件会保存在该目录下）
python scripts/generate_billing_report.py 2026-02 -o /path/to/output
```

**注意**: 默认情况下，生成的 CSV 和 Markdown 文件会保存在运行命令时的当前工作目录下。

## 工作流程

### 完整流程（推荐）

使用 `generate_billing_report.py` 一键完成：

```
1. 检查/生成上个月账单数据 (business_summary + product_summary)
   ↓
2. 检查/生成上上个月账单数据
   ↓
3. 对比分析两个月份数据
   ↓
4. 生成 Markdown 报告
   ↓
5. (可选) 发送 HTML 邮件
```

### 分步执行 （以阿里云为例）

如需单独控制每个步骤：

```bash
# 步骤 1: 生成账单汇总
python aliyun_billing_business_summary.py 2026-02

# 步骤 2: 生成账单明细
python aliyun_billing_product_summary.py 2026-02

# 步骤 3: 发送已有报告
python send_billing_report.py aliyun_billing_report_202602.md -t recipient@company.com -c cc1@company.com,cc2@company.com
```

## 脚本说明

### generate_billing_report.py

主流程脚本，自动完成数据获取、分析、报告生成和邮件发送。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `month` | 目标月份 (YYYY-MM 或 "last") | last |
| `-o, --output-dir` | 输出目录 | 当前目录 |
| `--send-email` | 生成后发送邮件 | 否 |
| `-t, --to` | 收件人邮箱 | 从环境变量或配置文件读取 |
| `-c, --cc` | 抄送人邮箱 (逗号分隔) | 从环境变量或配置文件读取 |
| `--cloud` | 云平台名称 (aliyun/tencentcloud) | 从环境变量或配置文件读取 |

### aliyun_billing_business_summary.py

获取账单汇总数据（按产品分组）。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `month` | 月份 (YYYY-MM 或 "last"/"current") | last |
| `-o, --output-dir` | 输出目录 | 当前目录 |

**输出文件**: `aliyun_billing_YYYYMM_business_summary.csv`

### aliyun_billing_product_summary.py

获取账单明细数据（按资源分组，支持分页）。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `month` | 月份 (YYYY-MM 或 "last"/"current") | last |
| `-o, --output-dir` | 输出目录 | 当前目录 |
| `--limit` | 每页记录数 (最大 1000) | 1000 |

**输出文件**: `aliyun_billing_YYYYMM_product_summary.csv`

### send_billing_report.py

发送报告邮件（Markdown 转 HTML）。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `report_path` | Markdown 报告文件路径 | 必填 |
| `-t, --to` | 收件人邮箱 | 从环境变量或配置文件读取 |
| `-c, --cc` | 抄送人邮箱 (逗号分隔) | 从环境变量或配置文件读取 |
| `-s, --subject` | 邮件主题 | 自动生成，但是依赖于云平台名称 |

### markdown_converter.py

Markdown 转 HTML 工具（内部使用）。

## 输出文件说明

### business_summary.csv

| 字段 | 说明 |
|------|------|
| 分组 key | 产品编码（如 ecs） |
| 分组名称 | 产品名称（如 云服务器 ECS） |
| 原价 | 产品原价 |
| 实际费用 | RealTotalCost，实际代支付费用（**核心字段**） |
| 现金费用 | 现金支付费用 |

### product_summary.csv
f.write("产品名称,产品编码,子产品名称,子产品编码,资源别名,资源 ID,付费模式,原价,实际费用,现金支付,折扣,账单类型\n")
            
| 字段 | 说明 |
|------|------|
| 产品名称 | 产品中文名称 |
| 产品编码 | 产品编码 |
| 子产品名称 | 子产品名称 |
| 子产品编码| 子产品编码 |
| 资源别名 | 资源别名 |
| 资源 ID | 资源唯一标识 |
| 付费模式 | 按量计费/包年包月 |
| 实际费用 | RealTotalCost/PretaxAmount（**核心字段**） |
| 现金支付| 现金支付 |
| 折扣 | 折扣率 |
| 账单类型 | 正常/异常 |

## 报告内容

生成的报告包含以下固定格式章节：

### 一、整体费用概览
- 两个月份的总费用对比
- 变化金额和变化百分比

### 二、产品费用变化分析 (Business Summary)
- **2.1 费用变化汇总表**: 所有产品的费用对比（完整列表且按照'本月费用'倒排序）
- **2.2 费用降低 TOP 5**: 按变化金额排序的前 5 个下降产品
- **2.3 费用增长产品**: 所有费用增长的产品列表
- **2.4 费用持平产品**: 变化比例小于 1% 的产品

### 三、费用变化原因分析 (Product Summary)
对每个重点变化产品（变化金额>1000 或 变化比例>20%）进行详细分析：
- 产品费用变化概览
- 明细变化表格（按资源/子产品分组）
- 原因分析（基于付费模式和用量变化）

### 四、总结
- **4.1 费用下降主要驱动因素**: TOP 5 下降产品及其占比
- **4.2 费用稳定/增长项**: 稳定产品和增长产品列表
- **4.3 建议**: 成本优化和异常核查建议

**报告特点**:
- 所有费用数据保留 2 位小数，使用千分位格式
- 变化金额和比例带有 +/- 符号便于识别
- 原因分析基于实际账单数据自动生成
- 报告格式固定，每次生成保持一致

## 常见问题

### API 认证失败

```
✗ API 调用失败：InvalidAccessKeyId.NotFound
```

**解决**: 
1. 检查 `ALIBABA_CLOUD_ACCESS_KEY_ID` 和 `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 是否正确
2. 确认 RAM 用户有 Billing 相关权限（如 `AliyunBSSFullAccess`）

### 邮件发送失败

```
✗ SMTP 认证失败
```

**解决**: 
- 确认 `EMAIL_PASSWORD` 是授权码而非登录密码
- QQ 邮箱需在设置中开启 SMTP 服务获取授权码

### 数据不全

明细数据可能超过 1000 条，脚本会自动分页获取。如需调整每页数量：

```bash
python aliyun_billing_product_summary.py 2026-02 --limit 500
```

## 相关文件

- 报告模板：`references/report_template.md`
- 所有脚本：`scripts/` 目录

## 使用示例

### 示例 1: 每月自动生成

```bash
# 添加到 crontab，每月 5 号生成上月报告
0 9 5 * * cd ~/Documents/AI-Skills/anthropics-skills/skills/aliyun-billing-report/scripts && \
    export ALIBABA_CLOUD_ACCESS_KEY_ID=xxx && \
    export ALIBABA_CLOUD_ACCESS_KEY_SECRET=xxx && \
    export EMAIL_HOST=smtp.qq.com && \
    export EMAIL_USER=xxx@company.com && \
    export EMAIL_PASSWORD=xxx && \
    export EMAIL_FROM_NAME=阿里云账单报告 && \
    python generate_billing_report.py last --send-email
```

### 示例 2: 指定收件人

```bash
python generate_billing_report.py 2026-02 \
    --send-email \
    -t cfo@company.com \
    -c finance-team@company.com;ops@company.com
```

### 示例 3: 仅获取数据

```bash
# 只生成账单汇总，不生成报告
python aliyun_billing_business_summary.py 2026-02 -o /data/billing/
```

## 邮件格式

生成的邮件采用固定格式，包含：

- **HTML 格式**: 美观的表格和样式
- **附件**: Markdown 原始报告文件
- **主题**: 阿里云账单分析报告 - YYYY 年 M 月 vs N 月

邮件内容结构与报告一致，包含完整的费用分析和建议。
