from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.core import Graph, KahnSorter, TopoSortResult


class SortWorker(QObject):
    """Runs KahnSorter.topological_orders() off the UI thread.

    moveToThread onto a QThread, connect started -> run, then collect
    finished/error via queued signals back on the main thread.
    """

    finished = Signal(object)  # TopoSortResult
    error = Signal(str)

    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self._graph = graph

    def run(self) -> None:
        try:
            result: TopoSortResult = KahnSorter(self._graph).topological_orders()
        except ValueError as exc:
            self.error.emit(str(exc))
            return
        except Exception as exc:  # safety net — never crash the UI
            self.error.emit(f"排序过程中发生意外错误: {exc}")
            return
        self.finished.emit(result)
