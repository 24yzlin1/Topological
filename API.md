# 图与拓扑排序工具文档

## 概述

本工具提供：

- 有向图数据结构：`Graph`
- 节点与边：`Node`、`Edge`
- 图档案读写与排序结果汇出：`GraphIO`
- 拓扑排序枚举：`KahnSorter`
- 排序统计结果：`TopoSortResult`

可用于解析 `<A,B>` 形式的依赖关系，检查是否为 DAG，并列出所有可能的拓扑排序。

## 模块结构

假设项目模块如下，实际汇入路径请依项目调整：

```python
from app.core.type import Graph, Node, Edge
from app.core.sorter import KahnSorter, TopoSortResult
from app.core.io import GraphIO
```

## 数据模型

### `Node`

```python
@dataclass(eq=False)
class Node:
    id: str
    name: str
```

| 字段   | 型别  | 说明                    |
| ------ | ----- | ----------------------- |
| `id`   | `str` | UUID 字符串，唯一标识符 |
| `name` | `str` | 节点名称，例如 `A`、`B` |

`eq=False` 表示不自动生成等值比较，实务上以对象身份或 `id` 判断。

### `Edge`

```python
@dataclass(eq=False)
class Edge:
    id: str
    source: Node
    target: Node
```

| 字段     | 型别   | 说明                    |
| -------- | ------ | ----------------------- |
| `id`     | `str`  | UUID 字符串，唯一标识符 |
| `source` | `Node` | 起点                    |
| `target` | `Node` | 终点                    |

### `Graph`

`Graph` 使用节点 ID 与边 ID 作为主要索引。

内部字段：

| 字段                | 型别                   | 说明                                              |
| ------------------- | ---------------------- | ------------------------------------------------- |
| `nodes`             | `list[str]`            | 所有节点 ID                                       |
| `node_by_id`        | `dict[str, Node]`      | 节点 ID → `Node`                                  |
| `edges`             | `list[str]`            | 所有边 ID                                         |
| `edge_by_id`        | `dict[str, Edge]`      | 边 ID → `Edge`                                    |
| `edge_keys`         | `set[tuple[str, str]]` | 已存在的 `(source_id, target_id)`，用于避免重复边 |
| `adjacency`         | `dict[str, set[str]]`  | 节点 ID → 后继节点 ID 集合                        |
| `reverse_adjacency` | `dict[str, set[str]]`  | 节点 ID → 前驱节点 ID 集合                        |
| `in_degree`         | `dict[str, int]`       | 节点 ID → 入度                                    |

#### 常用方法

| 方法                                             | 说明                            |
| ------------------------------------------------ | ------------------------------- |
| `Graph.from_string(raw: str) -> Graph`           | 从 `<A,B>` 格式字符串建立图     |
| `add_node(name: str) -> Node`                    | 新增节点，自动产生 UUID         |
| `add_edge(source: Node, target: Node) -> Edge`   | 新增有向边                      |
| `remove_edge(edge: str) -> bool`                 | 依边 ID 删除边                  |
| `get_node(id: str) -> Node \| None`              | 依 ID 取得节点                  |
| `get_edge(id: str) -> Edge \| None`              | 依 ID 取得边                    |
| `get_adjacency() -> dict[str, set[str]]`         | 回传「节点名称 → 后继名称集合」 |
| `get_reverse_adjacency() -> dict[str, set[str]]` | 回传「节点名称 → 前驱名称集合」 |
| `get_in_degree() -> dict[str, int]`              | 回传「节点名称 → 入度」         |
| `is_dag() -> bool`                               | 判断是否为有向无环图            |

#### 建立图范例

```python
raw = """
<A,B>
<B,C>
<A,C>
"""

graph = Graph.from_string(raw)
print(graph.is_dag())  # True
```

#### 限制

- 不允许自环：`add_edge(A, A)` 会抛出 `ValueError("Self-loop is not allowed")`
- 不允许重复边：相同 `(source, target)` 会抛出 `ValueError("Duplicate edge")`
- `from_string` 会依节点名称自动去重，同名节点只建立一次

## `GraphIO`

`GraphIO` 提供档案读写工具。

### `load_graph_from_file(path: str) -> Graph`

从文本文件载入图。

- 文件格式：每行一个 `<source,target>`
- 空行会忽略
- 档案不存在：`FileNotFoundError`
- 档案为空：`ValueError("文件是空的")`
- 格式错误：`ValueError`

范例档案 `graph.txt`：

```text
<A,B>
<B,C>
<A,C>
```

使用：

```python
graph = GraphIO.load_graph_from_file("graph.txt")
```

### `save_sorts_to_txt(path: str, sorts: list[list[Node]]) -> None`

将拓扑排序结果存成 TXT。

输出格式：

```text
方案 A -> B -> C
方案 B -> A -> C
```

使用：

```python
GraphIO.save_sorts_to_txt("sorts.txt", result.orders)
```

### `save_graph_to_file(path: str, graph: Graph) -> None`

将图的边汇出成 `<source,target>` 格式。

输出范例：

```text
<A,B>
<B,C>
<A,C>
```

使用：

```python
GraphIO.save_graph_to_file("export.txt", graph)
```

### `save_sorts_to_csv(path: str, sorts: list[list[Node]]) -> None`

将拓扑排序结果存成 CSV。

表头：

```text
方案编号,拓扑排序
```

输出范例：

```csv
方案编号,拓扑排序
A -> B -> C
B -> A -> C
```

使用：

```python
GraphIO.save_sorts_to_csv("sorts.csv", result.orders)
```

## 拓扑排序

### `TopoSortResult`

```python
class TopoSortResult(NamedTuple):
    orders: list[list[Node]]
    elapsed: timedelta
    node_count: int
    edge_count: int
    order_count: int
```

| 字段          | 说明                                 |
| ------------- | ------------------------------------ |
| `orders`      | 所有拓扑排序，每个排序是 `Node` 列表 |
| `elapsed`     | 排序耗时                             |
| `node_count`  | 节点数                               |
| `edge_count`  | 边数                                 |
| `order_count` | 拓扑排序方案数                       |

### `KahnSorter`

```python
sorter = KahnSorter(graph)
result = sorter.topological_orders()
```

方法：

| 方法                                     | 说明                             |
| ---------------------------------------- | -------------------------------- |
| `sort() -> list[list[Node]]`             | 回传所有拓扑排序                 |
| `topological_orders() -> TopoSortResult` | 回传排序结果与统计信息           |
| `_sort()`                                | 内部方法，回传节点 ID 的拓扑排序 |

若图中有环，会抛出：

```python
ValueError("Graph contains a cycle; topological sort is not possible")
```

### 完整使用范例

```python
from app.core.type import Graph
from app.core.io import GraphIO
from app.core.sorter import KahnSorter

graph = GraphIO.load_graph_from_file("graph.txt")

sorter = KahnSorter(graph)
result = sorter.topological_orders()

print("节点数：", result.node_count)
print("边数：", result.edge_count)
print("方案数：", result.order_count)
print("耗时：", result.elapsed)

for i, order in enumerate(result.orders, :
    names = [node.name for node in order]
    print(f"方案{i}: " + " -> ".join(names))

GraphIO.save_sorts_to_txt("sorts.txt", result.orders)
GraphIO.save_sorts_to_csv("sorts.csv", result.orders)
GraphIO.save_graph_to_file("export.txt", graph)
```

## 输入格式

图档每行格式：

```text
<source,target>
```

范例：

```text
<A,B>
<B,C>
<A,C>
```

规则：

- 空行忽略
- 每行使用正则 `< (.*?) , (.*?) >` 搜寻
- 节点名称前后空白会被去除
- 同一行若有多个 `<...>`，目前只取第一个匹配
- 节点名称建议使用简单字符串，避免包含 `,` 或 `>`

## 输出格式

### TXT

```text
方案 A -> B -> C
方案 B -> A -> C
```

### CSV

```csv
方案编号,拓扑排序
A -> B -> C
B -> A -> C
```

### 图汇出

```text
<A,B>
<B,C>
<A,C>
```

## 异常与注意事项

| 情境         | 异常                                     |
| ------------ | ---------------------------------------- |
| 图有环       | `ValueError`                             |
| 自环         | `ValueError("Self-loop is not allowed")` |
| 重复边       | `ValueError("Duplicate edge")`           |
| 档案不存在   | `FileNotFoundError`                      |
| 档案为空     | `ValueError("文件是空的")`               |
| 输入格式错误 | `ValueError`                             |

其他注意事项：

`KahnSorter` 会枚举所有拓扑排序，方案数可能随节点数快速增长，甚至达到阶乘级。大图不建议直接枚举全部。
`Graph.nodes` 与 `Graph.edges` 储存的是 ID，不是对象。
`get_adjacency()`、`get_reverse_adjacency()`、`get_in_degree()` 回传的键是节点名称，不是 ID。
`GraphIO.save_*` 会覆盖同名档案。
CSV 使用 `utf-，若用 Excel 开启可能需改用 `utf-sig`。
 `Graph.remove_edge()`目前程序代码中`return True`的缩排位于`for` 循环内，可能导致只检查第一个端点就返回。若需删除孤立节点，建议检查并修正此处。

修正范例：

```python
def remove_edge(self, edge: str) -> bool:
    existing = self.edge_by_id.get(edge)
    if existing is None:
        return False

    source_id = existing.source.id
    target_id = existing.target.id

    self.edges.remove(edge)
    del self.edge_by_id[edge]
    self.edge_keys.remove((source_id, target_id))

    self.adjacency[source_id].discard(target_id)
    self.reverse_adjacency[target_id].discard(source_id)
    self.in_degree[target_id] -= 1

    for node_id in (source_id, target_id):
        if self.in_degree[node_id] == and not self.adjacency[node_id]:
            self.nodes.remove(node_id)
            del self.node_by_id[node_id]
            del self.adjacency[node_id]
            del self.reverse_adjacency[node_id]
            del self.in_degree[node_id]

    return True
```

## 快速开始

```python
from app.core.type import Graph
from app.core.io import GraphIO
from app.core.sorter import KahnSorter

graph = GraphIO.load_graph_from_file("graph.txt")
result = KahnSorter(graph).topological_orders()

GraphIO.save_sorts_to_txt("sorts.txt", result.orders)
GraphIO.save_sorts_to_csv("sorts.csv", result.orders)
GraphIO.save_graph_to_file("export.txt", graph)
```
