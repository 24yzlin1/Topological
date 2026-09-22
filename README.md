# 课程拓扑排序工具

基于 Kahn 算法的有向无环图（DAG）拓扑排序枚举工具，以课程先修关系为应用场景。支持解析 `<先修课程,后续课程>` 格式的依赖关系，检测图中是否存在环，并枚举所有合法的拓扑排序方案。提供 QML 桌面 GUI 界面。

## 功能

- **图构建与解析**：从文本构建有向图，每行一个 `<source,target>` 表示一条有向边
- **环检测**：自动检测自环、重复边和环结构，并以友好提示报错
- **拓扑排序枚举**：基于 Kahn 算法枚举所有合法的拓扑排序方案
- **可视化**：GUI 支持文字列表与分层 DAG 图形两种视图切换
- **文件导入**：从 `.txt` 文件导入课程先修关系
- **排序导出**：将排序结果导出为 TXT 或 CSV

## 快速开始

### 环境要求

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装与运行

```bash
uv sync                # 安装依赖（PySide6 等）
uv run python main.py  # 启动 GUI
```

### 输入格式

每行一个 `<source,target>`，表示 source → target 的有向边：

```text
<数据结构,操作系统>
<操作系统,计算机网络>
<高等数学,数据结构>
<离散数学,数据结构>
```

- 空行忽略
- 正则匹配：`<(.*?),(.*?)>`
- 节点名称前后空白会去除
- 同名节点自动去重

## 使用方法

### GUI

运行 `uv run python main.py` 打开界面：

1. **左侧输入面板**：在文本区输入 `<先修,后续>` 关系，或点击「从文件导入」读取 `.txt` 文件
2. 点击「载入图」构建有向图，下方显示节点数和边数
3. 点击右侧「拓扑排序」按钮执行排序
4. **右侧结果面板**：
   - 默认显示统计信息（节点数/边数/方案数/耗时）和所有排序方案列表
   - 点击「切换到图形视图」可查看分层 DAG 可视化（节点为矩形，边带箭头）
   - 再次点击切回文字列表
5. 节点数超过 10 个时会弹出确认框，防止阶乘级方案数导致卡顿

### Python API

```python
from app.core import Graph, KahnSorter, GraphIO

# 从字符串构建图
graph = Graph.from_string("""
<A,B>
<A,C>
<B,D>
<C,D>
""")

# 枚举所有拓扑排序
result = KahnSorter(graph).topological_orders()
print(f"方案数：{result.order_count}")
for order in result.orders:
    print(" → ".join(node.name for node in order))

# 从文件加载
graph = GraphIO.load_graph_from_file("courses.txt")

# 导出排序结果
GraphIO.save_sorts_to_txt("sorts.txt", result.orders)
GraphIO.save_sorts_to_csv("sorts.csv", result.orders)

# 导出图数据
GraphIO.save_graph_to_file("graph.txt", graph)
```

详细 API 参考见 [API.md](API.md)。

## 项目结构

```
main.py              # GUI 入口（QML + PySide6）
app/
  core/              # 核心算法层
    type.py          # Graph, Node, Edge — 图数据结构与解析
    topo.py          # KahnSorter, TopoSortResult — 拓扑排序枚举
    file_io.py       # GraphIO — 文件读写与导出
  qml/               # QML 界面层
    backend.py       # Backend(QObject) — PySide6/QML 桥接层
    qml/             # QML 视图文件
      Main.qml       # 主窗口（SplitView + 对话框）
      InputPanel.qml # 输入面板（文本编辑 + 文件导入）
      ResultsPanel.qml # 结果面板（排序结果 / 图形视图切换）
      GraphView.qml  # DAG 可视化（Flickable + Canvas）
  ui/                # 旧版 Widget 界面（已弃用，workers/ 仍被 qml/ 共享）
    workers/
      sort_worker.py # SortWorker — QThread 后台排序（qml/backend.py 复用）
API.md               # 核心 API 文档
TASK.md              # 项目进度跟踪
```

## 技术栈

| 层 | 技术 |
|---|---|
| 核心算法 | Python 3.13 标准库（`uuid`, `dataclasses`, `re`, `csv`） |
| GUI 框架 | PySide6 ≥ 6.11.2（QML + QtQuick Material 风格） |
| 异步排序 | QThread + Signal/Slot |
| 包管理 | uv |

## 异常处理

| 情境 | 异常 |
|---|---|
| 图有环 | `ValueError("Graph contains a cycle; topological sort is not possible")` |
| 自环 | `ValueError("Self-loop is not allowed")` |
| 重复边 | `ValueError("Duplicate edge")` |
| 文件不存在 | `FileNotFoundError` |
| 文件为空 | `ValueError("文件是空的")` |
| 格式错误 | `ValueError` |

GUI 界面会捕获所有异常并弹窗提示，不会崩溃。
