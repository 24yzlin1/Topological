import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    signal sortRequested
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12
        Button {
            Layout.fillWidth: true
            text: qsTr("拓扑排序")
            highlighted: true
            enabled: backend.hasGraph && !backend.sortRunning
            onClicked: root.sortRequested()
        }
        GroupBox {
            title: qsTr("统计")
            Layout.fillWidth: true
            Label {
                anchors.fill: parent
                text: backend.statsText
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
                    model: backend.ordersModel
                    ScrollBar.vertical: ScrollBar {}
                    delegate: ItemDelegate {
                        width: listView.width
                        text: model.display
                        highlighted: false
                    }
                }
                Label {
                    Layout.fillWidth: true
                    visible: backend.truncated
                    text: backend.truncationText
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
