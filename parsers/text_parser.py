# parsers/text_parser.py
from typing import Any


class TextParser:
    """纯文本解析器"""

    @staticmethod
    def parse(content: str) -> str:
        """解析文本内容"""
        return content

    @staticmethod
    def format(data: str) -> str:
        """格式化文本内容"""
        return data