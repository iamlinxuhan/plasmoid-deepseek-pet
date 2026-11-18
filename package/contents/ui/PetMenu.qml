import QtQuick
import QtQuick.Controls as QQC2

/*
 * 普通桌面组件模式的菜单（Popup 套 PetMenuPanel）。
 * Layer Shell 模式不用它，改用独立的 LayerPetMenuWindow。
 */
QQC2.Popup {
    id: popup

    property bool petSleeping: false
    property bool hasSleep: true
    property var actionListRef: panel.actionListRef

    signal playRequested(string name)
    signal walkRequested(string name)
    signal idleRequested()
    signal turnRequested()
    signal sleepRequested()
    signal wakeRequested()
    signal resetRequested()
    signal chimeRequested()
    signal configureRequested()

    width: panel.width
    height: panel.height
    padding: 0
    modal: false
    focus: true
    closePolicy: QQC2.Popup.CloseOnEscape | QQC2.Popup.CloseOnPressOutside
    background: Item {}

    PetMenuPanel {
        id: panel
        anchors.fill: parent
        petSleeping: popup.petSleeping
        hasSleep: popup.hasSleep

        onPlayRequested: function (name) { popup.playRequested(name); popup.close(); }
        onWalkRequested: function (name) { popup.walkRequested(name); popup.close(); }
        onIdleRequested: { popup.idleRequested(); popup.close(); }
        onTurnRequested: { popup.turnRequested(); popup.close(); }
        onSleepRequested: { popup.sleepRequested(); popup.close(); }
        onWakeRequested: { popup.wakeRequested(); popup.close(); }
        onResetRequested: { popup.resetRequested(); popup.close(); }
        onChimeRequested: { popup.chimeRequested(); popup.close(); }
        onConfigureRequested: { popup.configureRequested(); popup.close(); }
        onDismissRequested: popup.close()
    }

    onOpened: panel.resetView()
}
