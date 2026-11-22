import QtQuick
import QtQuick.Window as QW
import "layershell" as LayerShell

/*
 * 真正的置顶桌宠：Wayland Layer Shell 表面。
 *
 * 窗口本身就是宠物画布（贴紧身体四周，不覆盖整个屏幕），LayerShell 负责把它
 * 放在所有普通窗口之上；bodyX/bodyY 是该窗口的屏幕坐标，拖动/走路/抛掷时窗口
 * 跟着鼠标或物理移动。输入区域只有这一小块，所以不会挡住其它窗口的点击。
 *
 * 需要 qml6-module-org-kde-layershell（Debian/Ubuntu 包名）或发行版等价包。
 */
QW.Window {
    id: win

    property var petConfig: ({})
    property bool petVisible: true
    // 供自动化测试/外部脚本读取宠物实例。
    property var petItem: pet
    property var menuWindowRef: menuWindow
    property var maskLoaderRef: maskLoader
    signal configureRequested()

    // 气泡画在鱼头顶上方；Layer Shell 窗口要在上方留出这块透明画布，
    // 同时把窗口整体上移，保证鱼身在屏幕上的位置仍然是 bodyY。
    readonly property real bubbleReserve: 96
    readonly property real petWidthForPet: Math.max(96, petConfig.petSize !== undefined ? petConfig.petSize : 420)
    // 窗口本身永远不越过屏幕上沿：靠近顶部时改为把 Pet 内容向上移，
    // 这样负 margin 只用于左右两侧，顶部不依赖 compositor 是否接受负 margin。
    readonly property real windowTop: Math.max(0, pet.bodyY - bubbleReserve)

    width: pet.petWidth
    height: pet.petHeight + bubbleReserve
    visible: petVisible
    color: "transparent"
    flags: Qt.FramelessWindowHint
    title: "DeepSeek 大肥鱼"

    LayerShell.Window.scope: "deepseek-pet"
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft
    LayerShell.Window.margins.left: pet.bodyX
    LayerShell.Window.margins.top: win.windowTop
    LayerShell.Window.margins.right: 0
    LayerShell.Window.margins.bottom: 0
    // -1 = 不占工作区、不把其它窗口挤开。
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone

    Pet {
        id: pet
        x: 0
        y: pet.bodyY - win.windowTop
        width: win.petWidthForPet
        height: win.petWidthForPet * 9 / 16
        layerMode: true
        screenWidth: Screen.width
        screenHeight: Screen.height
        workWidth: Screen.desktopAvailableWidth
        workHeight: Screen.desktopAvailableHeight
        // desktopAvailableHeight 在部分 Wayland/浮动面板配置下等于整屏高度；
        // 这时退回 Plasma 默认面板厚度 44px，保证脚底正好贴住任务栏上沿。
        bottomInset: Screen.height - Screen.desktopAvailableHeight > 0
                     ? Screen.height - Screen.desktopAvailableHeight : 44
        topReserve: win.bubbleReserve
        petSize: win.petConfig.petSize !== undefined ? win.petConfig.petSize : 420
        allowRoam: win.petConfig.allowRoam !== undefined ? win.petConfig.allowRoam : true
        activityLevel: win.petConfig.activityLevel !== undefined ? win.petConfig.activityLevel : 1
        clickSoundEnabled: win.petConfig.clickSoundEnabled !== undefined ? win.petConfig.clickSoundEnabled : true
        throwPower: win.petConfig.throwPower !== undefined ? win.petConfig.throwPower : 1.0
        gravity: win.petConfig.gravity !== undefined ? win.petConfig.gravity : 1400
        walkSpeed: win.petConfig.walkSpeed !== undefined ? win.petConfig.walkSpeed : 2.5
        startCorner: win.petConfig.startCorner !== undefined ? win.petConfig.startCorner : 3
        chimeEnabled: win.petConfig.chimeEnabled !== undefined ? win.petConfig.chimeEnabled : true
        strollEnabled: win.petConfig.strollEnabled !== undefined ? win.petConfig.strollEnabled : true
        monitorEnabled: win.petConfig.monitorEnabled !== undefined ? win.petConfig.monitorEnabled : true
        cpuUsage: win.petConfig.cpuUsage !== undefined ? win.petConfig.cpuUsage : 0
        memUsage: win.petConfig.memUsage !== undefined ? win.petConfig.memUsage : 0
        onConfigureRequested: win.configureRequested()
        onMenuRequested: function (px, py) { win.toggleMenu(px, py); }
        onMenuDismissRequested: menuWindow.closeMenu()
    }

    // 输入区域裁到宠物命中框：画布四周透明部分不再吞鼠标。
    Loader {
        id: maskLoader
        source: "MaskBinder.qml"
        onLoaded: {
            item.targetWindow = win;
            item.pet = pet;
        }
        onStatusChanged: if (status === Loader.Error) {
            console.warn("[deepseek-pet] input mask unavailable, transparent area will block clicks");
        }
    }

    // 菜单是独立的 Layer Shell 窗口：鱼移动/换前台窗口后，右键菜单仍然在最上层。
    LayerPetMenuWindow {
        id: menuWindow
        screen: win.screen
        petSleeping: pet.sleeping
        hasSleep: pet.hasSleep
        onPlayRequested: function (name) { pet.playChosen(name); }
        onWalkRequested: function (name) { pet.walkChosen(name); }
        onIdleRequested: pet.playIdleOnce()
        onTurnRequested: pet.playTurn()
        onSleepRequested: pet.startSleep()
        onWakeRequested: pet.wake()
        onResetRequested: pet.resetPosition()
        onChimeRequested: pet.hourlyChime()
        onConfigureRequested: win.configureRequested()
    }

    function toggleMenu(px, py) {
        if (menuWindow.visible) {
            menuWindow.closeMenu();
            return;
        }
        var mw = menuWindow.width;
        var mh = menuWindow.height;
        var sw = pet.workWidth > 0 ? pet.workWidth : pet.screenWidth;
        var sh = Math.min(pet.workHeight > 0 ? pet.workHeight : pet.screenHeight,
                          pet.screenHeight - pet.bottomInset);
        var gx = pet.bodyX + px - mw / 2;
        var gy = pet.bodyY + pet.petHeight + 8;
        if (gy + mh > sh) {
            gy = pet.bodyY - mh - 8;
        }
        gx = Math.max(0, Math.min(gx, Math.max(0, sw - mw)));
        gy = Math.max(0, Math.min(gy, Math.max(0, sh - mh)));
        menuWindow.openAt(gx, gy);
    }

    onPetVisibleChanged: if (!petVisible) menuWindow.closeMenu()

    Component.onDestruction: {
        visible = false;
        menuWindow.closeMenu();
    }
}
