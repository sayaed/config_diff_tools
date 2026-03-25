# parsers/xml_parser.py
import xml.etree.ElementTree as ET
from typing import Any, Dict


class XMLParser:
    """XML解析器"""

    @staticmethod
    def parse(content: str) -> Dict:
        """解析XML字符串"""
        try:
            root = ET.fromstring(content)
            return XMLParser._element_to_dict(root)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")

    @staticmethod
    def _element_to_dict(element: ET.Element) -> Dict:
        """将XML元素转换为字典"""
        result = {
            'tag': element.tag,
            'attributes': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'children': []
        }

        for child in element:
            result['children'].append(XMLParser._element_to_dict(child))

        return result

    @staticmethod
    def format(data: Dict) -> str:
        """格式化XML数据（简化实现）"""
        return str(data)  # 实际项目中应实现完整的XML序列化
