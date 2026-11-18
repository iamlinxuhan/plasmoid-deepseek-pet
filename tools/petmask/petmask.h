#pragma once
#include <QObject>
#include <QWindow>
#include <QRegion>
#include <QRectF>
#include <QVariantList>
#include <QQmlExtensionPlugin>
#include <qqml.h>

class WindowMask : public QObject {
    Q_OBJECT
    Q_PROPERTY(QWindow *window READ window WRITE setWindow NOTIFY windowChanged)
    Q_PROPERTY(QVariantList rects READ rects WRITE setRects NOTIFY rectsChanged)
public:
    explicit WindowMask(QObject *parent = nullptr) : QObject(parent) {}
    QWindow *window() const { return m_window; }
    void setWindow(QWindow *w) {
        if (m_window == w) return;
        m_window = w;
        emit windowChanged();
        apply();
    }
    QVariantList rects() const { return m_rects; }
    void setRects(const QVariantList &r) {
        m_rects = r;
        emit rectsChanged();
        apply();
    }
private:
    void apply() {
        if (!m_window) return;
        QRegion region;
        for (const QVariant &v : m_rects) {
            const QRectF rf = v.toRectF();
            if (rf.isValid() && rf.width() > 0 && rf.height() > 0)
                region += rf.toRect();
        }
        m_window->setMask(region);
    }
    QWindow *m_window = nullptr;
    QVariantList m_rects;
signals:
    void windowChanged();
    void rectsChanged();
};

class PetMaskPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "org.qt-project.Qt.QQmlExtensionPlugin")
public:
    void registerTypes(const char *uri) override {
        qmlRegisterType<WindowMask>(uri, 1, 0, "WindowMask");
    }
};
