import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import AppBackend 1.0

ApplicationWindow {
    id: window
    width: 900
    height: 600
    visible: true
    title: qsTr(" ")
    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        InputPanel {
            id: inputPanel
            SplitView.fillWidth: true
            SplitView.minimumWidth: 240
            onLoadRequested: text => Backend.loadFromText(text)
        }
        ResultsPanel {
            id: resultsPanel
            SplitView.fillWidth: true
            SplitView.minimumWidth: 240
            onSortRequested: Backend.requestSort()
        }
    }
    footer: ToolBar {
        Label {
            id: statusLabel
            anchors.fill: parent
            anchors.leftMargin: 12
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Timer {
            id: statusTimer
            interval: 3000
            onTriggered: statusLabel.text = ""
        }
    }
    Connections {
        target: Backend
        function onStatus(text) {
            statusLabel.text = text;
            statusTimer.restart();
        }
        function onMessage(title, text) {
            errorDialog.title = title;
            errorDialog.text = text;
            errorDialog.open();
        }
        function onConfirmSort(count) {
            confirmDialog.text = qsTr("当前图有 %1 个节点，拓扑排序方案数可能达到 %1! 量级，" + "可能导致程序卡顿。\n确定继续？").arg(count);
            confirmDialog.open();
        }
    }
    MessageDialog {
        id: errorDialog
        buttons: MessageDialog.Ok
    }
    MessageDialog {
        id: confirmDialog
        title: qsTr("确认排序")
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: Backend.startSort()
    }
    onClosing: close => {
        Backend.shutdown();
        close.accepted = true;
    }
}
