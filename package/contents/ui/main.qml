import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root

    // 桌宠不应该有小组件卡片背景。
    Plasmoid.backgroundHints: "NoBackground"
    // 桌面组件重登后会被 Plasma 恢复成 compact 图标；强制始终用完整表示，
    // 才会实例化 fullRepresentation 里的 Layer Shell 窗口。
    preferredRepresentation: fullRepresentation
    toolTipMainText: "DeepSeek 大肥鱼"
    toolTipSubText: {
        if (layerReady) {
            return "点击锚点显示/隐藏 · 右键鱼身换动作 · 拖拽甩飞";
        }
        if (layerFailed) {
            return "缺少 qml6-module-org-kde-layershell，当前为桌面小组件模式";
        }
        return "点一下互动 · 拖拽甩飞 · 右键换动作";
    }

    // Layer Shell 只在 Wayland 可用；X11 或模块缺失时自动走桌面小组件模式。
    readonly property bool wantLayer: Qt.platform.pluginName.indexOf("wayland") === 0
    property bool layerReady: false
    property bool layerFailed: false
    readonly property bool layerLoading: wantLayer && !layerReady && !layerFailed
    property bool petVisible: true

    property bool monitorEnabled: Plasmoid.configuration.monitorEnabled
    property bool chimeEnabled: Plasmoid.configuration.chimeEnabled
    property bool strollEnabled: Plasmoid.configuration.strollEnabled
    property real cpuUsage: 0
    property real memUsage: 0
    property bool monitorBusy: false

    property var petConfig: ({
        petSize: Plasmoid.configuration.petSize,
        allowRoam: Plasmoid.configuration.allowRoam,
        activityLevel: Plasmoid.configuration.activityLevel,
        clickSoundEnabled: Plasmoid.configuration.clickSound,
        throwPower: Plasmoid.configuration.throwPower,
        gravity: Plasmoid.configuration.gravity,
        walkSpeed: Plasmoid.configuration.walkSpeed,
        startCorner: Plasmoid.configuration.startCorner,
        chimeEnabled: root.chimeEnabled,
        strollEnabled: root.strollEnabled,
        monitorEnabled: root.monitorEnabled,
        cpuUsage: root.cpuUsage,
        memUsage: root.memUsage
    })

    // 采样脚本在包内；用 sh 跑一次（约 1 秒），结果由 Plasma5Support 的
    // executable 数据源读回。只读 /proc，不联网。
    readonly property string sysmonCommand: {
        var url = Qt.resolvedUrl("assets/scripts/sysmon.sh").toString();
        var path = decodeURIComponent(url.replace(/^file:\/\//, ""));
        return "sh '" + path.replace(/'/g, "'\\''") + "'";
    }

    Plasma5Support.DataSource {
        id: monitorSource
        engine: "executable"
        connectedSources: []

        onNewData: function (source, data) {
            root.monitorBusy = false;
            monitorTimeout.stop();
            monitorSource.disconnectSource(root.sysmonCommand);
            var out = (data.stdout || "").trim();
            var parts = out.split(/\s+/);
            if (parts.length >= 2) {
                var cpu = parseFloat(parts[0]);
                var mem = parseFloat(parts[1]);
                if (!isNaN(cpu)) {
                    root.cpuUsage = Math.max(0, Math.min(100, cpu));
                }
                if (!isNaN(mem)) {
                    root.memUsage = Math.max(0, Math.min(100, mem));
                }
            }
        }
    }

    Timer {
        interval: 5000
        repeat: true
        running: root.monitorEnabled
        onTriggered: root.pollSystem()
    }

    Timer {
        id: monitorTimeout
        interval: 5000
        repeat: false
        onTriggered: {
            if (root.monitorBusy) {
                root.monitorBusy = false;
                monitorSource.disconnectSource(root.sysmonCommand);
            }
        }
    }

    function pollSystem() {
        if (!monitorEnabled || monitorBusy) {
            return;
        }
        monitorBusy = true;
        monitorTimeout.restart();
        monitorSource.connectSource(sysmonCommand);
    }

    onMonitorEnabledChanged: {
        if (!monitorEnabled) {
            monitorBusy = false;
            monitorTimeout.stop();
            monitorSource.disconnectSource(sysmonCommand);
        } else {
            pollSystem();
        }
    }

    Component.onCompleted: if (monitorEnabled) pollSystem()

    fullRepresentation: Item {
        id: container
        implicitWidth: root.layerReady ? 48 : 560
        implicitHeight: root.layerReady ? 48 : 400
        Layout.minimumWidth: root.layerReady ? 48 : 160
        Layout.minimumHeight: root.layerReady ? 48 : 140
        Layout.preferredWidth: implicitWidth
        Layout.preferredHeight: implicitHeight

        // 模块缺失时 Loader 进入 Error，保持 layerReady=false，下面的桌面 Pet 接管。
        Loader {
            id: layerLoader
            active: root.wantLayer
            source: "LayerPetWindow.qml"

            onLoaded: {
                item.petConfig = Qt.binding(function () { return root.petConfig; });
                item.petVisible = Qt.binding(function () { return root.petVisible; });
                item.configureRequested.connect(function () {
                    Plasmoid.internalAction("configure").trigger();
                });
                root.layerReady = true;
                root.layerFailed = false;
            }

            onStatusChanged: {
                if (status === Loader.Error) {
                    root.layerReady = false;
                    root.layerFailed = true;
                }
            }
        }

        // 桌面组件本身不画任何图标或点击热区：桌宠只由上面的 Layer Shell
        // 窗口呈现。这样壁纸中央不会多出一个应用图标，也不会吞掉桌面点击。
        // 需要隐藏/移除组件时，用桌面右键菜单或 Plasma 编辑模式。
        // 降级模式：X11 或 Layer Shell 模块缺失时才创建；Layer Shell 可用时
        // 这份 Pet 会被销毁，避免两个实例同时报时/散步/读占用。
        Component {
            id: fallbackPetComponent

            Pet {
                anchors.fill: parent
                petSize: Plasmoid.configuration.petSize
                allowRoam: Plasmoid.configuration.allowRoam
                activityLevel: Plasmoid.configuration.activityLevel
                clickSoundEnabled: Plasmoid.configuration.clickSound
                throwPower: Plasmoid.configuration.throwPower
                gravity: Plasmoid.configuration.gravity
                walkSpeed: Plasmoid.configuration.walkSpeed
                startCorner: Plasmoid.configuration.startCorner
                chimeEnabled: root.chimeEnabled
                strollEnabled: root.strollEnabled
                monitorEnabled: root.monitorEnabled
                cpuUsage: root.cpuUsage
                memUsage: root.memUsage
                onConfigureRequested: Plasmoid.internalAction("configure").trigger()
            }
        }

        Loader {
            anchors.fill: parent
            active: !root.wantLayer || root.layerFailed
            sourceComponent: fallbackPetComponent
        }
    }

    compactRepresentation: Item {
        implicitWidth: 48
        implicitHeight: 48

        Image {
            anchors.fill: parent
            anchors.margins: 4
            source: Qt.resolvedUrl("assets/images/logo.png")
            fillMode: Image.PreserveAspectFit
        }

        MouseArea {
            anchors.fill: parent
            onClicked: root.expanded = !root.expanded
        }
    }
}
