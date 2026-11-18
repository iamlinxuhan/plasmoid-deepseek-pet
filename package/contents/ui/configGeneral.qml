import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_petSize: sizeSpin.value
    property alias cfg_activityLevel: activityCombo.currentIndex
    property alias cfg_allowRoam: roamCheck.checked
    property alias cfg_clickSound: soundCheck.checked
    property alias cfg_throwPower: powerSlider.value
    property alias cfg_gravity: gravitySpin.value
    property alias cfg_startCorner: cornerCombo.currentIndex

    Kirigami.FormLayout {
        QQC2.SpinBox {
            id: sizeSpin
            from: 160
            to: 720
            stepSize: 10
            editable: true
            Kirigami.FormData.label: "宠物大小："
        }

        QQC2.ComboBox {
            id: activityCombo
            model: ["安静（多待机）", "正常", "活泼（爱动爱走）"]
            Kirigami.FormData.label: "活跃程度："
        }

        QQC2.CheckBox {
            id: roamCheck
            text: "允许自己在桌面范围内走动"
        }

        QQC2.CheckBox {
            id: soundCheck
            text: "点击时播放音效"
        }

        QQC2.Label {
            text: "拖拽手感"
            Kirigami.FormData.isSection: true
        }

        QQC2.Slider {
            id: powerSlider
            from: 0.5
            to: 2.0
            stepSize: 0.1
            Kirigami.FormData.label: "抛掷力度：" + value.toFixed(1)
        }

        QQC2.SpinBox {
            id: gravitySpin
            from: 0
            to: 4000
            stepSize: 100
            editable: true
            Kirigami.FormData.label: "重力："
        }

        QQC2.Label {
            text: "0 = 无重力，宠物被甩出后会一直飘；默认 1400。"
            font: Kirigami.Theme.smallFont
            opacity: 0.7
            Layout.maximumWidth: Kirigami.Units.gridUnit * 18
            wrapMode: Text.Wrap
        }

        QQC2.Label {
            text: "初始位置"
            Kirigami.FormData.isSection: true
        }

        QQC2.ComboBox {
            id: cornerCombo
            model: ["左上角", "右上角", "左下角", "右下角"]
            Kirigami.FormData.label: "回到原位时出现在："
        }
    }
}
