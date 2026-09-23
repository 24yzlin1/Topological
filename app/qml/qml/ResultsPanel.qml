import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import AppBackend 1.0

Item {
    id: root
    signal sortRequested

    // 0 = txt export, 1 = image export
    property int _exportMode: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // Toggle + Export buttons
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                text: stack.currentIndex === 0 ? qsTr("切换到图形视图") : qsTr("切换到排序结果")
                onClicked: stack.currentIndex = stack.currentIndex === 0 ? 1 : 0
            }

            Item { Layout.fillWidth: true }

            Button {
                text: stack.currentIndex === 0 ? qsTr("导出 TXT") : qsTr("导出图片")
                enabled: stack.currentIndex === 0 ? Backend.hasResult : Backend.hasGraph
                onClicked: {
                    if (stack.currentIndex === 0) {
                        root._exportMode = 0
                        exportDialog.defaultSuffix = "txt"
                        exportDialog.nameFilters = ["文本文件 (*.txt)"]
                    } else {
                        root._exportMode = 1
                        exportDialog.defaultSuffix = "png"
                        exportDialog.nameFilters = ["PNG 图片 (*.png)"]
                    }
                    exportDialog.open()
                }
            }
        }

        StackLayout {
            id: stack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0

            // Page 0: Sort results
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                Button {
                    Layout.fillWidth: true
                    text: qsTr("拓扑排序")
                    highlighted: true
                    enabled: Backend.hasGraph && !Backend.sortRunning
                    onClicked: root.sortRequested()
                }

                GroupBox {
                    title: qsTr("统计")
                    Layout.fillWidth: true
                    Label {
                        anchors.fill: parent
                        text: Backend.statsText
                        wrapMode: Text.WordWrap
                    }
                }

                GroupBox {
                    title: qsTr("排序方案")
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 6
                        ListView {
                            id: listView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: Backend.ordersModel
                            ScrollBar.vertical: ScrollBar {}
                            delegate: ItemDelegate {
                                width: listView.width
                                text: model.display
                                highlighted: false
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: Backend.truncated
                            text: Backend.truncationText
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }

            // Page 1: Graph visualization
            GraphView {
                id: graphView
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }

    FileDialog {
        id: exportDialog
        fileMode: FileDialog.SaveFile
        onAccepted: {
            if (root._exportMode === 0) {
                Backend.exportTxt(selectedFile)
            } else {
                graphView.grabToFile(selectedFile)
            }
        }
    }
}
