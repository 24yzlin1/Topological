import QtQuick
import QtQuick.Controls
import AppBackend 1.0

Item {
    id: root

    function grabToFile(url) {
        graphContent.grabToImage(function(result) {
            result.saveToFile(url)
            Backend.onImageExported("")
        })
    }

    Flickable {
        id: flickable
        anchors.fill: parent
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        contentWidth: Math.max(Backend.graphViewWidth, flickable.width)
        contentHeight: Math.max(Backend.graphViewHeight, flickable.height)

        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        // Wrapper — grabbable unit containing edges + nodes
        Item {
            id: graphContent
            width: Backend.graphViewWidth
            height: Backend.graphViewHeight

            // Edge layer (drawn first, behind nodes)
            Canvas {
                id: edgeCanvas
                width: Backend.graphViewWidth
                height: Backend.graphViewHeight
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.strokeStyle = "#9e9e9e"
                    ctx.lineWidth = 1.5
                    ctx.fillStyle = "#9e9e9e"

                    var edges = Backend.edgeLayout
                    for (var i = 0; i < edges.length; i++) {
                        var e = edges[i]

                        // Line
                        ctx.beginPath()
                        ctx.moveTo(e.fromX, e.fromY)
                        ctx.lineTo(e.toX, e.toY)
                        ctx.stroke()

                        // Arrowhead at target
                        var angle = Math.atan2(e.toY - e.fromY, e.toX - e.fromX)
                        var arrowLen = 8
                        var arrowAngle = Math.PI / 7
                        ctx.beginPath()
                        ctx.moveTo(e.toX, e.toY)
                        ctx.lineTo(
                            e.toX - arrowLen * Math.cos(angle - arrowAngle),
                            e.toY - arrowLen * Math.sin(angle - arrowAngle)
                        )
                        ctx.lineTo(
                            e.toX - arrowLen * Math.cos(angle + arrowAngle),
                            e.toY - arrowLen * Math.sin(angle + arrowAngle)
                        )
                        ctx.closePath()
                        ctx.fill()
                    }
                }
                Component.onCompleted: requestPaint()
            }

            // Node layer (drawn on top of edges)
            Repeater {
                model: Backend.nodeLayout
                Rectangle {
                    x: modelData.x
                    y: modelData.y
                    width: 100   // must match _NODE_W in backend.py
                    height: 36   // must match _NODE_H in backend.py
                    color: "#e3f2fd"
                    border.color: "#1976d2"
                    border.width: 1
                    radius: 4
                    Text {
                        anchors.fill: parent
                        anchors.margins: 4
                        text: modelData.name
                        font.pixelSize: 13
                        elide: Text.ElideRight
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }

    // Empty state overlay
    Text {
        visible: !Backend.hasGraph
        text: qsTr("请先载入图")
        color: "#999"
        anchors.centerIn: parent
        font.pixelSize: 14
        z: 1
    }

    Connections {
        target: Backend
        function onGraphLayoutChanged() {
            edgeCanvas.requestPaint()
        }
    }
}
