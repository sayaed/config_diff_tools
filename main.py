# main.py
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

from diff_engine import DiffEngine
from parsers import ParserFactory
from formatters.json_formatter import JSONFormatter
from formatters.html_formatter import HTMLFormatter


class ConfigDiffTool:
    """配置比对工具主类"""

    def __init__(self, ignore_whitespace: bool = True, case_sensitive: bool = True):
        self.engine = DiffEngine(
            ignore_whitespace=ignore_whitespace,
            case_sensitive=case_sensitive
        )

    def compare_files(self, source_file: str, target_file: str,
                      config_type: str = None, output_format: str = 'json',
                      output_file: str = None) -> str:
        """
        比对两个配置文件
        """
        # 读取文件内容
        with open(source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()

        with open(target_file, 'r', encoding='utf-8') as f:
            target_content = f.read()

        # 自动检测配置类型
        if not config_type:
            config_type = self._detect_config_type(source_file, target_file)

        # 获取解析器
        parser = ParserFactory.get_parser(config_type)

        # 解析配置
        source_data = parser.parse(source_content)
        target_data = parser.parse(target_content)

        # 准备版本信息（包含properties）
        import datetime
        source_info = {
            "name": Path(source_file).name,
            "path": source_file,
            "update_time": datetime.fromtimestamp(Path(source_file).stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

        target_info = {
            "name": Path(target_file).name,
            "path": target_file,
            "update_time": datetime.fromtimestamp(Path(target_file).stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

        # 执行比对
        if config_type in ['json']:
            result = self.engine.compare_json(
                source_data, target_data,
                source_info, target_info
            )
        elif config_type in ['properties']:
            result = self.engine.compare_properties(
                source_data, target_data,
                source_info, target_info
            )
        else:
            result = self.engine.compare_text(
                source_content, target_content,
                source_info, target_info,
                source_properties=source_content,  # 传递文本内容
                target_properties=target_content
            )

        # 格式化输出
        if output_format == 'html':
            output = HTMLFormatter.format(result)
        else:
            output = JSONFormatter.format(result)

        # 写入文件或返回
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {output_file}")

        return output


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='配置项版本比对工具')
    parser.add_argument('source', help='源配置文件路径')
    parser.add_argument('target', help='目标配置文件路径')
    parser.add_argument('--type', '-t', help='配置类型（json/yaml/xml/properties/text）')
    parser.add_argument('--format', '-f', choices=['json', 'html'], default='json',
                        help='输出格式（默认：json）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--case-sensitive', action='store_true',
                        help='大小写敏感（默认：True）')
    parser.add_argument('--no-ignore-whitespace', action='store_true',
                        help='不忽略空白字符')

    args = parser.parse_args()

    # 创建比对工具
    tool = ConfigDiffTool(
        ignore_whitespace=not args.no_ignore_whitespace,
        case_sensitive=args.case_sensitive
    )

    try:
        # 执行比对
        result = tool.compare_files(
            source_file=args.source,
            target_file=args.target,
            config_type=args.type,
            output_format=args.format,
            output_file=args.output
        )

        # 如果没有指定输出文件，打印到控制台
        if not args.output:
            print(result)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()