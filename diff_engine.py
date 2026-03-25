# diff_engine.py
import json
import difflib
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class DiffType(Enum):
    """差异类型枚举"""
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffResult:
    """差异结果数据类"""
    path: str
    type: DiffType
    source_value: Optional[Any] = None
    target_value: Optional[Any] = None

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "path": self.path,
            "type": self.type.value,
            "source_value": self.source_value,
            "target_value": self.target_value
        }


@dataclass
class CompareResult:
    """比对结果汇总"""
    source_info: Dict[str, Any]
    target_info: Dict[str, Any]
    differences: List[DiffResult]
    summary: Dict[str, int]
    config_type: str
    source_properties: Optional[Dict[str, Any]] = None  # 新增：源配置属性
    target_properties: Optional[Dict[str, Any]] = None  # 新增：目标配置属性

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = {
            "source": self.source_info,
            "target": self.target_info,
            "differences": [d.to_dict() for d in self.differences],
            "summary": self.summary,
            "config_type": self.config_type,
            "timestamp": datetime.now().isoformat()
        }

        # 添加properties字段（如果存在）
        if self.source_properties is not None:
            result["source_properties"] = self.source_properties
        if self.target_properties is not None:
            result["target_properties"] = self.target_properties

        return result


class DiffEngine:
    """配置比对引擎"""

    def __init__(self, ignore_whitespace: bool = True, case_sensitive: bool = True):
        """
        初始化比对引擎

        Args:
            ignore_whitespace: 是否忽略空白字符
            case_sensitive: 是否大小写敏感
        """
        self.ignore_whitespace = ignore_whitespace
        self.case_sensitive = case_sensitive

    def compare_text(self, source: str, target: str, source_info: Dict = None,
                     target_info: Dict = None, source_properties: Any = None,
                     target_properties: Any = None) -> CompareResult:
        """
        比对纯文本内容

        Args:
            source: 源文本
            target: 目标文本
            source_info: 源版本信息
            target_info: 目标版本信息
            source_properties: 源配置属性（用于显示）
            target_properties: 目标配置属性（用于显示）

        Returns:
            CompareResult: 比对结果
        """
        # 预处理文本
        if self.ignore_whitespace:
            source_lines = [line.rstrip() for line in source.splitlines()]
            target_lines = [line.rstrip() for line in target.splitlines()]
        else:
            source_lines = source.splitlines()
            target_lines = target.splitlines()

        # 使用difflib进行行比对
        differ = difflib.SequenceMatcher(None, source_lines, target_lines)
        differences = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'replace':
                for idx in range(max(i2 - i1, j2 - j1)):
                    if idx < (i2 - i1):
                        source_line = source_lines[i1 + idx]
                    else:
                        source_line = None
                    if idx < (j2 - j1):
                        target_line = target_lines[j1 + idx]
                    else:
                        target_line = None

                    if source_line and target_line:
                        # 进一步检查是否为修改（逐字符比对）
                        if source_line != target_line:
                            differences.append(DiffResult(
                                path=f"line_{i1 + idx + 1}",
                                type=DiffType.MODIFIED,
                                source_value=source_line,
                                target_value=target_line
                            ))
                    elif source_line and not target_line:
                        differences.append(DiffResult(
                            path=f"line_{i1 + idx + 1}",
                            type=DiffType.DELETED,
                            source_value=source_line,
                            target_value=None
                        ))
                    elif not source_line and target_line:
                        differences.append(DiffResult(
                            path=f"line_{j1 + idx + 1}",
                            type=DiffType.ADDED,
                            source_value=None,
                            target_value=target_line
                        ))
            elif tag == 'delete':
                for idx in range(i1, i2):
                    differences.append(DiffResult(
                        path=f"line_{idx + 1}",
                        type=DiffType.DELETED,
                        source_value=source_lines[idx],
                        target_value=None
                    ))
            elif tag == 'insert':
                for idx in range(j1, j2):
                    differences.append(DiffResult(
                        path=f"line_{idx + 1}",
                        type=DiffType.ADDED,
                        source_value=None,
                        target_value=target_lines[idx]
                    ))

        return CompareResult(
            source_info=source_info or {"name": "source"},
            target_info=target_info or {"name": "target"},
            differences=differences,
            summary=self._calculate_summary(differences),
            config_type="text",
            source_properties=source_properties or source,  # 添加源配置
            target_properties=target_properties or target  # 添加目标配置
        )

    def compare_json(self, source: Dict, target: Dict, source_info: Dict = None,
                     target_info: Dict = None, path: str = "") -> CompareResult:
        """
        比对JSON结构

        Args:
            source: 源JSON对象
            target: 目标JSON对象
            source_info: 源版本信息
            target_info: 目标版本信息
            path: 当前路径

        Returns:
            CompareResult: 比对结果
        """
        differences = []
        self._compare_dict(source, target, differences, path)

        # 展平JSON为点号路径格式
        source_flat = self._flatten_dict(source)
        target_flat = self._flatten_dict(target)

        return CompareResult(
            source_info=source_info or {"name": "source"},
            target_info=target_info or {"name": "target"},
            differences=differences,
            summary=self._calculate_summary(differences),
            config_type="json",
            source_properties=source_flat,  # 添加源配置（展平）
            target_properties=target_flat  # 添加目标配置（展平）
        )

    def compare_properties(self, source: Dict[str, str], target: Dict[str, str],
                           source_info: Dict = None, target_info: Dict = None) -> CompareResult:
        """
        比对Properties配置

        Args:
            source: 源Properties字典
            target: 目标Properties字典
            source_info: 源版本信息
            target_info: 目标版本信息

        Returns:
            CompareResult: 比对结果
        """
        differences = []
        all_keys = set(source.keys()) | set(target.keys())

        for key in all_keys:
            if key not in source:
                differences.append(DiffResult(
                    path=key,
                    type=DiffType.ADDED,
                    source_value=None,
                    target_value=target[key]
                ))
            elif key not in target:
                differences.append(DiffResult(
                    path=key,
                    type=DiffType.DELETED,
                    source_value=source[key],
                    target_value=None
                ))
            elif source[key] != target[key]:
                # 处理大小写敏感
                if not self.case_sensitive:
                    if source[key].lower() != target[key].lower():
                        differences.append(DiffResult(
                            path=key,
                            type=DiffType.MODIFIED,
                            source_value=source[key],
                            target_value=target[key]
                        ))
                else:
                    differences.append(DiffResult(
                        path=key,
                        type=DiffType.MODIFIED,
                        source_value=source[key],
                        target_value=target[key]
                    ))

        return CompareResult(
            source_info=source_info or {"name": "source"},
            target_info=target_info or {"name": "target"},
            differences=differences,
            summary=self._calculate_summary(differences),
            config_type="properties",
            source_properties=source,  # 添加源配置
            target_properties=target  # 添加目标配置
        )

    def _compare_dict(self, source: Dict, target: Dict, differences: List[DiffResult],
                      path: str = ""):
        """递归比对字典"""
        all_keys = set(source.keys()) | set(target.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            source_value = source.get(key)
            target_value = target.get(key)

            if key not in source:
                differences.append(DiffResult(
                    path=current_path,
                    type=DiffType.ADDED,
                    source_value=None,
                    target_value=target_value
                ))
            elif key not in target:
                differences.append(DiffResult(
                    path=current_path,
                    type=DiffType.DELETED,
                    source_value=source_value,
                    target_value=None
                ))
            elif isinstance(source_value, dict) and isinstance(target_value, dict):
                self._compare_dict(source_value, target_value, differences, current_path)
            elif isinstance(source_value, list) and isinstance(target_value, list):
                self._compare_list(source_value, target_value, differences, current_path)
            elif source_value != target_value:
                # 处理值比较时的选项
                if not self.case_sensitive and isinstance(source_value, str) and isinstance(target_value, str):
                    if source_value.lower() != target_value.lower():
                        differences.append(DiffResult(
                            path=current_path,
                            type=DiffType.MODIFIED,
                            source_value=source_value,
                            target_value=target_value
                        ))
                elif source_value != target_value:
                    differences.append(DiffResult(
                        path=current_path,
                        type=DiffType.MODIFIED,
                        source_value=source_value,
                        target_value=target_value
                    ))

    def _compare_list(self, source: List, target: List, differences: List[DiffResult],
                      path: str):
        """比对列表"""
        # 简单的列表比对（可扩展为更复杂的算法）
        max_len = max(len(source), len(target))

        for i in range(max_len):
            current_path = f"{path}[{i}]"
            source_value = source[i] if i < len(source) else None
            target_value = target[i] if i < len(target) else None

            if source_value is None:
                differences.append(DiffResult(
                    path=current_path,
                    type=DiffType.ADDED,
                    source_value=None,
                    target_value=target_value
                ))
            elif target_value is None:
                differences.append(DiffResult(
                    path=current_path,
                    type=DiffType.DELETED,
                    source_value=source_value,
                    target_value=None
                ))
            elif isinstance(source_value, dict) and isinstance(target_value, dict):
                self._compare_dict(source_value, target_value, differences, current_path)
            elif isinstance(source_value, list) and isinstance(target_value, list):
                self._compare_list(source_value, target_value, differences, current_path)
            elif source_value != target_value:
                differences.append(DiffResult(
                    path=current_path,
                    type=DiffType.MODIFIED,
                    source_value=source_value,
                    target_value=target_value
                ))

    def _flatten_dict(self, data: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        展平嵌套字典

        Args:
            data: 嵌套字典
            parent_key: 父键
            sep: 分隔符

        Returns:
            展平后的字典
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep=sep).items())
            elif isinstance(value, list):
                # 对于列表，转换为字符串
                items.append((new_key, json.dumps(value, ensure_ascii=False)))
            else:
                items.append((new_key, str(value) if value is not None else ''))
        return dict(items)

    def _calculate_summary(self, differences: List[DiffResult]) -> Dict[str, int]:
        """计算差异统计"""
        summary = {
            "added": 0,
            "deleted": 0,
            "modified": 0
        }

        for diff in differences:
            if diff.type == DiffType.ADDED:
                summary["added"] += 1
            elif diff.type == DiffType.DELETED:
                summary["deleted"] += 1
            elif diff.type == DiffType.MODIFIED:
                summary["modified"] += 1

        return summary