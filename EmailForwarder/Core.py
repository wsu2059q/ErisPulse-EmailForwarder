"""
ErisPulse 邮件转发模块

监听邮件并根据配置转发到其他平台
支持多种匹配模式和自定义模板系统

{!--< tips >!--}
此模块需要在启用邮件适配器后才能正常工作
配置文件中可以定义多个转发规则，每条规则可以匹配特定的邮件条件
{!--< /tips >!--}
"""
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import message
import fnmatch
import re
from typing import List, Dict, Any, Optional


class Main(BaseModule):
    """
    邮件转发模块主类
    """
    
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("EmailForwarder")
        self.storage = sdk.storage
        self.config_manager = sdk.config
        self.module_config = self._load_config()
        self.rules = self._load_rules()
        self.templates = self._load_templates()

    @staticmethod
    def get_load_strategy():
        """
        返回模块加载策略
        
        模块需要立即加载以监听邮件事件
        """
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,  # 立即加载，需要监听事件
            priority=50       # 中等优先级
        )

    def _load_config(self):
        """
        加载模块配置
        
        :return: 模块配置字典
        """
        self.logger.debug("开始加载 EmailForwarder 模块配置")
        config = self.config_manager.getConfig("EmailForwarder")
        
        # 检查配置是否有效（非空且为字典类型）
        if not config or not isinstance(config, dict):
            default_config = {
                "enabled": True,
                "rules": [],
                "templates": {
                    "default": {
                        "content": "新邮件\n\n主题: {subject}\n发件人: {from}\n收件人: {to}\n\n{body}\n\n#匹配规则 {rule_name}"
                    }
                }
            }
            self.config_manager.setConfig("EmailForwarder", default_config)
            if not config:
                self.logger.warning("未找到模块配置，已创建默认配置到 config.toml")
            else:
                self.logger.warning(f"模块配置类型错误（期望 dict，实际 {type(config).__name__}），已重置为默认配置")
            self.logger.debug(f"已创建默认配置: {default_config}")
            return default_config
        
        # 确保模板配置存在
        if "templates" not in config or not config["templates"]:
            config["templates"] = {
                "default": {
                    "content": "新邮件\n\n主题: {subject}\n发件人: {from}\n收件人: {to}\n\n{body}\n\n#匹配规则 {rule_name}"
                }
            }
            self.config_manager.setConfig("EmailForwarder", config)
            self.logger.debug("已添加默认模板配置")
        
        return config

    def _load_templates(self) -> Dict[str, str]:
        """
        加载模板配置
        
        :return: 模板字典 {name: content}
        """
        self.logger.debug("开始加载模板配置")
        templates = self.module_config.get("templates", {})
        result = {}
        
        for name, template_config in templates.items():
            if isinstance(template_config, dict):
                content = template_config.get("content", "")
            elif isinstance(template_config, str):
                content = template_config
            else:
                content = ""
            
            if content:
                result[name] = content
                self.logger.debug(f"加载模板 '{name}'，内容长度: {len(content)}")
        
        # 确保默认模板存在
        if "default" not in result:
            default_template = "新邮件\n\n主题: {subject}\n发件人: {from}\n收件人: {to}\n\n{body}\n\n#匹配规则 {rule_name}"
            result["default"] = default_template
            self.logger.debug("使用内置默认模板")
        
        self.logger.info(f"已加载 {len(result)} 个模板")
        return result

    def _load_rules(self) -> List[Dict[str, Any]]:
        """
        加载转发规则
        
        :return: 规则列表
        """
        self.logger.debug("开始加载转发规则")
        rules = self.module_config.get("rules", [])
        self.logger.info(f"已加载 {len(rules)} 条转发规则")
        for idx, rule in enumerate(rules):
            rule_name = rule.get("name", "未命名")
            targets_count = len(rule.get("targets", []))
            match_count = len(rule.get("match", []))
            self.logger.debug(f"规则 #{idx+1}: '{rule_name}', 匹配条件: {match_count}, 目标数量: {targets_count}")
        return rules

    def _match_wildcard(self, pattern: str, value: str) -> bool:
        """
        通配符匹配
        
        :param pattern: 匹配模式
        :param value: 实际值
        :return: 是否匹配
        """
        return fnmatch.fnmatch(value.lower(), pattern.lower())

    def _match_regex(self, pattern: str, value: str) -> bool:
        """
        正则表达式匹配
        
        :param pattern: 正则表达式
        :param value: 实际值
        :return: 是否匹配
        """
        try:
            return bool(re.search(pattern, value, re.IGNORECASE))
        except re.error as e:
            self.logger.warning(f"正则表达式匹配失败: pattern='{pattern}', error={e}")
            return False

    def _match_exact(self, pattern: str, value: str) -> bool:
        """
        精确匹配
        
        :param pattern: 匹配值
        :param value: 实际值
        :return: 是否匹配
        """
        return value.lower() == pattern.lower()

    def _match_contains(self, pattern: str, value: str) -> bool:
        """
        包含匹配
        
        :param pattern: 要包含的字符串
        :param value: 实际值
        :return: 是否匹配
        """
        return pattern.lower() in value.lower()

    def _match_not_contains(self, pattern: str, value: str) -> bool:
        """
        不包含匹配
        
        :param pattern: 不能包含的字符串
        :param value: 实际值
        :return: 是否匹配
        """
        return pattern.lower() not in value.lower()

    def _match_prefix(self, pattern: str, value: str) -> bool:
        """
        前缀匹配
        
        :param pattern: 前缀字符串
        :param value: 实际值
        :return: 是否匹配
        """
        return value.lower().startswith(pattern.lower())

    def _match_suffix(self, pattern: str, value: str) -> bool:
        """
        后缀匹配
        
        :param pattern: 后缀字符串
        :param value: 实际值
        :return: 是否匹配
        """
        return value.lower().endswith(pattern.lower())

    def _match_condition(self, match_config: Dict[str, Any], value: str) -> bool:
        """
        检查值是否匹配条件
        
        :param match_config: 匹配配置 {field, mode, value}
        :param value: 实际值
        :return: 是否匹配
        """
        mode = match_config.get("mode", "contains")
        pattern = match_config.get("value", "")
        
        # 映射匹配模式到对应的匹配函数
        match_methods = {
            "wildcard": self._match_wildcard,
            "regex": self._match_regex,
            "exact": self._match_exact,
            "contains": self._match_contains,
            "not_contains": self._match_not_contains,
            "prefix": self._match_prefix,
            "suffix": self._match_suffix
        }
        
        match_func = match_methods.get(mode, self._match_contains)
        result = match_func(pattern, value)
        
        self.logger.debug(f"匹配检查: 模式={mode}, 值='{value}', 模式值='{pattern}', 结果={result}")
        return result

    def _get_email_field_value(self, email_data: Dict[str, Any], field: str) -> str:
        """
        获取邮件字段值
        
        :param email_data: 邮件数据
        :param field: 字段名 (from/to/subject)
        :return: 字段值
        """
        field_map = {
            "from": "email_from",
            "to": "email_to",
            "subject": "email_subject"
        }
        return email_data.get(field_map.get(field, field), "")

    def _should_forward_email(self, email_data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """
        检查邮件是否应该根据此规则转发
        
        所有匹配条件都必须满足（AND逻辑）
        
        :param email_data: 邮件数据
        :param rule: 转发规则
        :return: 是否应该转发
        """
        rule_name = rule.get("name", "未命名")
        self.logger.debug(f"开始检查邮件是否匹配规则 '{rule_name}'")
        
        match_conditions = rule.get("match", [])
        
        # 如果匹配条件列表为空，则匹配所有邮件
        if not match_conditions:
            self.logger.debug(f"规则 '{rule_name}' 匹配条件为空，匹配所有邮件")
            return True
        
        # 检查所有匹配条件（AND逻辑）
        for idx, condition in enumerate(match_conditions):
            field = condition.get("field")
            value = self._get_email_field_value(email_data, field)
            
            if not self._match_condition(condition, value):
                self.logger.debug(f"规则 '{rule_name}': 条件 #{idx+1} (field={field}) 不匹配")
                return False
            
            self.logger.debug(f"规则 '{rule_name}': 条件 #{idx+1} (field={field}) 匹配成功")
        
        self.logger.debug(f"规则 '{rule_name}': 所有条件匹配成功")
        return True

    def _render_template(self, template: str, email_data: Dict[str, Any], rule: Dict[str, Any]) -> str:
        """
        渲染模板
        
        支持的变量:
        - {subject}: 邮件主题
        - {from}: 发件人
        - {to}: 收件人
        - {time}: 收件时间
        - {body}: 邮件正文
        - {rule_name}: 规则名称
        - {attachments}: 附件列表
        - {attachment_count}: 附件数量
        
        :param template: 模板内容
        :param email_data: 邮件数据
        :param rule: 转发规则
        :return: 渲染后的内容
        """
        self.logger.debug("开始渲染模板")
        
        # 提取邮件正文 - 从 email_raw 中获取纯正文，避免重复的邮件头信息
        # email_raw.text_content 包含纯文本正文，不包含邮件头
        body_text = email_data.get("email_raw", {}).get("text_content", "")
        
        # 如果 email_raw 中没有 text_content，则尝试从 message 数组中提取
        if not body_text:
            for segment in email_data.get("message", []):
                if segment.get("type") == "text":
                    body_text = segment.get("data", {}).get("text", "")
                    break
        
        # 构建附件信息
        attachments = email_data.get("attachments", [])
        attachment_info = ""
        if attachments:
            attachment_info = f"附件 ({len(attachments)}个):\n"
            for att in attachments:
                filename = att.get("filename", "未知文件")
                size = att.get("size", 0)
                attachment_info += f"  - {filename} ({self._format_size(size)})\n"
        
        # 替换模板变量
        rendered = template
        
        replacements = {
            "{subject}": email_data.get("email_subject", "无主题"),
            "{from}": email_data.get("email_from", "未知发件人"),
            "{to}": email_data.get("email_to", "未知收件人"),
            "{time}": email_data.get("time", ""),
            "{body}": body_text,
            "{rule_name}": rule.get("name", "未命名规则"),
            "{attachments}": attachment_info,
            "{attachment_count}": str(len(attachments))
        }
        
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, str(value))
        
        self.logger.debug(f"模板渲染完成，长度: {len(rendered)} 字符")
        return rendered

    def _format_size(self, size: int) -> str:
        """
        格式化文件大小
        
        :param size: 字节数
        :return: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
        return f"{size:.2f}TB"

    def _format_email_message(self, email_data: Dict[str, Any], rule: Dict[str, Any]) -> str:
        """
        格式化邮件消息（使用模板）
        
        :param email_data: 邮件数据
        :param rule: 转发规则
        :return: 格式化后的消息文本
        """
        self.logger.debug("开始格式化邮件消息")
        
        # 获取规则指定的模板
        template_name = rule.get("template", "default")
        template = self.templates.get(template_name, self.templates.get("default", ""))
        
        if not template:
            self.logger.warning(f"未找到模板 '{template_name}'，使用默认模板")
            template = self.templates.get("default", "")
        
        # 渲染模板
        message_text = self._render_template(template, email_data, rule)
        
        self.logger.debug(f"消息格式化完成，总长度: {len(message_text)} 字符")
        return message_text

    async def _forward_to_target(self, email_data: Dict[str, Any], rule: Dict[str, Any], target: Dict[str, Any]):
        """
        转发邮件到指定目标
        
        :param email_data: 邮件数据
        :param rule: 转发规则
        :param target: 目标配置 {platform, type, id}
        """
        rule_name = rule.get("name", "未命名")
        platform = target.get("platform")
        target_type = target.get("type", "user")
        target_id = target.get("id")
        
        self.logger.debug(f"准备转发邮件到目标: {platform}://{target_type}/{target_id} (规则: '{rule_name}')")
        
        if not platform or not target_id:
            self.logger.warning(f"转发目标配置不完整: {target}")
            return
        
        # 获取适配器实例
        adapter_instance = None
        try:
            adapter_instance = getattr(self.sdk.adapter, platform)
            self.logger.debug(f"成功获取平台适配器: {platform}")
        except AttributeError:
            self.logger.error(f"未找到平台适配器: {platform}")
            return
        
        # 格式化消息
        message_text = self._format_email_message(email_data, rule)
        
        try:
            # 发送消息
            self.logger.debug(f"开始发送消息到 {platform}://{target_type}/{target_id}")
            await adapter_instance.Send.To(target_type, target_id).Text(message_text)
            self.logger.info(f"邮件已转发到 {platform}://{target_type}/{target_id}")
        except Exception as e:
            self.logger.error(f"转发到 {platform}://{target_type}/{target_id} 失败: {e}")

    async def _process_email(self, email_data: Dict[str, Any]):
        """
        处理邮件事件，根据规则转发
        
        :param email_data: 邮件事件数据
        """
        
        if not self.module_config.get("enabled", True):
            self.logger.debug("邮件转发模块未启用，跳过处理")
            return
        # 检查是否为邮件事件
        platform = email_data.get("platform")
        if platform != "email":
            return

        # 从 email_raw 中提取邮件数据
        email_raw = email_data.get("email_raw", {})
        
        # 构建标准化的邮件数据结构
        normalized_email = {
            "email_from": email_raw.get("from", email_data.get("user_id", "未知")),
            "email_to": email_raw.get("to", "未知"),
            "email_subject": email_raw.get("subject", "无主题"),
            "time": email_raw.get("date", ""),
            "message": email_data.get("message", []),
            "attachments": email_data.get("attachments", []),
            "email_raw": email_raw  # 保留原始数据
        }

        email_from = normalized_email.get("email_from", "未知")
        email_subject = normalized_email.get("email_subject", "无主题")
        self.logger.info(f"开始处理邮件 - 发件人: '{email_from}', 主题: '{email_subject}'")
        
        # 遍历所有规则
        matched_rules = 0
        for rule in self.rules:
            try:
                # 检查邮件是否匹配规则
                if self._should_forward_email(normalized_email, rule):
                    matched_rules += 1
                    rule_name = rule.get('name', '未命名')
                    self.logger.info(f"邮件匹配规则 '{rule_name}'，开始转发")
                    
                    # 转发到所有目标
                    targets = rule.get("targets", [])
                    self.logger.debug(f"规则 '{rule_name}' 有 {len(targets)} 个转发目标")
                    for target in targets:
                        await self._forward_to_target(normalized_email, rule, target)
            except Exception as e:
                self.logger.error(f"处理规则 '{rule.get('name', '未命名')}' 时出错: {e}")
        
        if matched_rules == 0:
            self.logger.debug("邮件未匹配任何转发规则，处理完成")
        else:
            self.logger.info(f"邮件处理完成，匹配了 {matched_rules} 条规则")

    async def on_load(self, event):
        """
        模块加载时调用
        
        :param event: 加载事件
        :return: 处理结果
        """
        self.logger.info("开始加载邮件转发模块")
        
        # 注册消息事件处理器（监听邮件）
        @message.on_message()
        async def handle_email_message(event_data):
            await self._process_email(event_data)
        
        self.logger.info("邮件转发模块已加载，消息事件监听器已注册")
        self.logger.debug(f"模块状态: enabled={self.module_config.get('enabled', True)}, 规则数量={len(self.rules)}, 模板数量={len(self.templates)}")

    async def on_unload(self, event):
        """
        模块卸载时调用
        
        :param event: 卸载事件
        :return: 处理结果
        """
        self.logger.info("开始卸载邮件转发模块")
        self.logger.debug("停止监听邮件事件")
        self.logger.info("邮件转发模块已卸载")