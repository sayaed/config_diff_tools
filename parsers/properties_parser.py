# parsers/properties_parser.py (修复版本 - 修正键解析)

import re
import os
import codecs
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from collections import OrderedDict


class PropertiesFormat(Enum):
    """Properties文件格式类型"""
    STANDARD = "standard"
    JAVA = "java"
    ANT = "ant"
    MAVEN = "maven"
    INI = "ini"
    CUSTOM = "custom"


class LineType(Enum):
    """行类型枚举"""
    COMMENT = "comment"
    BLANK = "blank"
    PROPERTY = "property"
    SECTION = "section"
    CONTINUATION = "continuation"
    ESCAPE = "escape"


@dataclass
class PropertyLine:
    """属性行数据结构"""
    line_number: int
    line_type: LineType
    raw_content: str
    key: Optional[str] = None
    value: Optional[str] = None
    comment: Optional[str] = None
    section: Optional[str] = None
    indent: int = 0
    original_key: Optional[str] = None


@dataclass
class PropertiesMetadata:
    """Properties元数据"""
    file_path: Optional[str] = None
    encoding: str = "utf-8"
    format_type: PropertiesFormat = PropertiesFormat.STANDARD
    line_count: int = 0
    property_count: int = 0
    comment_count: int = 0
    blank_count: int = 0
    last_modified: Optional[datetime] = None
    variables: Dict[str, str] = field(default_factory=dict)
    sections: List[str] = field(default_factory=list)


class PropertiesParser:
    """完整的Properties文件解析器"""

    def __init__(self,
                 encoding: str = 'utf-8',
                 preserve_comments: bool = True,
                 preserve_order: bool = True,
                 variable_resolution: bool = True,
                 escape_unicode: bool = True,
                 line_separator: str = '\n'):
        """
        初始化Properties解析器
        """
        self.encoding = encoding
        self.preserve_comments = preserve_comments
        self.preserve_order = preserve_order
        self.variable_resolution = variable_resolution
        self.escape_unicode = escape_unicode
        self.line_separator = line_separator

        # 注释和节的正则
        self.comment_pattern = re.compile(r'^[#!](.*)$')
        self.section_pattern = re.compile(r'^\[(.*?)\]$')
        self.continuation_pattern = re.compile(r'\\$')
        self.variable_pattern = re.compile(r'\$\{([^}]+)\}')
        self.unicode_pattern = re.compile(r'\\u([0-9a-fA-F]{4})')

        # 存储解析结果
        self.lines: List[PropertyLine] = []
        self.properties: Dict[str, str] = OrderedDict() if preserve_order else {}
        self.comments: Dict[int, str] = {}

    def parse(self, content: str, with_metadata: bool = False) -> Union[Dict[str, str], Dict[str, Any]]:
        """
        解析Properties字符串
        """
        self.lines.clear()
        if self.preserve_order:
            self.properties = OrderedDict()
        else:
            self.properties = {}

        self.comments.clear()

        lines = content.splitlines()
        current_section = None
        current_key = None
        current_value_parts = []

        for line_num, raw_line in enumerate(lines, 1):
            # 处理行尾回车符
            line = raw_line.rstrip('\r\n')
            original_line = line

            # 计算缩进
            indent = len(line) - len(line.lstrip())
            line = line.strip()

            # 空行处理
            if not line:
                self._add_blank_line(line_num, original_line, current_section)
                continue

            # 节标题处理（INI格式）
            section_match = self.section_pattern.match(line)
            if section_match:
                current_section = section_match.group(1)
                self._add_section_line(line_num, original_line, current_section, indent)
                continue

            # 注释处理
            comment_match = self.comment_pattern.match(line)
            if comment_match:
                if self.preserve_comments:
                    self._add_comment_line(line_num, original_line, comment_match.group(1),
                                           current_section, indent)
                continue

            # 续行处理
            if self.continuation_pattern.search(line):
                # 移除续行符
                line_part = line[:-1].rstrip()
                current_value_parts.append(line_part)
                if current_key is None:
                    # 尝试从续行中提取键
                    current_key = self._extract_key_from_line(line_part)
                self._add_continuation_line(line_num, original_line, current_key,
                                            line_part, current_section, indent)
                continue

            # 如果是续行的后续部分
            if current_key is not None and current_value_parts:
                current_value_parts.append(line)
                full_value = ''.join(current_value_parts)
                # 处理转义字符
                full_value = self._unescape_string(full_value)

                # 变量替换
                if self.variable_resolution:
                    full_value = self._resolve_variables(full_value, self.properties)

                # 存储属性
                self._set_property(current_key, full_value, line_num, original_line,
                                   current_section, indent)

                # 重置续行状态
                current_key = None
                current_value_parts = []
                continue

            # 标准属性行 - 解析键值对
            key, value = self._parse_key_value(line)

            if key is not None:
                # 处理Unicode转义
                if self.escape_unicode:
                    value = self._unescape_unicode(value)

                # 处理转义字符
                value = self._unescape_string(value)

                # 变量替换
                if self.variable_resolution:
                    value = self._resolve_variables(value, self.properties)

                self._set_property(key, value, line_num, original_line, current_section, indent)
            else:
                # 无法解析的行，作为注释处理
                self._add_comment_line(line_num, original_line, line, current_section, indent)

        if with_metadata:
            return {
                "properties": self.properties,
                "metadata": self._generate_metadata(content)
            }

        return self.properties

    def _parse_key_value(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析键值对，正确处理键中包含的冒号和等号

        策略：找到第一个未被转义的分隔符（=或:）
        """
        if not line:
            return None, None

        # 查找第一个分隔符位置（跳过转义字符）
        separators = ['=', ':']

        # 记录转义状态
        i = 0
        while i < len(line):
            # 检查是否遇到转义字符
            if line[i] == '\\':
                i += 2  # 跳过转义字符和下一个字符
                continue

            # 检查当前字符是否是分隔符
            if line[i] in separators:
                # 找到分隔符
                key = line[:i].rstrip()
                value = line[i + 1:].lstrip()

                # 清理键中的转义字符（但保留原始内容）
                key = self._unescape_key(key)

                return key, value

            i += 1

        # 没有找到分隔符，尝试将整行作为键，值为空
        return line.strip(), ""

    def _unescape_key(self, key: str) -> str:
        """处理键中的转义字符"""
        if not key:
            return key

        # 处理常见的转义序列
        result = []
        i = 0
        while i < len(key):
            if key[i] == '\\' and i + 1 < len(key):
                # 转义字符
                next_char = key[i + 1]
                if next_char in '=:! ':
                    result.append(next_char)
                    i += 2
                else:
                    result.append(key[i])
                    i += 1
            else:
                result.append(key[i])
                i += 1

        return ''.join(result)

    def _extract_key_from_line(self, line: str) -> Optional[str]:
        """从行中提取键"""
        key, _ = self._parse_key_value(line)
        return key

    def _set_property(self, key: str, value: str, line_num: int, raw_content: str,
                      section: Optional[str], indent: int):
        """设置属性值"""
        original_key = key

        # 处理节前缀
        if section:
            full_key = f"{section}.{key}"
        else:
            full_key = key

        # 存储属性行信息
        property_line = PropertyLine(
            line_number=line_num,
            line_type=LineType.PROPERTY,
            raw_content=raw_content,
            key=full_key,
            value=value,
            comment=None,
            section=section,
            indent=indent,
            original_key=original_key
        )
        self.lines.append(property_line)

        # 存储属性值
        self.properties[full_key] = value

    def _add_blank_line(self, line_num: int, raw_content: str, section: Optional[str]):
        """添加空行"""
        blank_line = PropertyLine(
            line_number=line_num,
            line_type=LineType.BLANK,
            raw_content=raw_content,
            section=section,
            indent=0
        )
        self.lines.append(blank_line)

    def _add_comment_line(self, line_num: int, raw_content: str, comment: str,
                          section: Optional[str], indent: int):
        """添加注释行"""
        comment_line = PropertyLine(
            line_number=line_num,
            line_type=LineType.COMMENT,
            raw_content=raw_content,
            comment=comment,
            section=section,
            indent=indent
        )
        self.lines.append(comment_line)
        self.comments[line_num] = comment

    def _add_section_line(self, line_num: int, raw_content: str, section: str, indent: int):
        """添加节标题行"""
        section_line = PropertyLine(
            line_number=line_num,
            line_type=LineType.SECTION,
            raw_content=raw_content,
            section=section,
            indent=indent
        )
        self.lines.append(section_line)

    def _add_continuation_line(self, line_num: int, raw_content: str, key: Optional[str],
                               line_part: str, section: Optional[str], indent: int):
        """添加续行"""
        continuation_line = PropertyLine(
            line_number=line_num,
            line_type=LineType.CONTINUATION,
            raw_content=raw_content,
            key=key,
            value=line_part,
            section=section,
            indent=indent
        )
        self.lines.append(continuation_line)

    def _unescape_string(self, s: str) -> str:
        """处理字符串转义"""
        if not s:
            return s

        # 处理常见转义序列
        escapes = {
            '\\n': '\n',
            '\\r': '\r',
            '\\t': '\t',
            '\\f': '\f',
            '\\b': '\b',
            '\\\\': '\\',
            "\\'": "'",
            '\\"': '"'
        }

        for esc, char in escapes.items():
            s = s.replace(esc, char)

        return s

    def _unescape_unicode(self, s: str) -> str:
        """处理Unicode转义"""

        def replace_unicode(match):
            return chr(int(match.group(1), 16))

        return self.unicode_pattern.sub(replace_unicode, s)

    def _resolve_variables(self, value: str, properties: Dict[str, str]) -> str:
        """
        解析变量引用 ${variable}
        """

        def replace_var(match):
            var_expr = match.group(1)

            # 处理默认值
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
            else:
                var_name = var_expr
                default_value = ''

            # 处理环境变量
            if var_name.startswith('env:'):
                env_name = var_name[4:]
                return os.environ.get(env_name, default_value)

            # 处理系统属性
            if var_name.startswith('sys:'):
                sys_name = var_name[4:]
                return getattr(os, sys_name, default_value)

            # 处理日期变量
            if var_name == 'date':
                return datetime.now().strftime('%Y-%m-%d')
            if var_name == 'time':
                return datetime.now().strftime('%H:%M:%S')
            if var_name == 'timestamp':
                return datetime.now().strftime('%Y%m%d_%H%M%S')

            # 从properties中查找
            if var_name in properties:
                value = properties[var_name]
                # 递归解析嵌套变量
                if self.variable_resolution and '${' in value:
                    return self._resolve_variables(value, properties)
                return value

            # 检查是否已解析过（避免循环引用）
            if hasattr(self, '_resolving') and var_name in self._resolving:
                return default_value or f"${{{var_name}}}"

            if not hasattr(self, '_resolving'):
                self._resolving = set()

            self._resolving.add(var_name)
            try:
                if var_name in properties:
                    result = properties[var_name]
                    if '${' in result:
                        result = self._resolve_variables(result, properties)
                    return result
                return default_value
            finally:
                self._resolving.discard(var_name)

        if not hasattr(self, '_resolving'):
            self._resolving = set()

        try:
            max_iterations = 100  # 防止无限循环
            for _ in range(max_iterations):
                new_value = self.variable_pattern.sub(replace_var, value)
                if new_value == value:
                    break
                value = new_value
            return value
        except RecursionError:
            return value

    def _generate_metadata(self, content: str) -> PropertiesMetadata:
        """生成元数据"""
        property_count = len(self.properties)
        comment_count = sum(1 for line in self.lines if line.line_type == LineType.COMMENT)
        blank_count = sum(1 for line in self.lines if line.line_type == LineType.BLANK)
        sections = list(set(line.section for line in self.lines if line.section))

        return PropertiesMetadata(
            line_count=len(self.lines),
            property_count=property_count,
            comment_count=comment_count,
            blank_count=blank_count,
            sections=sections
        )

    def format(self, data: Union[Dict[str, str], 'PropertiesParser'],
               sort: bool = False,
               comments: Optional[Dict[str, str]] = None,
               include_header: bool = True) -> str:
        """格式化Properties数据"""
        # 获取属性字典
        if isinstance(data, PropertiesParser):
            properties = data.properties
            lines_data = data.lines if hasattr(data, 'lines') else None
        else:
            properties = data
            lines_data = None

        # 如果有保存的行结构且保留顺序，使用原始格式
        if lines_data and self.preserve_order:
            return self._format_from_lines(lines_data)

        # 否则重新生成
        return self._format_from_dict(properties, sort, comments, include_header)

    def _format_from_lines(self, lines: List[PropertyLine]) -> str:
        """从行结构重新生成Properties文件"""
        result_lines = []

        for line in lines:
            if line.line_type == LineType.BLANK:
                result_lines.append('')
            elif line.line_type == LineType.COMMENT:
                result_lines.append(f"#{line.comment}" if not line.comment.startswith(('#', '!'))
                                    else line.comment)
            elif line.line_type == LineType.SECTION:
                result_lines.append(f"[{line.section}]")
            elif line.line_type == LineType.PROPERTY:
                # 转义特殊字符
                key = self._escape_key(line.original_key or line.key)
                value = self._escape_value(line.value)
                result_lines.append(f"{key}={value}")
            elif line.line_type == LineType.CONTINUATION:
                # 续行
                result_lines[-1] = result_lines[-1].rstrip() + '\\'
                result_lines.append(line.value)

        return self.line_separator.join(result_lines)

    def _format_from_dict(self, properties: Dict[str, str], sort: bool = False,
                          comments: Optional[Dict[str, str]] = None,
                          include_header: bool = True) -> str:
        """从字典生成Properties文件"""
        lines = []

        if include_header:
            lines.append("# Generated by PropertiesParser")
            lines.append(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

        items = sorted(properties.items()) if sort else list(properties.items())

        for key, value in items:
            # 添加注释
            if comments and key in comments:
                lines.append(f"# {comments[key]}")

            # 转义键和值
            escaped_key = self._escape_key(key)
            escaped_value = self._escape_value(value)

            lines.append(f"{escaped_key}={escaped_value}")

        return self.line_separator.join(lines)

    def _escape_key(self, key: str) -> str:
        """转义键中的特殊字符"""
        # 如果键包含特殊字符，使用反斜杠转义
        result = []
        for char in key:
            if char in '=:! ':
                result.append('\\')
            result.append(char)
        return ''.join(result)

    def _escape_value(self, value: str) -> str:
        """转义值中的特殊字符"""
        # 转义特殊字符
        value = value.replace('\\', '\\\\')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')
        value = value.replace('\f', '\\f')

        # 处理前导和尾随空格
        if value and (value[0].isspace() or value[-1].isspace()):
            value = value.replace(' ', '\\ ')

        return value

    def load_file(self, file_path: str) -> Dict[str, str]:
        """从文件加载Properties配置"""
        with codecs.open(file_path, 'r', encoding=self.encoding) as f:
            content = f.read()
        return self.parse(content)

    def save_file(self, file_path: str, properties: Dict[str, str],
                  comments: Optional[Dict[str, str]] = None):
        """保存Properties配置到文件"""
        content = self.format(properties, comments=comments)
        with codecs.open(file_path, 'w', encoding=self.encoding) as f:
            f.write(content)

    def merge(self, base: Dict[str, str], override: Dict[str, str]) -> Dict[str, str]:
        """合并两个Properties配置"""
        result = base.copy()

        for key, value in override.items():
            if key in result and self.variable_resolution:
                # 解析变量引用
                result[key] = self._resolve_variables(value, result)
            else:
                result[key] = value

        return result

    def diff(self, props1: Dict[str, str], props2: Dict[str, str]) -> Dict[str, Any]:
        """比对两个Properties配置的差异"""
        all_keys = set(props1.keys()) | set(props2.keys())

        added = {}
        deleted = {}
        modified = {}

        for key in all_keys:
            if key not in props1:
                added[key] = props2[key]
            elif key not in props2:
                deleted[key] = props1[key]
            elif props1[key] != props2[key]:
                modified[key] = {
                    'old': props1[key],
                    'new': props2[key]
                }

        return {
            'added': added,
            'deleted': deleted,
            'modified': modified,
            'total_added': len(added),
            'total_deleted': len(deleted),
            'total_modified': len(modified)
        }

    def validate(self, content: str, required_keys: List[str] = None,
                 key_patterns: Dict[str, str] = None) -> Dict[str, Any]:
        """验证Properties配置"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'parsed_properties': {}
        }

        try:
            properties = self.parse(content)
            result['parsed_properties'] = properties

            # 检查必需键
            if required_keys:
                missing_keys = [key for key in required_keys if key not in properties]
                if missing_keys:
                    result['valid'] = False
                    result['errors'].append(f"缺少必需键: {', '.join(missing_keys)}")

            # 检查键值模式
            if key_patterns:
                for key, pattern in key_patterns.items():
                    if key in properties:
                        if not re.match(pattern, properties[key]):
                            result['valid'] = False
                            result['errors'].append(f"键 '{key}' 的值 '{properties[key]}' 不符合模式 '{pattern}'")

            # 检查循环引用
            if self.variable_resolution:
                for key, value in properties.items():
                    if '${' in value:
                        try:
                            self._resolve_variables(value, properties)
                        except RecursionError:
                            result['valid'] = False
                            result['errors'].append(f"键 '{key}' 中存在循环变量引用")

        except Exception as e:
            result['valid'] = False
            result['errors'].append(str(e))

        return result

    def convert_to_json(self, properties: Dict[str, str]) -> Dict[str, Any]:
        """将Properties转换为嵌套JSON结构"""
        result = {}

        for key, value in properties.items():
            parts = key.split('.')
            current = result

            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    def convert_from_json(self, json_obj: Dict[str, Any], prefix: str = '') -> Dict[str, str]:
        """将嵌套JSON结构转换为Properties格式"""
        properties = {}

        for key, value in json_obj.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                properties.update(self.convert_from_json(value, full_key))
            elif isinstance(value, list):
                properties[full_key] = json.dumps(value, ensure_ascii=False)
            else:
                properties[full_key] = str(value)

        return properties