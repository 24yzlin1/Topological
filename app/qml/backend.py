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

from app.core import Graph, TopoSortResult
from app.ui.workers.sort_worker import SortWorker

_SORT_CONFIRM_THRESHOLD = 10
_DISPLAY_LIMIT = 1000

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
        self.statsChanged.emit()
        self.truncatedChanged.emit()

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
