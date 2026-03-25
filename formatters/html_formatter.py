# formatters/html_formatter.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from diff_engine import CompareResult, DiffType
import json


class HTMLFormatter:
    """HTML报告生成器 - 左右对比布局"""

    @staticmethod
    def format(result: CompareResult) -> str:
        """
        生成HTML格式的比对报告（左右对比布局）

        Args:
            result: 比对结果对象

        Returns:
            HTML字符串
        """
        # 从 result 中获取 properties
        source_props = result.source_properties if result.source_properties is not None else {}
        target_props = result.target_properties if result.target_properties is not None else {}

        # 如果是文本类型，需要转换为行号映射
        if result.config_type == "text" and isinstance(source_props, str):
            source_props = HTMLFormatter._text_to_lines(source_props)
            target_props = HTMLFormatter._text_to_lines(target_props)

        # 构建差异映射
        diff_map = {}
        for diff in result.differences:
            diff_map[diff.path] = diff

        # 生成HTML
        html = HTMLFormatter._generate_html(
            result, source_props, target_props, diff_map
        )

        return html

    @staticmethod
    def _text_to_lines(text: str) -> Dict[str, str]:
        """将文本转换为行号映射"""
        if not text:
            return {}
        lines = text.splitlines()
        result = {}
        for i, line in enumerate(lines, 1):
            result[f"line_{i}"] = line
        return result

    @staticmethod
    def _generate_html(result: CompareResult, source_props: Dict,
                       target_props: Dict, diff_map: Dict) -> str:
        """生成HTML内容"""

        # 准备统计信息
        added_count = result.summary.get('added', 0)
        deleted_count = result.summary.get('deleted', 0)
        modified_count = result.summary.get('modified', 0)

        # 获取所有键（用于显示）
        all_keys = sorted(set(source_props.keys()) | set(target_props.keys()))

        html = f"""<!DOCTYPE html>
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
            height: 100vh;
            overflow: hidden;
        }}

        /* 主容器 - 全屏flex布局 */
        .app {{
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        /* 顶部导航栏 */
        .navbar {{
            background: white;
            border-bottom: 1px solid #E5E7EB;
            padding: 0 24px;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }}

        .navbar-left {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .logo {{
            font-size: 20px;
            font-weight: 600;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .navbar-right {{
            display: flex;
            gap: 12px;
        }}

        /* 配置选择区 */
        .config-bar {{
            background: white;
            border-bottom: 1px solid #E5E7EB;
            padding: 16px 24px;
            flex-shrink: 0;
        }}

        .config-row {{
            display: flex;
            align-items: center;
            gap: 24px;
            flex-wrap: wrap;
        }}

        .config-selector {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }}

        .config-selector label {{
            font-size: 14px;
            font-weight: 500;
            color: #6B7280;
        }}

        .version-group {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: #F9FAFB;
            padding: 8px 16px;
            border-radius: 8px;
            flex: 1;
        }}

        .version-group .label {{
            font-size: 12px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
        }}

        .version-select {{
            padding: 6px 12px;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            font-size: 14px;
            background: white;
            cursor: pointer;
            min-width: 150px;
        }}

        .version-select:hover {{
            border-color: #3B82F6;
        }}

        .env-buttons {{
            display: flex;
            gap: 8px;
        }}

        .env-btn {{
            padding: 6px 12px;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            background: white;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .env-btn:hover {{
            border-color: #3B82F6;
            color: #3B82F6;
        }}

        .env-btn.active {{
            background: #3B82F6;
            border-color: #3B82F6;
            color: white;
        }}

        .action-buttons {{
            display: flex;
            gap: 8px;
        }}

        .btn-primary {{
            padding: 8px 20px;
            background: #3B82F6;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn-primary:hover {{
            background: #2563EB;
        }}

        .btn-secondary {{
            padding: 8px 16px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn-secondary:hover {{
            border-color: #3B82F6;
            color: #3B82F6;
        }}

        /* 统计摘要栏 */
        .stats-bar {{
            background: white;
            border-bottom: 1px solid #E5E7EB;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }}

        .stats-cards {{
            display: flex;
            gap: 16px;
        }}

        .stat-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 16px;
            border-radius: 8px;
            background: #F9FAFB;
        }}

        .stat-card.added {{
            background: #E6F7E6;
        }}

        .stat-card.deleted {{
            background: #FFE6E6;
        }}

        .stat-card.modified {{
            background: #FFF7E6;
        }}

        .stat-number {{
            font-size: 24px;
            font-weight: 700;
        }}

        .stat-label {{
            font-size: 12px;
            color: #6B7280;
        }}

        .stat-card.added .stat-number {{
            color: #52C41A;
        }}

        .stat-card.deleted .stat-number {{
            color: #F5222D;
        }}

        .stat-card.modified .stat-number {{
            color: #FA8C16;
        }}

        .export-btn {{
            padding: 6px 12px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }}

        /* 工具栏 */
        .toolbar {{
            background: #F9FAFB;
            padding: 8px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border-bottom: 1px solid #E5E7EB;
            flex-shrink: 0;
        }}

        .tool-btn {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .tool-btn:hover {{
            border-color: #3B82F6;
        }}

        .tool-btn.active {{
            background: #3B82F6;
            border-color: #3B82F6;
            color: white;
        }}

        .search-box {{
            flex: 1;
            max-width: 300px;
            padding: 6px 12px;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            font-size: 13px;
        }}

        .diff-nav {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: auto;
        }}

        .nav-btn {{
            padding: 4px 8px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }}

        .nav-btn:hover {{
            border-color: #3B82F6;
        }}

        .diff-counter {{
            font-size: 13px;
            color: #6B7280;
        }}

        /* 左右对比视图 - 核心布局 */
        .compare-view {{
            flex: 1;
            display: flex;
            overflow: hidden;
            position: relative;
        }}

        /* 左侧面板 */
        .panel-left {{
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #E5E7EB;
            overflow: hidden;
            background: white;
        }}

        /* 右侧面板 */
        .panel-right {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: white;
        }}

        /* 面板头部 */
        .panel-header {{
            padding: 12px 16px;
            background: #F9FAFB;
            border-bottom: 1px solid #E5E7EB;
            flex-shrink: 0;
        }}

        .version-title {{
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 4px;
        }}

        .version-meta {{
            font-size: 12px;
            color: #6B7280;
        }}

        .panel-actions {{
            margin-top: 8px;
            display: flex;
            gap: 8px;
        }}

        .panel-action-btn {{
            padding: 4px 8px;
            font-size: 12px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            cursor: pointer;
        }}

        /* 内容区域 - 可滚动 */
        .panel-content {{
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }}

        /* 配置项行 */
        .config-row {{
            display: flex;
            border-bottom: 1px solid #F3F4F6;
            min-height: 36px;
        }}

        .config-row:hover {{
            background: #F9FAFB;
        }}

        .config-row.highlight {{
            background: #FFF7E6;
        }}

        .row-key {{
            width: 35%;
            padding: 8px 12px;
            font-weight: 500;
            color: #1F2937;
            border-right: 1px solid #F3F4F6;
            word-break: break-word;
            white-space: pre-wrap;
        }}

        .row-value {{
            width: 65%;
            padding: 8px 12px;
            color: #6B7280;
            word-break: break-word;
            white-space: pre-wrap;
            font-family: inherit;
        }}

        /* 差异样式 */
        .config-row.added .row-key,
        .config-row.added .row-value {{
            background: #E6F7E6;
        }}

        .config-row.added .row-key {{
            border-left: 3px solid #52C41A;
        }}

        .config-row.deleted .row-key,
        .config-row.deleted .row-value {{
            background: #FFE6E6;
        }}

        .config-row.deleted .row-key {{
            border-left: 3px solid #F5222D;
        }}

        .config-row.modified .row-key,
        .config-row.modified .row-value {{
            background: #FFF7E6;
        }}

        .config-row.modified .row-key {{
            border-left: 3px solid #FA8C16;
        }}

        .diff-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
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

        /* 空状态 */
        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #9CA3AF;
        }}

        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}

        /* 差异导航浮层 */
        .diff-nav-overlay {{
            position: fixed;
            right: 24px;
            bottom: 24px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 8px;
            display: flex;
            gap: 8px;
            z-index: 100;
        }}

        /* 滚动条样式 */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: #F1F1F1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #C1C1C1;
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #A8A8A8;
        }}

        /* 加载动画 */
        .loading {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}

        .spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid #E5E7EB;
            border-top-color: #3B82F6;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="app">
        <!-- 顶部导航栏 -->
        <div class="navbar">
            <div class="navbar-left">
                <div class="logo">📊 配置比对工具</div>
            </div>
            <div class="navbar-right">
                <button class="btn-secondary" onclick="window.location.reload()">刷新</button>
            </div>
        </div>

        <!-- 配置选择区 -->
        <div class="config-bar">
            <div class="config-row">
                <div class="config-selector">
                    <label>配置项：</label>
                    <select class="version-select" id="configSelect">
                        <option>{HTMLFormatter._escape_html(result.source_info.get('name', 'config'))}</option>
                    </select>
                </div>
                <div class="env-buttons">
                    <button class="env-btn">开发</button>
                    <button class="env-btn">测试</button>
                    <button class="env-btn">预发</button>
                    <button class="env-btn active">生产</button>
                </div>
            </div>
            <div class="config-row" style="margin-top: 12px;">
                <div class="version-group">
                    <span class="label">版本A</span>
                    <select class="version-select" id="versionASelect">
                        <option selected>{HTMLFormatter._escape_html(result.source_info.get('name', 'source'))}</option>
                    </select>
                </div>
                <div class="version-group">
                    <span class="label">版本B</span>
                    <select class="version-select" id="versionBSelect">
                        <option selected>{HTMLFormatter._escape_html(result.target_info.get('name', 'target'))}</option>
                    </select>
                </div>
                <div class="action-buttons">
                    <button class="btn-primary" onclick="compare()">🔍 比对</button>
                    <button class="btn-secondary" onclick="swapVersions()">↻ 交换</button>
                </div>
            </div>
        </div>

        <!-- 统计摘要栏 -->
        <div class="stats-bar">
            <div class="stats-cards">
                <div class="stat-card added">
                    <div class="stat-number">+{added_count}</div>
                    <div class="stat-label">新增</div>
                </div>
                <div class="stat-card deleted">
                    <div class="stat-number">-{deleted_count}</div>
                    <div class="stat-label">删除</div>
                </div>
                <div class="stat-card modified">
                    <div class="stat-number">~{modified_count}</div>
                    <div class="stat-label">修改</div>
                </div>
            </div>
            <button class="export-btn" onclick="exportReport()">📄 导出报告</button>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
            <button class="tool-btn" id="syncScrollBtn" onclick="toggleSyncScroll()">
                🔄 同步滚动
            </button>
            <button class="tool-btn" id="showDiffOnlyBtn" onclick="toggleDiffOnly()">
                📄 仅显示差异行
            </button>
            <input type="text" class="search-box" placeholder="🔍 搜索配置项..." id="searchInput" onkeyup="searchConfig()">
            <div class="diff-nav">
                <button class="nav-btn" onclick="prevDiff()">▲</button>
                <span class="diff-counter" id="diffCounter">0 / 0</span>
                <button class="nav-btn" onclick="nextDiff()">▼</button>
            </div>
        </div>

        <!-- 左右对比视图 -->
        <div class="compare-view" id="compareView">
            <!-- 左侧面板 -->
            <div class="panel-left">
                <div class="panel-header">
                    <div class="version-title">版本A: {HTMLFormatter._escape_html(result.source_info.get('name', 'source'))}</div>
                    <div class="version-meta">
                        更新时间: {HTMLFormatter._escape_html(result.source_info.get('update_time', '未知'))}
                        {f" | 环境: {HTMLFormatter._escape_html(result.source_info.get('environment', ''))}" if result.source_info.get('environment') else ''}
                    </div>
                    <div class="panel-actions">
                        <button class="panel-action-btn" onclick="copyPanel('left')">📋 复制全部</button>
                        <button class="panel-action-btn" onclick="downloadPanel('left')">💾 下载</button>
                    </div>
                </div>
                <div class="panel-content" id="leftContent">
                    {HTMLFormatter._render_config_content(source_props, diff_map, 'left', all_keys)}
                </div>
            </div>

            <!-- 右侧面板 -->
            <div class="panel-right">
                <div class="panel-header">
                    <div class="version-title">版本B: {HTMLFormatter._escape_html(result.target_info.get('name', 'target'))}</div>
                    <div class="version-meta">
                        更新时间: {HTMLFormatter._escape_html(result.target_info.get('update_time', '未知'))}
                        {f" | 环境: {HTMLFormatter._escape_html(result.target_info.get('environment', ''))}" if result.target_info.get('environment') else ''}
                    </div>
                    <div class="panel-actions">
                        <button class="panel-action-btn" onclick="copyPanel('right')">📋 复制全部</button>
                        <button class="panel-action-btn" onclick="downloadPanel('right')">💾 下载</button>
                    </div>
                </div>
                <div class="panel-content" id="rightContent">
                    {HTMLFormatter._render_config_content(target_props, diff_map, 'right', all_keys)}
                </div>
            </div>
        </div>
    </div>

    <div class="diff-nav-overlay" id="diffNavOverlay">
        <button class="nav-btn" onclick="prevDiff()">▲ 上一个</button>
        <span id="overlayDiffCounter">0/0</span>
        <button class="nav-btn" onclick="nextDiff()">下一个 ▼</button>
    </div>

    <script>
        // 差异项列表
        let diffItems = [];
        let currentDiffIndex = -1;
        let syncScroll = false;
        let showDiffOnly = false;

        // 获取所有差异行
        function collectDiffItems() {{
            diffItems = [];
            const leftRows = document.querySelectorAll('#leftContent .config-row');
            const rightRows = document.querySelectorAll('#rightContent .config-row');

            leftRows.forEach((row, index) => {{
                if (row.classList.contains('added') || row.classList.contains('deleted') || row.classList.contains('modified')) {{
                    diffItems.push({{
                        element: row,
                        panel: 'left',
                        index: index,
                        key: row.querySelector('.row-key')?.innerText || ''
                    }});
                }}
            }});

            // 也收集右侧的差异（避免重复）
            const existingKeys = new Set(diffItems.map(item => item.key));
            rightRows.forEach((row, index) => {{
                const key = row.querySelector('.row-key')?.innerText || '';
                if ((row.classList.contains('added') || row.classList.contains('deleted') || row.classList.contains('modified')) && 
                    !existingKeys.has(key)) {{
                    diffItems.push({{
                        element: row,
                        panel: 'right',
                        index: index,
                        key: key
                    }});
                }}
            }});

            updateDiffCounter();
        }}

        // 更新差异计数器
        function updateDiffCounter() {{
            const total = diffItems.length;
            const current = currentDiffIndex >= 0 ? currentDiffIndex + 1 : 0;
            document.getElementById('diffCounter').innerText = `${{current}} / ${{total}}`;
            document.getElementById('overlayDiffCounter').innerText = `${{current}}/${{total}}`;
        }}

        // 下一个差异
        function nextDiff() {{
            if (diffItems.length === 0) return;
            currentDiffIndex = (currentDiffIndex + 1) % diffItems.length;
            scrollToDiff(currentDiffIndex);
        }}

        // 上一个差异
        function prevDiff() {{
            if (diffItems.length === 0) return;
            currentDiffIndex = currentDiffIndex <= 0 ? diffItems.length - 1 : currentDiffIndex - 1;
            scrollToDiff(currentDiffIndex);
        }}

        // 滚动到指定差异
        function scrollToDiff(index) {{
            if (index < 0 || index >= diffItems.length) return;
            const item = diffItems[index];
            const panel = item.panel === 'left' ? document.getElementById('leftContent') : document.getElementById('rightContent');
            const targetRow = item.element;

            if (targetRow) {{
                targetRow.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                targetRow.classList.add('highlight');
                setTimeout(() => targetRow.classList.remove('highlight'), 2000);
            }}

            updateDiffCounter();
        }}

        // 切换同步滚动
        function toggleSyncScroll() {{
            syncScroll = !syncScroll;
            const btn = document.getElementById('syncScrollBtn');
            if (syncScroll) {{
                btn.classList.add('active');
                enableSyncScroll();
            }} else {{
                btn.classList.remove('active');
                disableSyncScroll();
            }}
        }}

        let scrollHandlerLeft = null;
        let scrollHandlerRight = null;

        function enableSyncScroll() {{
            const leftPanel = document.getElementById('leftContent');
            const rightPanel = document.getElementById('rightContent');

            scrollHandlerLeft = () => {{
                if (syncScroll) {{
                    rightPanel.scrollTop = leftPanel.scrollTop;
                }}
            }};

            scrollHandlerRight = () => {{
                if (syncScroll) {{
                    leftPanel.scrollTop = rightPanel.scrollTop;
                }}
            }};

            leftPanel.addEventListener('scroll', scrollHandlerLeft);
            rightPanel.addEventListener('scroll', scrollHandlerRight);
        }}

        function disableSyncScroll() {{
            const leftPanel = document.getElementById('leftContent');
            const rightPanel = document.getElementById('rightContent');

            if (scrollHandlerLeft) {{
                leftPanel.removeEventListener('scroll', scrollHandlerLeft);
            }}
            if (scrollHandlerRight) {{
                rightPanel.removeEventListener('scroll', scrollHandlerRight);
            }}
        }}

        // 切换仅显示差异
        function toggleDiffOnly() {{
            showDiffOnly = !showDiffOnly;
            const btn = document.getElementById('showDiffOnlyBtn');
            const leftRows = document.querySelectorAll('#leftContent .config-row');
            const rightRows = document.querySelectorAll('#rightContent .config-row');

            if (showDiffOnly) {{
                btn.classList.add('active');
                leftRows.forEach(row => {{
                    if (!row.classList.contains('added') && !row.classList.contains('deleted') && !row.classList.contains('modified')) {{
                        row.style.display = 'none';
                    }}
                }});
                rightRows.forEach(row => {{
                    if (!row.classList.contains('added') && !row.classList.contains('deleted') && !row.classList.contains('modified')) {{
                        row.style.display = 'none';
                    }}
                }});
            }} else {{
                btn.classList.remove('active');
                leftRows.forEach(row => row.style.display = 'flex');
                rightRows.forEach(row => row.style.display = 'flex');
            }}
        }}

        // 搜索功能
        function searchConfig() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const leftRows = document.querySelectorAll('#leftContent .config-row');
            const rightRows = document.querySelectorAll('#rightContent .config-row');

            leftRows.forEach(row => {{
                const key = row.querySelector('.row-key')?.innerText.toLowerCase() || '';
                if (searchTerm === '' || key.includes(searchTerm)) {{
                    row.style.display = 'flex';
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            rightRows.forEach(row => {{
                const key = row.querySelector('.row-key')?.innerText.toLowerCase() || '';
                if (searchTerm === '' || key.includes(searchTerm)) {{
                    row.style.display = 'flex';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}

        // 交换版本
        function swapVersions() {{
            alert('当前为静态报告，交换功能需要在实时系统中实现');
        }}

        // 比对
        function compare() {{
            alert('当前为静态报告，重新比对功能需要在实时系统中实现');
        }}

        // 导出报告
        function exportReport() {{
            const html = document.documentElement.outerHTML;
            const blob = new Blob([html], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `config_diff_report_${{new Date().toISOString().slice(0,19).replace(/:/g, '-')}}.html`;
            a.click();
            URL.revokeObjectURL(url);
        }}

        // 复制面板内容
        function copyPanel(panel) {{
            const content = panel === 'left' ? document.getElementById('leftContent') : document.getElementById('rightContent');
            const rows = content.querySelectorAll('.config-row');
            let text = '';
            rows.forEach(row => {{
                const key = row.querySelector('.row-key')?.innerText || '';
                const value = row.querySelector('.row-value')?.innerText || '';
                text += `${{key}} = ${{value}}\\n`;
            }});
            navigator.clipboard.writeText(text);
            alert('已复制到剪贴板');
        }}

        // 下载面板内容
        function downloadPanel(panel) {{
            const content = panel === 'left' ? document.getElementById('leftContent') : document.getElementById('rightContent');
            const rows = content.querySelectorAll('.config-row');
            let text = '';
            rows.forEach(row => {{
                const key = row.querySelector('.row-key')?.innerText || '';
                const value = row.querySelector('.row-value')?.innerText || '';
                text += `${{key}} = ${{value}}\\n`;
            }});
            const blob = new Blob([text], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `config_${{panel}}_${{new Date().toISOString().slice(0,19)}}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }}

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {{
            if (e.altKey && e.key === 'ArrowUp') {{
                e.preventDefault();
                prevDiff();
            }} else if (e.altKey && e.key === 'ArrowDown') {{
                e.preventDefault();
                nextDiff();
            }} else if (e.ctrlKey && e.key === 'f') {{
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }}
        }});

        // 初始化
        setTimeout(() => {{
            collectDiffItems();
            enableSyncScroll();
        }}, 100);
    </script>
</body>
</html>"""

        return html

    @staticmethod
    def _render_config_content(properties: Dict[str, str], diff_map: Dict,
                               panel: str, all_keys: List[str]) -> str:
        """
        渲染配置内容

        Args:
            properties: 配置属性字典
            diff_map: 差异映射
            panel: 面板标识（left/right）
            all_keys: 所有键的列表（用于保持左右对齐）
        """
        if not properties:
            return """
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div>无配置内容</div>
            </div>
            """

        rows = []

        # 使用 all_keys 来保持左右顺序一致
        for key in all_keys:
            value = properties.get(key, '')
            diff = diff_map.get(key)
            diff_class = ""
            diff_badge = ""

            if diff:
                if diff.type.value == "added":
                    diff_class = "added"
                    diff_badge = '<span class="diff-badge added">新增</span>'
                elif diff.type.value == "deleted":
                    diff_class = "deleted"
                    diff_badge = '<span class="diff-badge deleted">删除</span>'
                elif diff.type.value == "modified":
                    diff_class = "modified"
                    diff_badge = '<span class="diff-badge modified">修改</span>'

            # 如果值为空且没有差异，显示占位符
            display_value = value if value else '(未设置)'

            rows.append(f"""
            <div class="config-row {diff_class}" data-key="{HTMLFormatter._escape_html(key)}">
                <div class="row-key">{HTMLFormatter._escape_html(key)}{diff_badge}</div>
                <div class="row-value">{HTMLFormatter._escape_html(str(display_value))}</div>
            </div>
            """)

        return ''.join(rows)

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        html_escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;"
        }
        return "".join(html_escape_table.get(c, c) for c in str(text))