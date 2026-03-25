# examples/example_usage.py
from main import ConfigDiffTool
from parsers import ParserFactory
from formatters.html_formatter import HTMLFormatter
import json


def example_compare_json_files():
    """示例：比对两个JSON配置文件"""
    tool = ConfigDiffTool(ignore_whitespace=True, case_sensitive=False)

    # 准备示例数据
    config_v1 = {
        "app": {
            "name": "MyApp",
            "version": "1.0.0",
            "port": 8080
        },
        "database": {
            "host": "localhost",
            "port": 3306,
            "name": "mydb"
        }
    }

    config_v2 = {
        "app": {
            "name": "MyApp",
            "version": "1.1.0",  # 修改
            "port": 9090  # 修改
        },
        "database": {
            "host": "192.168.1.100",  # 修改
            "port": 3306,
            "name": "mydb",
            "pool_size": 20  # 新增
        },
        "cache": {  # 新增
            "enabled": True,
            "ttl": 3600
        }
    }

    # 保存临时文件（实际使用时从文件读取）
    with open('config_v1.json', 'w') as f:
        json.dump(config_v1, f, indent=2)

    with open('config_v2.json', 'w') as f:
        json.dump(config_v2, f, indent=2)

    # 执行比对
    result = tool.compare_files(
        source_file='config_v1.json',
        target_file='config_v2.json',
        config_type='json',
        output_format='json'
    )

    print("JSON比对结果：")
    print(result)

    # 生成HTML报告
    html_result = tool.compare_files(
        source_file='config_v1.json',
        target_file='config_v2.json',
        config_type='json',
        output_format='html',
        output_file='diff_report.html'
    )

    print("\nHTML报告已生成: diff_report.html")


def example_compare_properties():
    """示例：比对Properties配置文件"""
    tool = ConfigDiffTool()

    # 准备Properties内容
    props_v1 = """
# Database Configuration
db.host=localhost
db.port=3306
db.name=mydb

# Application Settings
app.name=MyApp
app.debug=true
"""

    props_v2 = """
# Database Configuration
db.host=192.168.1.100
db.port=3306
db.name=mydb
db.pool.size=20

# Application Settings
app.name=MyApp
app.debug=false
app.feature.enabled=true
"""

    # 保存文件
    with open('config_v1.properties', 'w') as f:
        f.write(props_v1)

    with open('config_v2.properties', 'w') as f:
        f.write(props_v2)

    # 执行比对
    result = tool.compare_files(
        source_file='config_v1.properties',
        target_file='config_v2.properties',
        config_type='properties',
        output_format='json'
    )

    print("\nProperties比对结果：")
    print(result)


def example_programmatic_usage():
    """示例：编程方式使用"""
    from diff_engine import DiffEngine

    engine = DiffEngine(ignore_whitespace=True)

    # 直接比对JSON对象
    source = {"key1": "value1", "key2": "value2"}
    target = {"key1": "value1", "key3": "value3"}

    result = engine.compare_json(source, target)

    print("\n编程方式比对结果：")
    print(f"新增: {result.summary['added']}")
    print(f"删除: {result.summary['deleted']}")
    print(f"修改: {result.summary['modified']}")

    for diff in result.differences:
        print(f"  {diff.type.value}: {diff.path}")


if __name__ == '__main__':
    # example_compare_json_files()
    example_compare_properties()
    # example_programmatic_usage()