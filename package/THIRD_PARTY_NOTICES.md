# Third-party notices

## Bundled Layer Shell QML plugin

`contents/ui/layershell/` contains the QML plugin from KDE's
[layer-shell-qt](https://invent.kde.org/plasma/layer-shell-qt) (version 6.3.4,
Debian package `qml6-module-org-kde-layershell`, x86_64 build).

- Copyright: 2020–2023 Aleix Pol Gonzalez, 2018 Drew DeVault, and other contributors
- License: LGPL-3.0-only OR LGPL-3.0-or-later OR KDE Accepted LGPL (LGPL-3+KDEeV)
- Full license texts: `LICENSES/LGPL-3.txt` and `LICENSES/layer-shell-qt-copyright.txt`
- Source: https://invent.kde.org/plasma/layer-shell-qt

The plugin is loaded as a separate shared library by Qt's QML engine. It links to
the system `libLayerShellQtInterface.so.6` (package `layer-shell-qt`). On
architectures other than x86_64, or when `layer-shell-qt` is not installed, the
plugin fails to load and the applet automatically falls back to a normal Plasma
desktop widget.
