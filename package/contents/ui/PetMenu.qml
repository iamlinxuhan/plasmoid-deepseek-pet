import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components 3.0 as PlasmaComponents3

/*
 * 两栏式动作菜单：左侧分类、右侧该分类下的动画，底部是常用命令。
 * 没有用 QQC2/Plasma 的 Menu 子菜单——Qt 6.8 里 MenuItem.subMenu 是只读的。
 */
QQC2.Popup {
    id: menu

    property var categories: []
    property var moves: []
    property var clicks: []
    property bool petSleeping: false
    property bool hasSleep: true
    property int categoryIndex: 0

    property var allCategories: {
        var out = [];
        for (var i = 0; i < categories.length; i++) {
            out.push({ id: categories[i].id, actions: categories[i].actions });
        }
        out.push({ id: "走动", actions: moves });
        out.push({ id: "点击回应", actions: clicks });
        return out;
    }

    component MenuButton: PlasmaComponents3.Button {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 1.9
        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 0.9
    }

    signal playRequested(string name)
    signal walkRequested(string name)
    signal idleRequested()
    signal turnRequested()
    signal sleepRequested()
    signal wakeRequested()
    signal resetRequested()
    signal chimeRequested()
    signal configureRequested()

    width: Kirigami.Units.gridUnit * 28
    height: Kirigami.Units.gridUnit * 24
    padding: 0
    modal: false
    focus: true
    closePolicy: QQC2.Popup.CloseOnEscape | QQC2.Popup.CloseOnPressOutside

    onAllCategoriesChanged: if (categoryIndex >= allCategories.length) categoryIndex = 0

    background: Kirigami.ShadowedRectangle {
        color: Kirigami.Theme.backgroundColor
        radius: Kirigami.Units.smallSpacing
        border.width: 1
        border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.16)
        shadow.size: 18
        shadow.color: Qt.rgba(0, 0, 0, 0.35)
        shadow.yOffset: 4
    }

    contentItem: ColumnLayout {
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
                    text: modelData
                    onClicked: {
                        menu.playRequested(modelData);
                        menu.close();
                    }
                }

                PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {}
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
                onClicked: { menu.idleRequested(); menu.close(); }
            }
            MenuButton {
                text: "转身"
                onClicked: { menu.turnRequested(); menu.close(); }
            }
            MenuButton {
                text: "回原位"
                onClicked: { menu.resetRequested(); menu.close(); }
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
                    menu.close();
                }
            }
            MenuButton {
                text: "报时"
                onClicked: { menu.chimeRequested(); menu.close(); }
            }
            MenuButton {
                text: "设置"
                onClicked: { menu.configureRequested(); menu.close(); }
            }
        }
    }
}
