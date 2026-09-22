import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import AppBackend 1.0

Item {
    id: root
    signal sortRequested

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // Toggle button
        Button {
            text: stack.currentIndex === 0 ? qsTr("切换到图形视图") : qsTr("切换到排序结果")
            onClicked: stack.currentIndex = stack.currentIndex === 0 ? 1 : 0
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
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }
}
