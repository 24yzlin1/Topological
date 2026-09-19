from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class InputPanel(QWidget):
    """Left panel: text editor for ``<source,target>`` lines, file import, graph info."""

    load_requested = Signal(str)  # raw editor text — MainWindow parses it

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)

        # --- Input editor ---
        input_group = QGroupBox("输入（每行一个 <先修课程,后续课程>）")
        input_layout = QVBoxLayout(input_group)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("<数据结构,操作系统>\n<操作系统,计算机网络>")
        input_layout.addWidget(self._editor)

        button_row = QHBoxLayout()
        self._import_btn = QPushButton("从文件导入")
        self._load_btn = QPushButton("载入图")
        self._load_btn.setDefault(True)
        button_row.addWidget(self._import_btn)
        button_row.addStretch()
        button_row.addWidget(self._load_btn)
        input_layout.addLayout(button_row)

        outer.addWidget(input_group)

        # --- Graph info ---
        info_group = QGroupBox("图信息")
        info_layout = QVBoxLayout(info_group)
        self._node_label = QLabel("节点数：—")
        self._edge_label = QLabel("边数：—")
        info_layout.addWidget(self._node_label)
        info_layout.addWidget(self._edge_label)

        outer.addWidget(info_group)
        outer.addStretch()

        # --- Signals ---
        self._import_btn.clicked.connect(self._on_import)
        self._load_btn.clicked.connect(self._on_load)

    def display_graph_info(self, node_count: int, edge_count: int) -> None:
        """Update the info labels after a successful load."""
        self._node_label.setText(f"节点数：{node_count}")
        self._edge_label.setText(f"边数：{edge_count}")

    # ------------------------------------------------------------------

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "导入失败", f"无法读取文件：\n{exc}")
            return
        self._editor.setPlainText(text)

    def _on_load(self) -> None:
        self.load_requested.emit(self._editor.toPlainText())
