import QtQuick
import "petmask"

/*
 * 把宠物窗口的 input region 裁到命中框（QWindow::setMask）。
 * 画布四周的透明区域不再吞鼠标，下面的应用还能点。
 * 插件不可用时 Loader 失败，宠物本身照常工作。
 */
Item {
    property var targetWindow: null
    property var pet: null
    property real topPad: 0

    WindowMask {
        window: targetWindow
        rects: pet ? [Qt.rect(pet.hitX, topPad + pet.hitY, pet.hitW, pet.hitH)] : []
    }
}
