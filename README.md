# ErisPulse EmailForwarder

用于监听邮件适配器并将邮件转发到其他平台的 ErisPulse 模块。

## 功能特性

- 监听邮件适配器接收的新邮件
- 支持将邮件转发到多个平台（云湖、Telegram、OneBot11、OneBot12等）
- 灵活的目标配置（用户/群组/频道）
- 支持多种匹配模式（通配符、正则表达式、精确匹配、包含/不包含、前缀/后缀）
- 支持自定义模板系统
- 自动格式化邮件内容（主题、发件人、正文、附件）

## 安装

```bash
# 通过 ErisPulse CLI 安装
epsdk install EmailForwarder

# 或使用 pip 安装
pip install ErisPulse-EmailForwarder
```

## 快速开始

### 基本配置

在 `config.toml` 中添加以下配置：

```toml
[EmailForwarder]
enabled = true

# 定义默认模板
[EmailForwarder.templates.default]
content = """新邮件

主题: {subject}
发件人: {from}
收件人: {to}

{body}

#匹配规则 {rule_name}"""

# 添加转发规则
[[EmailForwarder.rules]]
name = "转发所有邮件"
template = "default"

[[EmailForwarder.rules.targets]]
platform = "onebot11"
type = "user"
id = "你的用户ID"
```

## 配置说明

### 模块配置

| 配置项 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `enabled` | boolean | 否 | 是否启用模块，默认 true |
| `templates` | object | 否 | 模板定义 |
| `rules` | array | 否 | 转发规则列表 |

### 模板配置

模板使用简单的变量替换语法，支持以下变量：

| 变量 | 说明 |
|------|------|
| `{subject}` | 邮件主题 |
| `{from}` | 发件人 |
| `{to}` | 收件人 |
| `{time}` | 收件时间 |
| `{body}` | 邮件正文 |
| `{rule_name}` | 匹配规则名称 |
| `{attachments}` | 附件列表 |
| `{attachment_count}` | 附件数量 |

#### 模板示例

```toml
[EmailForwarder.templates.default]
content = """新邮件

主题: {subject}
发件人: {from}
收件人: {to}

{body}

#匹配规则 {rule_name}"""

[EmailForwarder.templates.simple]
content = """[{rule_name}] {subject}
来自: {from}
---
{body}"""

[EmailForwarder.templates.detailed]
content = """=== 新邮件通知 ===
主题: {subject}
发件人: {from}
收件人: {to}
时间: {time}

---
{body}

---
附件数量: {attachment_count}
{attachments}
---
规则: {rule_name}"""
```

### 匹配模式

支持以下匹配模式：

| 模式 | 说明 | 示例 |
|------|------|------|
| `wildcard` | 通配符匹配 | `*@company.com` |
| `regex` | 正则表达式 | `^.*@company\.com$` |
| `exact` | 精确匹配 | `noreply@example.com` |
| `contains` | 包含匹配 | `重要` |
| `not_contains` | 不包含匹配 | `广告` |
| `prefix` | 前缀匹配 | `[通知]` |
| `suffix` | 后缀匹配 | `@company.com` |

### 匹配条件

匹配条件使用数组配置，所有条件必须同时满足（AND逻辑）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `field` | string | 是 | 匹配字段：from/to/subject |
| `mode` | string | 是 | 匹配模式 |
| `value` | string | 是 | 匹配值 |

### 转发规则

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 规则名称 |
| `template` | string | 否 | 使用的模板名称，默认 default |
| `match` | array | 否 | 匹配条件列表 |
| `targets` | array | 是 | 转发目标列表 |

### 转发目标

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform` | string | 是 | 目标平台名称 |
| `type` | string | 是 | 目标类型（user/group/channel） |
| `id` | string | 是 | 目标ID |

## 配置示例

### 示例 1: 转发所有邮件

```toml
[[EmailForwarder.rules]]
name = "转发所有邮件"

[[EmailForwarder.rules.targets]]
platform = "telegram"
type = "user"
id = "123456789"
```

### 示例 2: 转发特定发件人的邮件（通配符匹配）

```toml
[[EmailForwarder.rules]]
name = "工作邮件转发"

[[EmailForwarder.rules.match]]
field = "from"
mode = "wildcard"
value = "*@company.com"

[[EmailForwarder.rules.targets]]
platform = "yunhu"
type = "group"
id = "G1001"
```

### 示例 3: 转发包含关键字的邮件（包含匹配）

```toml
[[EmailForwarder.rules]]
name = "重要邮件转发"

[[EmailForwarder.rules.match]]
field = "subject"
mode = "contains"
value = "紧急"

[[EmailForwarder.rules.targets]]
platform = "onebot11"
type = "user"
id = "2694611137"
```

### 示例 4: 多条件匹配（所有条件都必须满足）

```toml
[[EmailForwarder.rules]]
name = "公司重要邮件"

[[EmailForwarder.rules.match]]
field = "from"
mode = "suffix"
value = "@company.com"

[[EmailForwarder.rules.match]]
field = "subject"
mode = "contains"
value = "项目"

[[EmailForwarder.rules.targets]]
platform = "telegram"
type = "group"
id = "-1001234567890"
```

### 示例 5: 使用正则表达式匹配

```toml
[[EmailForwarder.rules]]
name = "通知邮件"

[[EmailForwarder.rules.match]]
field = "subject"
mode = "regex"
value = "^\\[通知\\].*"

[[EmailForwarder.rules.targets]]
platform = "yunhu"
type = "channel"
id = "C123456789"
```

### 示例 6: 排除广告邮件（不包含匹配）

```toml
[[EmailForwarder.rules]]
name = "正常邮件转发"

[[EmailForwarder.rules.match]]
field = "subject"
mode = "not_contains"
value = "广告"

[[EmailForwarder.rules.match]]
field = "subject"
mode = "not_contains"
value = "推广"

[[EmailForwarder.rules.targets]]
platform = "onebot11"
type = "group"
id = "987654321"
```

### 示例 7: 使用自定义模板

```toml
# 定义简洁模板
[EmailForwarder.templates.simple]
content = """[{rule_name}] {subject}
来自: {from}
---
{body}"""

# 使用简洁模板
[[EmailForwarder.rules]]
name = "简洁转发"
template = "simple"

[[EmailForwarder.rules.targets]]
platform = "telegram"
type = "user"
id = "123456789"
```

### 示例 8: 转发到多个平台

```toml
[[EmailForwarder.rules]]
name = "多平台转发"

[[EmailForwarder.rules.match]]
field = "from"
mode = "wildcard"
value = "important@company.com"

[[EmailForwarder.rules.targets]]
platform = "yunhu"
type = "group"
id = "G2001"

[[EmailForwarder.rules.targets]]
platform = "telegram"
type = "group"
id = "-1001234567890"

[[EmailForwarder.rules.targets]]
platform = "onebot11"
type = "user"
id = "2694611137"
```

## 支持的平台

- Yunhu - 云湖
- Telegram - Telegram
- OneBot11 - QQ等OneBot11协议平台
- OneBot12 - OneBot12协议平台
- Email - 邮件平台

## 使用方法

安装并配置完成后，启动 ErisPulse 即可自动转发邮件：

```bash
# 启动 ErisPulse
epsdk run main.py
```
别忘了安装对应的适配器哦~

## 故障排除

### 邮件未被转发

1. 检查 EmailAdapter 是否正常运行
2. 检查目标平台适配器是否已安装和启用
3. 查看日志文件确认错误信息
4. 验证配置文件中的平台名称、目标类型和ID是否正确
5. 确认匹配规则是否正确

### 模板未生效

1. 检查模板名称是否拼写正确
2. 确保模板配置中包含 `content` 字段
3. 验证模板变量格式是否正确（使用花括号 `{variable}`）

### 匹配规则不工作

1. 检查匹配模式是否正确支持
2. 验证正则表达式语法是否正确
3. 确认匹配值是否需要转义（如 `\n`、`\t` 等）
4. 查看日志确认匹配过程的详细信息

## 注意事项

1. 确保 EmailAdapter 已正确安装和配置
2. 目标平台的适配器需要已安装并启用
3. 匹配条件为空时匹配所有邮件
4. 多个匹配条件之间为 AND 逻辑（必须全部满足）
5. 正则表达式匹配失败时会记录警告并视为不匹配

## 开发

本项目遵循 ErisPulse 模块开发规范。

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！
