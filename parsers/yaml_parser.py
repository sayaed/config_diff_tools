# parsers/yaml_parser.py
import yaml
from typing import Any


class YAMLParser:
    """YAML解析器"""

    @staticmethod
    def parse(content: str) -> Any:
        """解析YAML字符串"""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML content: {e}")

    @staticmethod
    def format(data: Any) -> str:
        """格式化YAML数据"""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

