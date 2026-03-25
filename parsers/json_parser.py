# parsers/json_parser.py
import json
from typing import Any


class JSONParser:
    """JSON解析器"""

    @staticmethod
    def parse(content: str) -> Any:
        """解析JSON字符串"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")

    @staticmethod
    def format(data: Any) -> str:
        """格式化JSON数据"""
        return json.dumps(data, indent=2, ensure_ascii=False)

