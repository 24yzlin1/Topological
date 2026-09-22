import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import AppBackend 1.0

Item {
    id: root
    signal loadRequested(string text)
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12
        GroupBox {
            title: qsTr("输入（每行一个 <先修课程,后续课程>）")
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    TextArea {
                        id: editor
                        wrapMode: TextArea.Wrap
                        selectByMouse: true
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Button {
                        text: qsTr("从文件导入")
                        flat: true
                        onClicked: fileDialog.open()
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Button {
                        text: qsTr("载入图")
                        highlighted: true
                        onClicked: root.loadRequested(editor.text)
                    }
                }
            }
        }
        GroupBox {
            title: qsTr("图信息")
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 4
                Label {
                    text: qsTr("节点数：") + (Backend.hasGraph ? Backend.nodeCount : "—")
                }
                Label {
                    text: qsTr("边数：") + (Backend.hasGraph ? Backend.edgeCount : "—")
                }
            }
        }
    }
    FileDialog {
        id: fileDialog
        title: qsTr("选择图文件")
        nameFilters: ["文本文件 (*.txt)", "所有文件 (*)"]
        onAccepted: Backend.readFile(selectedFile)
    }
    Connections {
        target: Backend
        function onFileLoaded(text) {
            editor.text = text;
        }
    }
}
