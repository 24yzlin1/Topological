from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QObject,
    QStringListModel,
    QThread,
    QUrl,
    Signal,
    Slot,
)

from app.core import Graph, GraphIO, TopoSortResult
from app.ui.workers.sort_worker import SortWorker

_SORT_CONFIRM_THRESHOLD = 10
_DISPLAY_LIMIT = 1000

# Graph layout constants — must match node dimensions in GraphView.qml
_NODE_W = 100.0
_NODE_H = 36.0
_LAYER_GAP = 120.0
_NODE_GAP = 50.0
_PADDING = 30.0

QML_ROOT = Path(__file__).resolve().parent / "qml"


class Backend(QObject):
    status = Signal(str)
    message = Signal(str, str)
    confirmSort = Signal(int)
    fileLoaded = Signal(str)

    graphChanged = Signal()
    sortRunningChanged = Signal()
    statsChanged = Signal()
    truncatedChanged = Signal()
    graphLayoutChanged = Signal()
    resultChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._graph: Graph | None = None
        self._thread: QThread | None = None
        self._worker: SortWorker | None = None
        self._sort_running = False

        self._orders = QStringListModel(self)
        self._stats_text = "尚未排序"
        self._truncated = False
        self._truncation_text = ""
        self._node_layout: list[dict] = []
        self._edge_layout: list[dict] = []
        self._canvas_width: float = 0.0
        self._canvas_height: float = 0.0
        self._last_result: TopoSortResult | None = None

    @Property(bool, notify=graphChanged)
    def hasGraph(self) -> bool:
        return self._graph is not None

    @Property(int, notify=graphChanged)
    def nodeCount(self) -> int:
        return len(self._graph.nodes) if self._graph is not None else 0

    @Property(int, notify=graphChanged)
    def edgeCount(self) -> int:
        return len(self._graph.edges) if self._graph is not None else 0

    @Property(bool, notify=sortRunningChanged)
    def sortRunning(self) -> bool:
        return self._sort_running

    @Property(QObject, constant=True)
    def ordersModel(self) -> QObject:
        return self._orders

    @Property(str, notify=statsChanged)
    def statsText(self) -> str:
        return self._stats_text

    @Property(bool, notify=truncatedChanged)
    def truncated(self) -> bool:
        return self._truncated

    @Property(str, notify=truncatedChanged)
    def truncationText(self) -> str:
        return self._truncation_text

    @Property(int, constant=True)
    def confirmThreshold(self) -> int:
        return _SORT_CONFIRM_THRESHOLD

    @Property(list, notify=graphLayoutChanged)
    def nodeLayout(self) -> list:
        return self._node_layout

    @Property(list, notify=graphLayoutChanged)
    def edgeLayout(self) -> list:
        return self._edge_layout

    @Property(float, notify=graphLayoutChanged)
    def graphViewWidth(self) -> float:
        return self._canvas_width

    @Property(float, notify=graphLayoutChanged)
    def graphViewHeight(self) -> float:
        return self._canvas_height

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._last_result is not None

    @Slot(str)
    def loadFromText(self, raw: str) -> None:
        try:
            graph = Graph.from_string(raw)
        except ValueError as exc:
            self.message.emit("载入失败", str(exc))
            return

        if not graph.nodes:
            self.message.emit("载入失败", "输入为空，请输入至少一条关系。")
            return

        self._graph = graph
        self._compute_graph_layout()
        self._clear_results()
        self.graphChanged.emit()
        self.status.emit("图载入成功")

    @Slot(QUrl)
    def readFile(self, url: QUrl) -> None:
        path = url.toLocalFile()
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            self.message.emit("导入失败", f"无法读取文件：\n{exc}")
            return
        self.fileLoaded.emit(text)

    @Slot()
    def requestSort(self) -> None:
        if self._graph is None or self._sort_running:
            return

        count = len(self._graph.nodes)
        if count > _SORT_CONFIRM_THRESHOLD:
            self.confirmSort.emit(count)
            return
        self.startSort()

    @Slot()
    def startSort(self) -> None:
        if self._graph is None or self._sort_running:
            return

        self._set_sort_running(True)

        self._thread = QThread(self)
        self._worker = SortWorker(self._graph)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_sort_finished)
        self._worker.error.connect(self._on_sort_error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

    def _on_sort_finished(self, result: TopoSortResult) -> None:
        self._last_result = result
        self.resultChanged.emit()
        self._update_orders(result)
        self._set_sort_running(False)
        self.status.emit("排序完成")

    def _on_sort_error(self, message: str) -> None:
        self.message.emit("排序失败", message)
        self._set_sort_running(False)

    def _on_thread_finished(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None

    def _clear_results(self) -> None:
        self._orders.setStringList([])
        self._stats_text = "尚未排序"
        self._truncated = False
        self._truncation_text = ""
        self._last_result = None
        self.resultChanged.emit()
        self.statsChanged.emit()
        self.truncatedChanged.emit()

    def _compute_graph_layout(self) -> None:
        """Compute a layered layout (left-to-right) for the DAG visualization.
        Nodes in the same topological layer are stacked vertically."""
        graph = self._graph

        if graph is None or not graph.nodes:
            self._node_layout = []
            self._edge_layout = []
            self._canvas_width = 0.0
            self._canvas_height = 0.0
            self.graphLayoutChanged.emit()
            return

        # Layer = longest path from any source node
        in_deg = dict(graph.in_degree)
        layer: dict[str, int] = {}
        queue = [nid for nid in graph.nodes if in_deg[nid] == 0]
        for nid in queue:
            layer[nid] = 0

        while queue:
            nid = queue.pop(0)
            for succ in graph.adjacency[nid]:
                in_deg[succ] -= 1
                if in_deg[succ] == 0:
                    preds = graph.reverse_adjacency[succ]
                    layer[succ] = max(layer[p] for p in preds) + 1
                    queue.append(succ)

        # Place any cyclic nodes (unreached by Kahn's) in the last layer
        max_l = max(layer.values()) if layer else -1
        for nid in graph.nodes:
            if nid not in layer:
                layer[nid] = max_l + 1

        # Group by layer
        layer_groups: dict[int, list[str]] = {}
        for nid, lyr in layer.items():
            layer_groups.setdefault(lyr, []).append(nid)

        # Compute canvas size
        max_nodes_in_layer = max(len(g) for g in layer_groups.values())
        total_h = max(1, max_nodes_in_layer) * (_NODE_H + _NODE_GAP)
        max_layer_id = max(layer_groups.keys())
        canvas_w = max_layer_id * (_NODE_W + _LAYER_GAP) + _NODE_W + 2 * _PADDING
        canvas_h = total_h + 2 * _PADDING

        # Assign coordinates
        pos: dict[str, tuple[float, float]] = {}
        nodes: list[dict] = []
        for lyr, nids in sorted(layer_groups.items()):
            count = len(nids)
            group_h = count * (_NODE_H + _NODE_GAP) - _NODE_GAP
            start_y = _PADDING + (total_h - group_h) / 2
            x = _PADDING + lyr * (_NODE_W + _LAYER_GAP)
            for i, nid in enumerate(nids):
                y = start_y + i * (_NODE_H + _NODE_GAP)
                pos[nid] = (x, y)
                nodes.append({
                    "name": graph.node_by_id[nid].name,
                    "x": x,
                    "y": y,
                })

        # Edge endpoints: right-center of source to left-center of target
        edges: list[dict] = []
        for eid in graph.edges:
            edge = graph.edge_by_id[eid]
            sx, sy = pos[edge.source.id]
            tx, ty = pos[edge.target.id]
            edges.append({
                "fromX": sx + _NODE_W,
                "fromY": sy + _NODE_H / 2,
                "toX": tx,
                "toY": ty + _NODE_H / 2,
            })

        self._node_layout = nodes
        self._edge_layout = edges
        self._canvas_width = canvas_w
        self._canvas_height = canvas_h
        self.graphLayoutChanged.emit()

    def _update_orders(self, result: TopoSortResult) -> None:
        total = result.order_count
        shown = min(total, _DISPLAY_LIMIT)

        self._orders.setStringList(
            [" → ".join(node.name for node in order) for order in result.orders[:shown]]
        )
        self._stats_text = (
            f"节点数：{result.node_count}\n"
            f"边数：{result.edge_count}\n"
            f"方案数：{result.order_count}\n"
            f"耗时：{_format_timedelta(result.elapsed)}"
        )
        self._truncated = total > _DISPLAY_LIMIT
        self._truncation_text = (
            f"仅显示前 {shown} 条，共 {total} 条" if self._truncated else ""
        )
        self.statsChanged.emit()
        self.truncatedChanged.emit()

    def _set_sort_running(self, running: bool) -> None:
        if self._sort_running != running:
            self._sort_running = running
            self.sortRunningChanged.emit()

    def _is_sort_running(self) -> bool:
        thread = self._thread
        if thread is None:
            return False
        try:
            return thread.isRunning()
        except RuntimeError:
            self._thread = None
            self._worker = None
            return False

    @Slot(QUrl)
    def exportTxt(self, url: QUrl) -> None:
        if self._last_result is None:
            self.message.emit("导出失败", "没有排序结果可导出")
            return
        path = url.toLocalFile()
        try:
            GraphIO.save_sorts_to_txt(path, self._last_result.orders)
        except OSError as exc:
            self.message.emit("导出失败", f"无法写入文件：\n{exc}")
            return
        self.status.emit("排序结果已导出")

    @Slot(str)
    def onImageExported(self, path: str) -> None:
        self.status.emit("图片已导出")

    @Slot()
    def shutdown(self) -> None:
        if self._is_sort_running():
            self._thread.quit()
            self._thread.wait(5000)


def _format_timedelta(td: timedelta) -> str:
    total = td.total_seconds()
    if total < 1:
        return f"{total * 1000:.1f} 毫秒"
    return f"{total:.3f} 秒"
