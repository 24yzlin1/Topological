from __future__ import annotations

import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from PySide6.QtQuickControls2 import QQuickStyle

from app.qml import QML_ROOT, Backend


def main():
    QQuickStyle.setStyle("Material")
    # QQuickStyle.setStyle("FluentWinUI3")

    app = QGuiApplication(sys.argv)

    backend = Backend()
    qmlRegisterSingletonInstance(Backend, "AppBackend", 1, 0, "Backend", backend)

    engine = QQmlApplicationEngine()
    engine.load(str(QML_ROOT / "Main.qml"))

    app.exec()


if __name__ == "__main__":
    main()
