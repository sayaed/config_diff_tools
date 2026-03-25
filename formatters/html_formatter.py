# formatters/html_formatter.py
from typing import List, Dict
from datetime import datetime
from diff_engine import CompareResult, DiffType




class HTMLFormatter:
    """HTML报告生成器"""

    @staticmethod
    def format(result: CompareResult) -> str:
        """生成HTML格式的比对报告"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>配置比对报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'SF Mono', monospace;
                    background: #F9FAFB;
                    padding: 24px;
                    color: #1F2937;
                }}

                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}

                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 32px;
                }}

                .header h1 {{
                    font-size: 24px;
                    margin-bottom: 8px;
                }}

                .header .meta {{
                    opacity: 0.9;
                    font-size: 14px;
                }}

                .summary {{
                    display: flex;
                    gap: 16px;
                    padding: 24px 32px;
                    background: white;
                    border-bottom: 1px solid #E5E7EB;
                }}

                .summary-card {{
                    flex: 1;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }}

                .summary-card.added {{
                    background: #E6F7E6;
                    border-left: 4px solid #52C41A;
                }}

                .summary-card.deleted {{
                    background: #FFE6E6;
                    border-left: 4px solid #F5222D;
                }}

                .summary-card.modified {{
                    background: #FFF7E6;
                    border-left: 4px solid #FA8C16;
                }}

                .summary-card .count {{
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }}

                .summary-card .label {{
                    font-size: 14px;
                    color: #6B7280;
                }}

                .info-bar {{
                    display: flex;
                    justify-content: space-between;
                    padding: 16px 32px;
                    background: #F9FAFB;
                    border-bottom: 1px solid #E5E7EB;
                    font-size: 14px;
                }}

                .version-info {{
                    display: flex;
                    gap: 32px;
                }}

                .version {{
                    display: flex;
                    gap: 8px;
                }}

                .version-label {{
                    font-weight: 600;
                    color: #6B7280;
                }}

                .version-value {{
                    color: #3B82F6;
                    font-weight: 500;
                }}

                .differences {{
                    padding: 24px 32px;
                }}

                .diff-item {{
                    margin-bottom: 16px;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    overflow: hidden;
                }}

                .diff-header {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 16px;
                    background: #F9FAFB;
                    border-bottom: 1px solid #E5E7EB;
                    font-family: 'SF Mono', monospace;
                    font-size: 13px;
                }}

                .diff-badge {{
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}

                .diff-badge.added {{
                    background: #52C41A;
                    color: white;
                }}

                .diff-badge.deleted {{
                    background: #F5222D;
                    color: white;
                }}

                .diff-badge.modified {{
                    background: #FA8C16;
                    color: white;
                }}

                .diff-path {{
                    color: #6B7280;
                    font-weight: 500;
                }}

                .diff-content {{
                    padding: 16px;
                    font-family: 'SF Mono', monospace;
                    font-size: 13px;
                    line-height: 1.5;
                }}

                .diff-value {{
                    padding: 8px;
                    margin: 4px 0;
                    border-radius: 4px;
                }}

                .diff-value.source {{
                    background: #FFE6E6;
                    border-left: 3px solid #F5222D;
                }}

                .diff-value.target {{
                    background: #E6F7E6;
                    border-left: 3px solid #52C41A;
                }}

                .diff-label {{
                    font-weight: 600;
                    color: #6B7280;
                    margin-bottom: 4px;
                    font-size: 12px;
                }}

                pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    margin: 0;
                }}

                .footer {{
                    padding: 20px 32px;
                    text-align: center;
                    border-top: 1px solid #E5E7EB;
                    color: #6B7280;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 配置项版本比对报告</h1>
                    <div class="meta">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>

                <div class="summary">
                    <div class="summary-card added">
                        <div class="count">+{result.summary['added']}</div>
                        <div class="label">新增配置项</div>
                    </div>
                    <div class="summary-card deleted">
                        <div class="count">-{result.summary['deleted']}</div>
                        <div class="label">删除配置项</div>
                    </div>
                    <div class="summary-card modified">
                        <div class="count">~{result.summary['modified']}</div>
                        <div class="label">修改配置项</div>
                    </div>
                </div>

                <div class="info-bar">
                    <div class="version-info">
                        <div class="version">
                            <span class="version-label">版本A：</span>
                            <span class="version-value">{result.source_info.get('name', 'source')}</span>
                        </div>
                        <div class="version">
                            <span class="version-label">版本B：</span>
                            <span class="version-value">{result.target_info.get('name', 'target')}</span>
                        </div>
                    </div>
                    <div>配置类型：{result.config_type.upper()}</div>
                </div>

                <div class="differences">
        """

        if not result.differences:
            html += """
                    <div style="text-align: center; padding: 60px 20px;">
                        <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                        <div style="font-size: 16px; color: #6B7280;">两个版本的配置内容完全一致</div>
                    </div>
            """
        else:
            for diff in result.differences:
                badge_class = diff.type.value
                badge_text = {
                    'added': '新增',
                    'deleted': '删除',
                    'modified': '修改'
                }.get(diff.type.value, diff.type.value)

                html += f"""
                    <div class="diff-item">
                        <div class="diff-header">
                            <span class="diff-badge {badge_class}">{badge_text}</span>
                            <span class="diff-path">{diff.path}</span>
                        </div>
                        <div class="diff-content">
                """

                if diff.type == DiffType.MODIFIED:
                    html += f"""
                            <div class="diff-value source">
                                <div class="diff-label">版本A：</div>
                                <pre>{HTMLFormatter._escape_html(str(diff.source_value))}</pre>
                            </div>
                            <div class="diff-value target">
                                <div class="diff-label">版本B：</div>
                                <pre>{HTMLFormatter._escape_html(str(diff.target_value))}</pre>
                            </div>
                    """
                elif diff.type == DiffType.ADDED:
                    html += f"""
                            <div class="diff-value target">
                                <div class="diff-label">新增值：</div>
                                <pre>{HTMLFormatter._escape_html(str(diff.target_value))}</pre>
                            </div>
                    """
                elif diff.type == DiffType.DELETED:
                    html += f"""
                            <div class="diff-value source">
                                <div class="diff-label">删除值：</div>
                                <pre>{HTMLFormatter._escape_html(str(diff.source_value))}</pre>
                            </div>
                    """

                html += """
                        </div>
                    </div>
                """

        html += """
                </div>
                <div class="footer">
                    配置项版本比对工具 | 报告自动生成，仅供参考
                </div>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        html_escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;"
        }
        return "".join(html_escape_table.get(c, c) for c in text)