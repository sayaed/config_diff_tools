# parsers/yaml_parser.py
import yaml
from typing import Any, Dict, List, Union, Optional
from dataclasses import dataclass
from enum import Enum


class YAMLStyle(Enum):
    """YAML样式类型"""
    BLOCK = "block"  # 块样式
    FLOW = "flow"  # 流样式
    DEFAULT = "default"


@dataclass
class YAMLNode:
    """YAML节点信息（用于保留位置信息）"""
    value: Any
    line: Optional[int] = None
    column: Optional[int] = None
    style: Optional[str] = None
    anchor: Optional[str] = None
    tag: Optional[str] = None


class YAMLParser:
    """YAML解析器 - 支持完整YAML 1.2特性"""

    def __init__(self, preserve_order: bool = True,
                 safe_load: bool = True,
                 allow_duplicate_keys: bool = False):
        """
        初始化YAML解析器

        Args:
            preserve_order: 是否保留键的顺序（Python 3.7+默认保留）
            safe_load: 是否使用安全加载模式
            allow_duplicate_keys: 是否允许重复键
        """
        self.preserve_order = preserve_order
        self.safe_load = safe_load
        self.allow_duplicate_keys = allow_duplicate_keys

        # 配置PyYAML加载器
        if safe_load:
            self.loader = yaml.SafeLoader
        else:
            self.loader = yaml.Loader

        # 自定义构造器以保留顺序
        if preserve_order:
            self._add_preserve_order_constructor()

    def _add_preserve_order_constructor(self):
        """添加保留顺序的构造器"""

        def construct_mapping(loader, node):
            """构造保留顺序的映射"""
            loader.flatten_mapping(node)
            mapping = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=False)
                value = loader.construct_object(value_node, deep=False)
                mapping[key] = value
            return mapping

        # 替换默认的映射构造器
        self.loader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping
        )

    def parse(self, content: str, with_metadata: bool = False) -> Union[Any, Dict[str, Any]]:
        """
        解析YAML字符串

        Args:
            content: YAML内容字符串
            with_metadata: 是否返回带元数据的结果

        Returns:
            解析后的Python对象，或包含元数据的字典

        Raises:
            ValueError: YAML格式错误时抛出
        """
        try:
            if with_metadata:
                return self._parse_with_metadata(content)
            else:
                return yaml.load(content, Loader=self.loader)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML content: {e}")
        except Exception as e:
            raise ValueError(f"YAML parsing error: {e}")

    def _parse_with_metadata(self, content: str) -> Dict[str, Any]:
        """
        解析YAML并保留元数据（行号、列号等）

        Args:
            content: YAML内容字符串

        Returns:
            包含数据和元数据的字典
        """
        # 使用Composer获取事件流
        from yaml.composer import Composer
        from yaml.parser import Parser
        from yaml.reader import Reader
        from yaml.scanner import Scanner
        from yaml.resolver import Resolver

        class CustomLoader(yaml.Loader):
            pass

        loader = CustomLoader(content)

        # 构建节点树
        nodes = []
        try:
            while loader.check_node():
                node = loader.get_node()
                if node:
                    nodes.append(self._process_node(node))
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}")

        result = {
            "data": nodes[0] if nodes else None,
            "metadata": {
                "nodes": nodes,
                "raw_content": content
            }
        }

        return result

    def _process_node(self, node):
        """处理YAML节点"""
        if isinstance(node, yaml.nodes.ScalarNode):
            return {
                "type": "scalar",
                "value": node.value,
                "tag": node.tag,
                "style": node.style,
                "line": node.start_mark.line + 1 if node.start_mark else None,
                "column": node.start_mark.column + 1 if node.start_mark else None
            }
        elif isinstance(node, yaml.nodes.SequenceNode):
            return {
                "type": "sequence",
                "value": [self._process_node(item) for item in node.value],
                "tag": node.tag,
                "style": node.style,
                "line": node.start_mark.line + 1 if node.start_mark else None,
                "column": node.start_mark.column + 1 if node.start_mark else None
            }
        elif isinstance(node, yaml.nodes.MappingNode):
            result = {
                "type": "mapping",
                "value": [],
                "tag": node.tag,
                "style": node.style,
                "line": node.start_mark.line + 1 if node.start_mark else None,
                "column": node.start_mark.column + 1 if node.start_mark else None
            }
            for key_node, value_node in node.value:
                result["value"].append({
                    "key": self._process_node(key_node),
                    "value": self._process_node(value_node)
                })
            return result

    def format(self, data: Any, style: YAMLStyle = YAMLStyle.DEFAULT,
               indent: int = 2, width: int = 80) -> str:
        """
        格式化Python对象为YAML字符串

        Args:
            data: 要格式化的数据
            style: YAML样式（block/flow/default）
            indent: 缩进空格数
            width: 行宽限制

        Returns:
            格式化后的YAML字符串
        """
        try:
            # 配置dump参数
            dump_kwargs = {
                'indent': indent,
                'width': width,
                'allow_unicode': True,
                'sort_keys': False,  # 保留顺序
                'default_flow_style': style == YAMLStyle.FLOW
            }

            # 处理特殊样式
            if style == YAMLStyle.BLOCK:
                dump_kwargs['default_flow_style'] = False

            return yaml.dump(data, **dump_kwargs)
        except Exception as e:
            raise ValueError(f"YAML formatting error: {e}")

    def merge(self, base: Dict, updates: Dict, deep: bool = True) -> Dict:
        """
        合并两个YAML配置

        Args:
            base: 基础配置
            updates: 更新配置
            deep: 是否深度合并

        Returns:
            合并后的配置
        """
        if not deep:
            return {**base, **updates}

        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge(result[key], value, deep)
            else:
                result[key] = value

        return result

    def validate(self, content: str, schema: Dict = None) -> Dict[str, Any]:
        """
        验证YAML内容

        Args:
            content: YAML内容
            schema: 可选的JSON Schema验证规则

        Returns:
            验证结果字典
        """
        try:
            data = self.parse(content)
            result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }

            # 基本语法验证
            if data is None:
                result["warnings"].append("YAML内容为空")

            # Schema验证
            if schema:
                schema_errors = self._validate_schema(data, schema)
                if schema_errors:
                    result["valid"] = False
                    result["errors"].extend(schema_errors)

            return result

        except ValueError as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }

    def _validate_schema(self, data: Any, schema: Dict, path: str = "") -> List[str]:
        """根据Schema验证数据"""
        errors = []

        if not schema:
            return errors

        # 简化版Schema验证
        if "type" in schema:
            expected_type = schema["type"]
            actual_type = type(data).__name__

            if expected_type == "object" and not isinstance(data, dict):
                errors.append(f"{path}: 期望对象类型，实际为{actual_type}")
            elif expected_type == "array" and not isinstance(data, list):
                errors.append(f"{path}: 期望数组类型，实际为{actual_type}")
            elif expected_type == "string" and not isinstance(data, str):
                errors.append(f"{path}: 期望字符串类型，实际为{actual_type}")
            elif expected_type == "number" and not isinstance(data, (int, float)):
                errors.append(f"{path}: 期望数字类型，实际为{actual_type}")
            elif expected_type == "boolean" and not isinstance(data, bool):
                errors.append(f"{path}: 期望布尔类型，实际为{actual_type}")

        # 必填字段验证
        if "required" in schema and isinstance(data, dict):
            for required_field in schema["required"]:
                if required_field not in data:
                    errors.append(f"{path}.{required_field}: 缺少必填字段")

        # 嵌套验证
        if "properties" in schema and isinstance(data, dict):
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    new_path = f"{path}.{prop}" if path else prop
                    errors.extend(self._validate_schema(data[prop], prop_schema, new_path))

        return errors


class YAMLMultiDocumentParser:
    """多文档YAML解析器（支持---分隔的多个文档）"""

    def __init__(self, parser: YAMLParser = None):
        self.parser = parser or YAMLParser()

    def parse_all(self, content: str) -> List[Any]:
        """
        解析YAML字符串中的所有文档

        Args:
            content: YAML内容字符串（可能包含多个文档）

        Returns:
            解析后的文档列表
        """
        documents = []

        try:
            for doc in yaml.load_all(content, Loader=self.parser.loader):
                documents.append(doc)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML multi-document parsing error: {e}")

        return documents

    def format_all(self, documents: List[Any], **kwargs) -> str:
        """
        格式化多个文档为YAML字符串

        Args:
            documents: 文档列表
            **kwargs: 传递给yaml.dump的参数

        Returns:
            格式化的YAML字符串（文档之间用---分隔）
        """
        parts = []
        for doc in documents:
            if doc is not None:
                parts.append(yaml.dump(doc, **kwargs))
            else:
                parts.append("")

        return "---\n".join(parts)