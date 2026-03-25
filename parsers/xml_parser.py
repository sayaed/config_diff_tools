# parsers/xml_parser.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.parsers import expat
from typing import Any, Dict, List, Union, Optional, Iterator
from dataclasses import dataclass, field
from collections import OrderedDict
import re


@dataclass
class XMLNode:
    """XML节点数据结构"""
    tag: str
    attributes: Dict[str, str] = field(default_factory=dict)
    text: Optional[str] = None
    tail: Optional[str] = None
    children: List['XMLNode'] = field(default_factory=list)
    parent: Optional['XMLNode'] = None

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = {
            "tag": self.tag,
            "attributes": self.attributes
        }

        if self.text and self.text.strip():
            result["text"] = self.text.strip()

        if self.children:
            # 处理重复标签
            children_dict = {}
            for child in self.children:
                child_dict = child.to_dict()
                if child.tag in children_dict:
                    if not isinstance(children_dict[child.tag], list):
                        children_dict[child.tag] = [children_dict[child.tag]]
                    children_dict[child.tag].append(child_dict)
                else:
                    children_dict[child.tag] = child_dict

            result["children"] = children_dict

        return result


class XMLParser:
    """XML解析器 - 支持完整XML特性"""

    def __init__(self, preserve_order: bool = True,
                 strip_namespace: bool = False,
                 handle_cdata: bool = True):
        """
        初始化XML解析器

        Args:
            preserve_order: 是否保留元素顺序
            strip_namespace: 是否移除命名空间前缀
            handle_cdata: 是否处理CDATA
        """
        self.preserve_order = preserve_order
        self.strip_namespace = strip_namespace
        self.handle_cdata = handle_cdata

        # 配置解析器
        self.parser = ET.XMLParser(target=ET.TreeBuilder())

    def parse(self, content: str, as_tree: bool = False) -> Union[Dict, ET.Element]:
        """
        解析XML字符串

        Args:
            content: XML内容字符串
            as_tree: 是否返回ElementTree对象

        Returns:
            解析后的字典或Element对象

        Raises:
            ValueError: XML格式错误时抛出
        """
        try:
            # 预处理CDATA
            if self.handle_cdata:
                content = self._preprocess_cdata(content)

            # 解析XML
            root = ET.fromstring(content, parser=self.parser)

            if as_tree:
                return root

            # 转换为字典格式
            return self._element_to_dict(root)

        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        except Exception as e:
            raise ValueError(f"XML parsing error: {e}")

    def parse_with_position(self, content: str) -> List[Dict]:
        """
        解析XML并保留位置信息（使用expat）

        Args:
            content: XML内容字符串

        Returns:
            包含位置信息的节点列表
        """

        class PositionHandler:
            def __init__(self):
                self.elements = []
                self.stack = []

            def start_element(self, name, attrs):
                pos = self.parser.CurrentPosition()
                element = {
                    "type": "start",
                    "tag": name,
                    "attributes": attrs,
                    "line": pos[0],
                    "column": pos[1],
                    "depth": len(self.stack)
                }
                self.elements.append(element)
                self.stack.append(element)

            def end_element(self, name):
                pos = self.parser.CurrentPosition()
                element = {
                    "type": "end",
                    "tag": name,
                    "line": pos[0],
                    "column": pos[1]
                }
                self.elements.append(element)
                if self.stack:
                    self.stack.pop()

            def char_data(self, data):
                if data.strip():
                    pos = self.parser.CurrentPosition()
                    element = {
                        "type": "text",
                        "text": data.strip(),
                        "line": pos[0],
                        "column": pos[1]
                    }
                    self.elements.append(element)

        handler = PositionHandler()
        self.parser = expat.ParserCreate()
        self.parser.StartElementHandler = handler.start_element
        self.parser.EndElementHandler = handler.end_element
        self.parser.CharacterDataHandler = handler.char_data
        handler.parser = self.parser

        try:
            self.parser.Parse(content, True)
            return handler.elements
        except expat.error as e:
            raise ValueError(f"XML parsing error at line {self.parser.ErrorLineNumber}: {e}")

    def _preprocess_cdata(self, content: str) -> str:
        """预处理CDATA部分"""

        def replace_cdata(match):
            cdata_content = match.group(1)
            # 将CDATA转换为普通文本，保留内容
            return cdata_content

        # 匹配CDATA标签
        cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
        return re.sub(cdata_pattern, replace_cdata, content, flags=re.DOTALL)

    def _element_to_dict(self, element: ET.Element) -> Dict:
        """
        将XML元素转换为字典

        Args:
            element: XML元素对象

        Returns:
            字典表示
        """
        result = {}

        # 处理标签名
        tag = element.tag
        if self.strip_namespace:
            tag = tag.split('}')[-1] if '}' in tag else tag

        result["tag"] = tag

        # 处理属性
        if element.attrib:
            attrs = {}
            for key, value in element.attrib.items():
                attr_key = key.split('}')[-1] if '}' in key else key
                attrs[attr_key] = value
            result["attributes"] = attrs

        # 处理文本
        if element.text and element.text.strip():
            result["text"] = element.text.strip()

        # 处理子元素
        children = list(element)
        if children:
            if self.preserve_order:
                # 保留顺序的列表形式
                children_list = []
                for child in children:
                    children_list.append(self._element_to_dict(child))
                result["children"] = children_list
            else:
                # 聚合重复标签的字典形式
                children_dict = {}
                for child in children:
                    child_dict = self._element_to_dict(child)
                    child_tag = child_dict["tag"]

                    if child_tag in children_dict:
                        if not isinstance(children_dict[child_tag], list):
                            children_dict[child_tag] = [children_dict[child_tag]]
                        children_dict[child_tag].append(child_dict)
                    else:
                        children_dict[child_tag] = child_dict

                result["children"] = children_dict

        # 处理尾部文本
        if element.tail and element.tail.strip():
            result["tail"] = element.tail.strip()

        return result

    def format(self, data: Union[Dict, ET.Element], pretty: bool = True,
               encoding: str = 'utf-8') -> str:
        """
        格式化数据为XML字符串

        Args:
            data: 字典或Element对象
            pretty: 是否美化输出
            encoding: 编码格式

        Returns:
            格式化的XML字符串
        """
        try:
            if isinstance(data, dict):
                root = self._dict_to_element(data)
            elif isinstance(data, ET.Element):
                root = data
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            # 转换为字符串
            if pretty:
                rough_string = ET.tostring(root, encoding=encoding)
                reparsed = minidom.parseString(rough_string)
                return reparsed.toprettyxml(indent="  ", encoding=encoding).decode(encoding)
            else:
                return ET.tostring(root, encoding=encoding).decode(encoding)

        except Exception as e:
            raise ValueError(f"XML formatting error: {e}")

    def _dict_to_element(self, data: Dict) -> ET.Element:
        """
        将字典转换为XML元素

        Args:
            data: 字典数据

        Returns:
            XML元素对象
        """
        if "tag" not in data:
            raise ValueError("Dictionary must contain 'tag' field")

        tag = data["tag"]
        element = ET.Element(tag)

        # 设置属性
        if "attributes" in data and isinstance(data["attributes"], dict):
            for key, value in data["attributes"].items():
                element.set(key, str(value))

        # 设置文本
        if "text" in data:
            element.text = data["text"]

        # 处理子元素
        if "children" in data:
            children = data["children"]

            if isinstance(children, list):
                # 列表形式的子元素
                for child_data in children:
                    if isinstance(child_data, dict):
                        child_element = self._dict_to_element(child_data)
                        element.append(child_element)
            elif isinstance(children, dict):
                # 字典形式的子元素
                for child_tag, child_data in children.items():
                    if isinstance(child_data, list):
                        for child_item in child_data:
                            if isinstance(child_item, dict):
                                child_item["tag"] = child_tag
                                child_element = self._dict_to_element(child_item)
                                element.append(child_element)
                    elif isinstance(child_data, dict):
                        child_data["tag"] = child_tag
                        child_element = self._dict_to_element(child_data)
                        element.append(child_element)

        # 设置尾部文本
        if "tail" in data:
            element.tail = data["tail"]

        return element

    def xpath_query(self, content: str, query: str) -> List[Any]:
        """
        执行XPath查询

        Args:
            content: XML内容
            query: XPath表达式

        Returns:
            查询结果列表
        """
        try:
            root = ET.fromstring(content)
            return root.findall(query)
        except ET.ParseError as e:
            raise ValueError(f"XML parsing error: {e}")
        except Exception as e:
            raise ValueError(f"XPath query error: {e}")

    def validate(self, content: str, xsd_schema: str = None) -> Dict[str, Any]:
        """
        验证XML内容

        Args:
            content: XML内容
            xsd_schema: XSD Schema文件路径或内容

        Returns:
            验证结果字典
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # 基本格式验证
            root = ET.fromstring(content)

            # 检查是否有重复属性警告
            for element in root.iter():
                if len(element.attrib) != len(set(element.attrib.keys())):
                    result["warnings"].append(f"元素 {element.tag} 包含重复属性")

            # XSD验证（如果需要）
            if xsd_schema:
                try:
                    from lxml import etree
                    xml_doc = etree.fromstring(content.encode('utf-8'))

                    if xsd_schema.startswith('<'):
                        xsd_doc = etree.fromstring(xsd_schema.encode('utf-8'))
                    else:
                        xsd_doc = etree.parse(xsd_schema)

                    schema = etree.XMLSchema(xsd_doc)
                    if not schema.validate(xml_doc):
                        result["valid"] = False
                        for error in schema.error_log:
                            result["errors"].append(str(error))

                except ImportError:
                    result["warnings"].append("lxml未安装，无法进行XSD验证")
                except Exception as e:
                    result["errors"].append(f"XSD验证错误: {e}")

        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append(f"XML格式错误: {e}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"验证错误: {e}")

        return result


class XMLNamespaceParser:
    """支持命名空间的XML解析器"""

    def __init__(self, namespaces: Dict[str, str] = None):
        """
        初始化命名空间解析器

        Args:
            namespaces: 命名空间映射字典
        """
        self.namespaces = namespaces or {}

    def parse(self, content: str, use_namespaces: bool = True) -> Dict:
        """
        解析XML并处理命名空间

        Args:
            content: XML内容
            use_namespaces: 是否使用命名空间

        Returns:
            带命名空间的解析结果
        """
        try:
            # 注册命名空间
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)

            root = ET.fromstring(content)

            if use_namespaces:
                return self._element_with_namespace(root)
            else:
                parser = XMLParser(strip_namespace=True)
                return parser._element_to_dict(root)

        except ET.ParseError as e:
            raise ValueError(f"XML parsing error: {e}")

    def _element_with_namespace(self, element: ET.Element) -> Dict:
        """处理带命名空间的元素"""
        result = {}

        # 处理命名空间前缀
        tag = element.tag
        ns_match = re.match(r'{(.*?)}', tag)
        if ns_match:
            namespace = ns_match.group(1)
            local_tag = tag[ns_match.end():]
            result["namespace"] = namespace
            result["tag"] = local_tag

            # 查找命名空间前缀
            for prefix, uri in self.namespaces.items():
                if uri == namespace:
                    result["prefix"] = prefix
                    break
        else:
            result["tag"] = tag

        # 处理属性
        if element.attrib:
            attrs = {}
            for key, value in element.attrib.items():
                ns_match = re.match(r'{(.*?)}', key)
                if ns_match:
                    namespace = ns_match.group(1)
                    local_key = key[ns_match.end():]
                    attrs[f"{{{namespace}}}{local_key}"] = value
                else:
                    attrs[key] = value
            result["attributes"] = attrs

        # 处理文本和子元素
        if element.text and element.text.strip():
            result["text"] = element.text.strip()

        children = list(element)
        if children:
            result["children"] = [self._element_with_namespace(child) for child in children]

        return result

    def format(self, data: Dict, with_declaration: bool = True) -> str:
        """
        格式化为带命名空间的XML

        Args:
            data: 字典数据
            with_declaration: 是否包含XML声明

        Returns:
            XML字符串
        """
        # 创建根元素
        root_tag = data.get("tag", "root")
        if "namespace" in data and "prefix" in data:
            root_tag = f"{{{data['namespace']}}}{root_tag}"

        root = ET.Element(root_tag)

        # 添加命名空间声明
        for prefix, uri in self.namespaces.items():
            if prefix:
                root.set(f"xmlns:{prefix}", uri)
            else:
                root.set("xmlns", uri)

        # 构建XML树
        self._build_xml_tree(root, data)

        # 转换为字符串
        xml_string = ET.tostring(root, encoding='unicode')

        if with_declaration:
            return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'

        return xml_string

    def _build_xml_tree(self, parent: ET.Element, data: Dict):
        """构建XML树"""
        # 添加文本
        if "text" in data:
            parent.text = data["text"]

        # 添加属性
        if "attributes" in data:
            for key, value in data["attributes"].items():
                parent.set(key, str(value))

        # 添加子元素
        if "children" in data:
            children = data["children"]
            if isinstance(children, list):
                for child_data in children:
                    child_tag = child_data.get("tag", "element")
                    if "namespace" in child_data and "prefix" in child_data:
                        child_tag = f"{{{child_data['namespace']}}}{child_tag}"

                    child = ET.SubElement(parent, child_tag)
                    self._build_xml_tree(child, child_data)
            elif isinstance(children, dict):
                for child_tag, child_data in children.items():
                    if isinstance(child_data, list):
                        for child_item in child_data:
                            child = ET.SubElement(parent, child_tag)
                            self._build_xml_tree(child, child_item)
                    else:
                        child = ET.SubElement(parent, child_tag)
                        self._build_xml_tree(child, child_data)

        # 添加尾部文本
        if "tail" in data:
            parent.tail = data["tail"]