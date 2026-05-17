# putimo-agent-skills

汇总个人工作和生活场景中可以转化的 SKill，用于提升效率。

## Available Skills

### 1. [ansible](./ansible/) - Ansible 自动化运维

Ansible 自动化和编排工具包，用于管理 Ansible 清单、执行 playbook 和临时命令。

**核心功能：**
- 列出 inventory 结构和主机
- 验证和执行 playbook
- 主机连通性测试 (ping)
- 执行临时命令
- 生成新的 playbook 文件

**触发场景：** 询问列出或查询 Ansible inventory、运行或验证 playbook、执行临时 Ansible 命令、测试主机连通性、创建新的 Ansible playbook、或检查 Ansible 版本。

---

### 2. [cloud-billing-report](./cloud-billing-report/) - 云平台账单对比分析

阿里云和腾讯云账单对比分析报告生成技能。

**核心功能：**
- 从阿里云/腾讯云 Billing API 获取账单数据
- 对比两个月份的费用变化
- 生成 Markdown 格式详细分析报告
- 发送 HTML 格式报告邮件

**触发场景：** 生成月度账单汇总/明细文件、对比分析费用变化、发送 HTML 格式报告邮件给指定收件人。

---

### 3. [126mail-skill](./126mail-skill/) - 126邮箱读取

读取网易126邮箱的邮件，基于 IMAP 协议实现。

**核心功能：**
- 获取最近 N 天邮件列表（标题、收件时间、发件人、是否有附件）
- 读取单封邮件完整内容

**触发场景：** 需要查看126邮箱的最近N天邮件、读取某封邮件的完整内容、了解邮件是否有附件。

---

### 4. [weather](./weather/) - 高德天气查询

使用高德地图天气 API 查询指定地区的天气信息。

**核心功能：**
- 查询实况天气（温度、湿度、风向、风力、天气状况）
- 查询未来4天天气预报

**触发场景：** 用户请求查询天气、天气状况、天气预报、温度、湿度等天气相关信息。

---

## License

See [LICENSE](./LICENSE) file for details.