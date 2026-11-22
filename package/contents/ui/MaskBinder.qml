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

    WindowMask {
        window: targetWindow
        // pet.y 是 Pet 在其父窗口内的坐标；直接参与绑定，
        // 避免加载时取一次 0 之后再也不更新。
        rects: pet ? [Qt.rect(pet.hitX, pet.y + pet.hitY, pet.hitW, pet.hitH)] : []
    }
}
