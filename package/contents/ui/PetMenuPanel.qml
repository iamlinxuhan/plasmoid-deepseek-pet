import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components 3.0 as PlasmaComponents3
import "AnimCatalog.js" as Catalog

/*
 * 菜单本体（纯 Item）。普通桌面组件里套在 QQC2.Popup 里；
 * Layer Shell 模式里放进独立的 LayerPetMenuWindow，保证菜单自己也在最上层。
 */
Rectangle {
    id: menu

    property bool petSleeping: false
    property bool hasSleep: true
    property int categoryIndex: 0
    property var actionListRef: actionList
    property var allCategories: []

    signal playRequested(string name)
    signal walkRequested(string name)
    signal idleRequested()
    signal turnRequested()
    signal sleepRequested()
    signal wakeRequested()
    signal resetRequested()
    signal chimeRequested()
    signal configureRequested()
    signal dismissRequested()

    width: Kirigami.Units.gridUnit * 28
    height: Kirigami.Units.gridUnit * 32
    color: "transparent"
    focus: true
    Keys.onEscapePressed: menu.dismissRequested()

    component MenuButton: PlasmaComponents3.Button {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 1.9
        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 0.9
    }

    Component.onCompleted: rebuild()

    function rebuild() {
        var out = [];
        for (var i = 0; i < Catalog.CATEGORIES.length; i++) {
            out.push({ id: Catalog.CATEGORIES[i].id, actions: Catalog.CATEGORIES[i].actions });
        }
        var moves = [];
        for (var j = 0; j < Catalog.MOVES.actions.length; j++) {
            moves.push(Catalog.MOVES.actions[j].name);
        }
        out.push({ id: "走动", actions: moves });
        out.push({ id: "点击回应", actions: Catalog.CLICKS });
        allCategories = out;
        if (categoryIndex >= out.length) {
            categoryIndex = 0;
        }
    }

    function resetView() {
        categoryIndex = 0;
        resetTimer.restart();
    }

    Timer {
        id: resetTimer
        interval: 60
        repeat: false
        onTriggered: {
            categoryList.positionViewAtBeginning();
            actionList.contentY = 0;
        }
    }

    Kirigami.ShadowedRectangle {
        anchors.fill: parent
        color: Kirigami.Theme.backgroundColor
        radius: Kirigami.Units.smallSpacing
        border.width: 1
        border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.16)
        shadow.size: 18
        shadow.color: Qt.rgba(0, 0, 0, 0.35)
        shadow.yOffset: 4
    }

    Item {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 6
        width: 34
        height: 34
        z: 20

        Rectangle {
            anchors.fill: parent
            radius: 17
            color: closeArea.containsMouse ? Qt.rgba(Kirigami.Theme.textColor.r,
                                                       Kirigami.Theme.textColor.g,
                                                       Kirigami.Theme.textColor.b, 0.10)
                                            : "transparent"
        }
        Text {
            anchors.centerIn: parent
            text: "×"
            color: Kirigami.Theme.textColor
            opacity: 0.75
            font.pixelSize: 20
        }
        MouseArea {
            id: closeArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: menu.dismissRequested()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            ListView {
                id: categoryList
                Layout.preferredWidth: Kirigami.Units.gridUnit * 7
                Layout.fillHeight: true
                clip: true
                model: menu.allCategories
                currentIndex: menu.categoryIndex

                delegate: PlasmaComponents3.ItemDelegate {
                    width: ListView.view.width
                    height: 40
                    text: modelData.id
                    checkable: true
                    checked: index === menu.categoryIndex
                    onClicked: menu.categoryIndex = index
                }

                PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {}
            }

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: Kirigami.Theme.textColor
                opacity: 0.14
            }

            ListView {
                id: actionList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: menu.allCategories[menu.categoryIndex] ? menu.allCategories[menu.categoryIndex].actions : []

                delegate: PlasmaComponents3.ItemDelegate {
                    width: ListView.view.width
                    height: 36
                    text: modelData
                    onClicked: {
                        menu.playRequested(modelData);
                        menu.dismissRequested();
                    }
                }

                onModelChanged: Qt.callLater(function () { contentY = 0; })

                PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {
                    policy: PlasmaComponents3.ScrollBar.AlwaysOn
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Kirigami.Theme.textColor
            opacity: 0.14
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            MenuButton {
                text: "待机"
                onClicked: { menu.idleRequested(); menu.dismissRequested(); }
            }
            MenuButton {
                text: "转身"
                onClicked: { menu.turnRequested(); menu.dismissRequested(); }
            }
            MenuButton {
                text: "回原位"
                onClicked: { menu.resetRequested(); menu.dismissRequested(); }
            }
            MenuButton {
                text: menu.petSleeping ? "叫醒" : "睡觉"
                visible: menu.hasSleep
                onClicked: {
                    if (menu.petSleeping) {
                        menu.wakeRequested();
                    } else {
                        menu.sleepRequested();
                    }
                    menu.dismissRequested();
                }
            }
            MenuButton {
                text: "报时"
                onClicked: { menu.chimeRequested(); menu.dismissRequested(); }
            }
            MenuButton {
                text: "设置"
                onClicked: { menu.configureRequested(); menu.dismissRequested(); }
            }
        }
    }
}
