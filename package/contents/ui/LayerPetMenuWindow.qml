import QtQuick
import QtQuick.Window as QW
import "layershell" as LayerShell

/*
 * 置顶菜单：独立 Layer Shell 表面。
 * 从宠物窗口弹出的普通 Popup 只是 xdg 窗口，鱼移动后会掉到前台窗口下面；
 * 这里让菜单自己也成为 LayerOverlay，并跟随鱼的实时屏幕坐标。
 */
QW.Window {
    id: win

    property real menuX: 0
    property real menuY: 0
    property bool petSleeping: false
    property bool hasSleep: true
    property var panelRef: panel

    signal playRequested(string name)
    signal walkRequested(string name)
    signal idleRequested()
    signal turnRequested()
    signal sleepRequested()
    signal wakeRequested()
    signal resetRequested()
    signal chimeRequested()
    signal configureRequested()

    width: 504
    height: 576
    visible: false
    color: "transparent"
    flags: Qt.FramelessWindowHint
    title: "DeepSeek 大肥鱼 · 菜单"

    LayerShell.Window.scope: "deepseek-pet-menu"
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft
    LayerShell.Window.margins.left: menuX
    LayerShell.Window.margins.top: menuY
    LayerShell.Window.margins.right: 0
    LayerShell.Window.margins.bottom: 0
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand

    PetMenuPanel {
        id: panel
        anchors.fill: parent
        petSleeping: win.petSleeping
        hasSleep: win.hasSleep

        onPlayRequested: function (name) { win.playRequested(name); win.closeMenu(); }
        onWalkRequested: function (name) { win.walkRequested(name); win.closeMenu(); }
        onIdleRequested: { win.idleRequested(); win.closeMenu(); }
        onTurnRequested: { win.turnRequested(); win.closeMenu(); }
        onSleepRequested: { win.sleepRequested(); win.closeMenu(); }
        onWakeRequested: { win.wakeRequested(); win.closeMenu(); }
        onResetRequested: { win.resetRequested(); win.closeMenu(); }
        onChimeRequested: { win.chimeRequested(); win.closeMenu(); }
        onConfigureRequested: { win.configureRequested(); win.closeMenu(); }
        onDismissRequested: win.closeMenu()
    }

    function openAt(x, y) {
        menuX = x;
        menuY = y;
        visible = true;
        panel.resetView();
    }

    function closeMenu() {
        visible = false;
    }

    Component.onDestruction: visible = false
}
