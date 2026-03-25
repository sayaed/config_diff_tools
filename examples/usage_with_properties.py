# examples/usage_with_properties.py
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.properties_parser import PropertiesParser
from diff_engine import DiffEngine
from formatters.html_formatter import HTMLFormatter
import json


def example_with_properties():
    """使用properties字段的示例"""
    print("=" * 50)
    print("Properties字段示例")
    print("=" * 50)

    # 准备Properties数据
    props_v1 = {
        'app.name': 'MyApp',
        'app.version': '1.0.0',
        'db.host': 'localhost',
        'db.port': '3306',
        'db.name': 'mydb'
    }

    props_v2 = {
        'app.name': 'MyApp',
        'app.version': '1.1.0',  # 修改
        'db.host': '192.168.1.100',  # 修改
        'db.port': '3306',
        'db.name': 'mydb',
        'db.pool.size': '20',  # 新增
        'cache.enabled': 'true'  # 新增
    }

    # 创建比对引擎
    engine = DiffEngine(ignore_whitespace=True, case_sensitive=False)

    # 准备版本信息
    source_info = {
        "name": "v1.0.0",
        "update_time": "2026-03-23 10:30:00",
        "environment": "production"
    }

    target_info = {
        "name": "v1.1.0",
        "update_time": "2026-03-24 14:20:00",
        "environment": "production"
    }

    # 执行比对
    result = engine.compare_properties(
        props_v1, props_v2,
        source_info, target_info
    )

    # 验证属性存在
    print("\n验证CompareResult属性:")
    print(f"✓ source_properties 存在: {hasattr(result, 'source_properties')}")
    print(f"✓ target_properties 存在: {hasattr(result, 'target_properties')}")

    # 现在可以安全访问
    print(f"\n源配置属性数量: {len(result.source_properties) if result.source_properties else 0}")
    print(f"目标配置属性数量: {len(result.target_properties) if result.target_properties else 0}")
    print(f"差异项数量: {len(result.differences)}")

    # 显示部分属性
    print("\n源配置示例:")
    for key, value in list(result.source_properties.items())[:3]:
        print(f"  {key} = {value}")

    print("\n目标配置示例:")
    for key, value in list(result.target_properties.items())[:3]:
        print(f"  {key} = {value}")

    # 生成HTML报告
    print("\n生成HTML报告...")
    html = HTMLFormatter.format(result)

    # 保存报告
    output_file = 'diff_report_with_properties.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML报告已生成: {output_file}")

    # 输出JSON格式
    print("\nJSON格式结果:")
    json_output = result.to_dict()
    print(f"  source: {json_output['source']['name']}")
    print(f"  target: {json_output['target']['name']}")
    print(f"  config_type: {json_output['config_type']}")
    print(f"  summary: {json_output['summary']}")

    return result


def example_json_with_properties():
    """JSON配置比对示例"""
    print("\n" + "=" * 50)
    print("JSON配置比对示例")
    print("=" * 50)

    # 准备JSON数据
    json_v1 = {
        "app": {
            "name": "MyApp",
            "version": "1.0.0",
            "debug": True
        },
        "database": {
            "host": "localhost",
            "port": 3306,
            "name": "mydb"
        }
    }

    json_v2 = {
        "app": {
            "name": "MyApp",
            "version": "1.1.0",
            "debug": False
        },
        "database": {
            "host": "192.168.1.100",
            "port": 3306,
            "name": "mydb",
            "pool_size": 20
        },
        "cache": {
            "enabled": True,
            "ttl": 3600
        }
    }

    # 创建比对引擎
    engine = DiffEngine(ignore_whitespace=True)

    # 准备版本信息
    source_info = {
        "name": "config_v1.json",
        "update_time": "2026-03-23 10:30:00"
    }

    target_info = {
        "name": "config_v2.json",
        "update_time": "2026-03-24 14:20:00"
    }

    # 执行比对
    result = engine.compare_json(json_v1, json_v2, source_info, target_info)

    print(f"\n源配置属性数量: {len(result.source_properties)}")
    print(f"目标配置属性数量: {len(result.target_properties)}")
    print(f"差异项数量: {len(result.differences)}")

    # 显示展平后的属性
    print("\n展平后的源配置示例:")
    for key, value in list(result.source_properties.items())[:5]:
        print(f"  {key} = {value}")

    # 生成HTML报告
    output_file = 'diff_report_json.html'
    html = HTMLFormatter.format(result)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML报告已生成: {output_file}")

    return result


def example_text_comparison():
    """文本配置比对示例"""
    print("\n" + "=" * 50)
    print("文本配置比对示例")
    print("=" * 50)

    # 准备文本内容
    text_v1 = """server.port=8080
server.host=localhost
app.name=MyApp
app.debug=true
"""

    text_v2 = """server.port=9090
server.host=192.168.1.100
app.name=MyApp
app.debug=false
app.feature.enabled=true
"""

    # 创建比对引擎
    engine = DiffEngine(ignore_whitespace=True)

    # 准备版本信息
    source_info = {
        "name": "config_v1.txt",
        "update_time": "2026-03-23 10:30:00"
    }

    target_info = {
        "name": "config_v2.txt",
        "update_time": "2026-03-24 14:20:00"
    }

    # 执行比对
    result = engine.compare_text(
        text_v1, text_v2,
        source_info, target_info,
        source_properties=text_v1,
        target_properties=text_v2
    )

    print(f"\n源配置类型: {type(result.source_properties)}")
    print(f"目标配置类型: {type(result.target_properties)}")
    print(f"差异项数量: {len(result.differences)}")

    # 生成HTML报告
    output_file = 'diff_report_text.html'
    html = HTMLFormatter.format(result)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML报告已生成: {output_file}")

    return result


if __name__ == '__main__':
    try:
        example_with_properties()
        example_json_with_properties()
        example_text_comparison()
        print("\n" + "=" * 50)
        print("所有示例执行成功！")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()