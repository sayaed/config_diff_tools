# formatters/json_formatter.py
import json
from typing import List, Dict
from diff_engine import CompareResult


class JSONFormatter:
    """JSON格式输出器"""

    @staticmethod
    def format(result: CompareResult) -> str:
        """格式化比对结果为JSON字符串"""
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False, default=str)


