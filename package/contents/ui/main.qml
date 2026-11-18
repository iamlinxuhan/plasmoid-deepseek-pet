import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    Plasmoid.backgroundHints: "NoBackground"
    toolTipMainText: "DeepSeek 大肥鱼"
    toolTipSubText: "点一下互动 · 拖拽甩飞 · 右键换动作"

    fullRepresentation: Item {
        id: container
        implicitWidth: 560
        implicitHeight: 400
        Layout.minimumWidth: 160
        Layout.minimumHeight: 140
        Layout.preferredWidth: 560
        Layout.preferredHeight: 400

        Pet {
            anchors.fill: parent
            petSize: Plasmoid.configuration.petSize
            allowRoam: Plasmoid.configuration.allowRoam
            activityLevel: Plasmoid.configuration.activityLevel
            clickSoundEnabled: Plasmoid.configuration.clickSound
            throwPower: Plasmoid.configuration.throwPower
            gravity: Plasmoid.configuration.gravity
            startCorner: Plasmoid.configuration.startCorner
            onConfigureRequested: Plasmoid.internalAction("configure").trigger()
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
