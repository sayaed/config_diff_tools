# parsers/properties_parser.py
from typing import Dict
import re


class PropertiesParser:
    """Properties文件解析器"""

    @staticmethod
    def parse(content: str) -> Dict[str, str]:
        """解析Properties文件"""
        result = {}
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#') or line.startswith('!'):
                continue

            # 解析键值对
            match = re.match(r'^([^=:]+)[=:](.*)$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                result[key] = value
            else:
                raise ValueError(f"Invalid properties format at line {line_num}: {line}")

        return result

    @staticmethod
    def format(data: Dict[str, str]) -> str:
        """格式化Properties数据"""
        lines = []
        for key, value in data.items():
            lines.append(f"{key}={value}")
        return '\n'.join(lines)
