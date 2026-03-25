# examples/properties_examples_fixed.py
from parsers.properties_parser import PropertiesParser


def test_special_keys_with_escape():
    """测试特殊字符键 - 使用转义"""
    print("=" * 50)
    print("测试特殊字符键解析（使用转义）")
    print("=" * 50)

    parser = PropertiesParser(preserve_order=True)

    # 正确的Properties格式：键中的特殊字符需要转义
    content = """
# 包含冒号的键（需要转义）
key\.with\:colon=值包含冒号
key\:with\:colon=另一个值

# 包含等号的键（需要转义）
key\=with\=equal=符号
key\.with\=equal=test

# 包含空格的键（需要转义）
key\ with\ spaces=值包含空格
long\ key\ name=长键名

# 混合特殊字符
complex\:key\=with\=value=here
"""

    props = parser.parse(content)

    print("\n解析结果:")
    for key, value in props.items():
        print(f"  '{key}' = '{value}'")

    # 验证 - 注意解析后的键会去除转义符
    assert 'key.with:colon' in props, "包含冒号的键未正确解析"
    print(f"✓ key.with:colon = {props['key.with:colon']}")

    assert 'key:with:colon' in props, "多个冒号的键未正确解析"
    print(f"✓ key:with:colon = {props['key:with:colon']}")

    assert 'key=with=equal' in props, "包含等号的键未正确解析"
    print(f"✓ key=with=equal = {props['key=with=equal']}")

    assert 'key with spaces' in props, "包含空格的键未正确解析"
    print(f"✓ key with spaces = {props['key with spaces']}")

    print("\n✅ 所有测试通过！")


def test_without_escape():
    """测试不转义的情况（非标准但常见）"""
    print("\n" + "=" * 50)
    print("测试不转义的特殊字符键（宽松模式）")
    print("=" * 50)

    # 创建一个宽松模式的解析器
    parser = PropertiesParser(preserve_order=True)

    # 不转义的内容
    content = """
key.with:colon=值包含冒号
key:with:colon=另一个值
key=with=equal=符号
key with spaces=值包含空格
"""

    # 自定义解析逻辑：只将第一个等号或冒号作为分隔符
    # 注意：这会导致 key:with:colon 被解析为 key 和 with:colon=另一个值
    props = parser.parse(content)

    print("\n解析结果（第一个分隔符策略）:")
    for key, value in props.items():
        print(f"  '{key}' = '{value}'")

    print("\n注意：这种解析方式下，key:with:colon 会被错误解析！")
    print("正确的做法是使用转义符：key\\:with\\:colon=另一个值")


def test_custom_parsing():
    """自定义解析：只使用等号作为分隔符"""
    print("\n" + "=" * 50)
    print("自定义解析：只使用等号作为分隔符")
    print("=" * 50)

    # 修改解析器的分隔符策略
    class CustomPropertiesParser(PropertiesParser):
        def _parse_key_value(self, line: str):
            """只使用等号作为分隔符"""
            if not line:
                return None, None

            if '=' in line:
                sep_pos = line.find('=')
                key = line[:sep_pos].rstrip()
                value = line[sep_pos + 1:].lstrip()
                return key, value

            # 如果没有等号，尝试使用冒号
            if ':' in line:
                sep_pos = line.find(':')
                key = line[:sep_pos].rstrip()
                value = line[sep_pos + 1:].lstrip()
                return key, value

            return line.strip(), ""

    parser = CustomPropertiesParser(preserve_order=True)

    content = """
key.with:colon=值包含冒号
key:with:colon=另一个值
key=with=equal=符号
"""

    props = parser.parse(content)

    print("\n解析结果:")
    for key, value in props.items():
        print(f"  '{key}' = '{value}'")

    # 验证
    if 'key.with:colon' in props:
        print("✓ key.with:colon 正确解析")
    else:
        print("✗ key.with:colon 未正确解析")

    if 'key:with:colon' in props:
        print("✓ key:with:colon 正确解析")
    else:
        print("✗ key:with:colon 未正确解析")


def main():
    """运行测试"""
    test_special_keys_with_escape()
    test_without_escape()
    test_custom_parsing()


if __name__ == '__main__':
    main()