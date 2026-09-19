from __future__ import annotations

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSplitter

from app.core import Graph, TopoSortResult
from app.ui.widgets.input_panel import InputPanel
from app.ui.widgets.results_panel import ResultsPanel
from app.ui.workers.sort_worker import SortWorker

_SORT_CONFIRM_THRESHOLD = 10


class MainWindow(QMainWindow):
    """Main window: left input panel + right results panel in a splitter."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("课程拓扑排序工具")
        self.resize(900, 600)

        self._graph: Graph | None = None
        self._thread: QThread | None = None
        self._worker: SortWorker | None = None

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._input = InputPanel()
        self._results = ResultsPanel()
        splitter.addWidget(self._input)
        splitter.addWidget(self._results)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # --- Wire signals ---
        self._input.load_requested.connect(self._on_load)
        self._results.sort_requested.connect(self._on_sort)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _on_load(self, raw: str) -> None:
        try:
            graph = Graph.from_string(raw)
        except ValueError as exc:
            QMessageBox.warning(self, "载入失败", str(exc))
            return

        if not graph.nodes:
            QMessageBox.warning(self, "载入失败", "输入为空，请输入至少一条关系。")
            return

        self._graph = graph
        self._input.display_graph_info(len(graph.nodes), len(graph.edges))
        self._results.enable_sort(True)
        self._results.clear()
        self.statusBar().showMessage("图载入成功", 3000)

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def _is_sort_running(self) -> bool:
        """True if a sort thread is still alive. Safely handles the case
        where the underlying C++ QThread has already been deleted by
        ``deleteLater`` but the Python reference is still non-None."""
        thread = self._thread
        if thread is None:
            return False
        try:
            return thread.isRunning()
        except RuntimeError:
            # C++ object deleted — treat as not running and clear stale ref
            self._thread = None
            self._worker = None
            return False

    def _on_sort(self) -> None:
        if self._graph is None:
            return
        if self._is_sort_running():
            return  # a sort is already in flight

        node_count = len(self._graph.nodes)
        if node_count > _SORT_CONFIRM_THRESHOLD:
            reply = QMessageBox.question(
                self,
                "确认排序",
                f"当前图有 {node_count} 个节点，拓扑排序方案数可能达到 "
                f"{node_count}! 量级，可能导致程序卡顿。\n确定继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._results.enable_sort(False)

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
        self._results.display_result(result)
        self._results.enable_sort(True)
        self.statusBar().showMessage("排序完成", 3000)

    def _on_sort_error(self, message: str) -> None:
        QMessageBox.warning(self, "排序失败", message)
        self._results.enable_sort(True)

    def _on_thread_finished(self) -> None:
        """Clear references after the thread finishes so the next sort
        starts cleanly. ``deleteLater`` is deferred, so we null the Python
        refs here rather than calling it ourselves."""
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt API name
        if self._is_sort_running():
            self._thread.quit()
            self._thread.wait(5000)
        event.accept()
