from __future__ import annotations

from datetime import timedelta

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import TopoSortResult

_DISPLAY_LIMIT = 1000


class ResultsPanel(QWidget):
    """Right panel: sort trigger, stats summary, and the list of topological orders."""

    sort_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)

        # --- Sort button ---
        self._sort_btn = QPushButton("拓扑排序")
        self._sort_btn.setEnabled(False)
        outer.addWidget(self._sort_btn)

        # --- Stats ---
        stats_group = QGroupBox("统计")
        stats_layout = QVBoxLayout(stats_group)
        self._stats_label = QLabel("尚未排序")
        stats_layout.addWidget(self._stats_label)
        outer.addWidget(stats_group)

        # --- Results list ---
        results_group = QGroupBox("排序方案")
        results_layout = QVBoxLayout(results_group)
        self._list = QListWidget()
        results_layout.addWidget(self._list)
        self._truncation_label = QLabel("")
        self._truncation_label.setVisible(False)
        results_layout.addWidget(self._truncation_label)
        outer.addWidget(results_group, stretch=1)

        # --- Signals ---
        self._sort_btn.clicked.connect(self.sort_requested.emit)

    def enable_sort(self, enabled: bool) -> None:
        self._sort_btn.setEnabled(enabled)

    def display_result(self, result: TopoSortResult) -> None:
        """Populate the list and stats from a completed sort."""
        self._list.clear()

        total = result.order_count
        shown = min(total, _DISPLAY_LIMIT)
        for order in result.orders[:shown]:
            self._list.addItem(" → ".join(node.name for node in order))

        self._stats_label.setText(
            f"节点数：{result.node_count}\n"
            f"边数：{result.edge_count}\n"
            f"方案数：{result.order_count}\n"
            f"耗时：{_format_timedelta(result.elapsed)}"
        )

        if total > _DISPLAY_LIMIT:
            self._truncation_label.setText(f"仅显示前 {shown} 条，共 {total} 条")
            self._truncation_label.setVisible(True)
        else:
            self._truncation_label.setVisible(False)

    def clear(self) -> None:
        self._list.clear()
        self._stats_label.setText("尚未排序")
        self._truncation_label.setVisible(False)


def _format_timedelta(td: timedelta) -> str:
    total = td.total_seconds()
    if total < 1:
        return f"{total * 1000:.1f} 毫秒"
    return f"{total:.3f} 秒"
