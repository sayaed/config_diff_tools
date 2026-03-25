# parsers/__init__.py
from .json_parser import JSONParser
from .yaml_parser import YAMLParser
from .xml_parser import XMLParser
from .properties_parser import PropertiesParser
from .text_parser import TextParser


class ParserFactory:
    """解析器工厂"""

    _parsers = {
        'json': JSONParser,
        'yaml': YAMLParser,
        'yml': YAMLParser,
        'xml': XMLParser,
        'properties': PropertiesParser,
        'txt': TextParser,
        'text': TextParser,
    }

    @classmethod
    def get_parser(cls, config_type: str):
        """获取对应类型的解析器"""
        parser_class = cls._parsers.get(config_type.lower())
        if not parser_class:
            raise ValueError(f"Unsupported config type: {config_type}")
        return parser_class()

    @classmethod
    def register_parser(cls, config_type: str, parser_class):
        """注册新的解析器"""
        cls._parsers[config_type.lower()] = parser_class