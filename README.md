# DeepSeek 大肥鱼 · KDE Plasma 桌宠

一只住在 KDE Plasma 桌面上的 DeepSeek 大肥鱼。动画与行为参考独立桌面版 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（以及它上游的 [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet)）；本项目把其中**纯桌宠**的部分移植成 Plasma 6 plasmoid，不安装 `dsh`、不依赖 Python/Node/npm，也不需要任何模型 API。

> 安装包：`dist/deepseek大肥鱼.plasmoid`

## 功能

- **108 段透明动画**：待机呼吸、伸展、打哈欠、玩魔方、吃东西、节日动作、工作状态姿态……全部按权重首尾衔接，随机播放。
- **随机链**：待机 / 转向 / 自主走动 / 随机小动作，四类按权重抽取；转向动画播完后才会翻转朝向。
- **不走滑的走路**：采用升级源的逐帧位移曲线（`move_strides.json`），位移只跟解码帧号走；先按两侧剩余空间选方向，距离量化成整圈步态，静帧段原地不动。
- **文字动画不镜像**：`text_clips.json` 里 6 段带可读文字的动画，在面向右时跳过随机抽取；右键点播时会先翻回正面。
- **点击回应**：点一下随机播一段回应动画，带 Q 弹挤压与点击音效。
- **拖拽甩抛**：拖起来跟着指针走，松手按手速甩出去；撞到容器边缘会反弹、摩擦、落地压扁回弹。
- **弹弓**：快速二次按下并拖远再松手，按拉距把宠物弹出去（方向和拉的反方向）。
- **睡觉**：右键「让它睡觉」播放入睡 → 睡眠循环，点击或右键「叫醒它」播放起床动画。
- **右键菜单**：按分类点播任意动画、走动、点击回应、睡觉、回到原位、打开设置。
- **多开**：同一个桌面小组件可以添加多次，每只鱼各自独立走动、睡觉、被拖拽。
- **可调配置**：大小、活跃程度、是否自主走动、点击音效、抛掷力度、重力、初始角落。

## 已移除的原插件功能

为了去掉 API 费用与外部依赖，以下内容没有移植：

- 余额 / 额度查询与余额动画（`余额-*` 素材已删除）
- AI 对话、碎碎念、长期记忆、表情包配图（升级源里有，本项目未移植）
- 语音合成（TTS）与语音识别（STT）
- 天气、待办事项、系统通知
- DSH 会话工作状态联动、HTTP API、Cordis 服务、Electron 桌面模式
- npm 发布、Node 依赖、`dsh` 插件包结构

所有动画与交互都在本地完成，离线可用。

## 安装

### 方式一：命令行

```bash
kpackagetool6 -t Plasma/Applet -i dist/deepseek大肥鱼.plasmoid
```

升级已安装版本：

```bash
kpackagetool6 -t Plasma/Applet -u dist/deepseek大肥鱼.plasmoid
```

卸载：

```bash
kpackagetool6 -t Plasma/Applet -r com.github.iamlinxuhan.deepseekpet
```

### 方式二：图形界面

右键桌面 → **添加组件** → **从文件安装组件**，选择 `deepseek大肥鱼.plasmoid`；然后在组件列表里搜索「DeepSeek 大肥鱼」并拖到桌面。

安装后如果没有立刻出现，可以重新登录一次 Plasma 会话，或执行 `kquitapp6 plasmashell && kstart plasmashell`。

## 使用

| 操作 | 效果 |
| --- | --- |
| 左键点一下 | 点击回应 + Q 弹 + 音效 |
| 按住拖动 | 抓起并跟随指针 |
| 拖动后松手 | 按手速甩抛；慢慢放下则原地站好 |
| 快速二次按下并拖远 | 弹弓发射 |
| 右键 | 换动作 / 走动 / 睡觉 / 回到原位 / 设置 |
| 滚轮（可选） | 暂未绑定 |

> 小组件会占据一块桌面区域。想让鱼走得更远，把小组件拉大即可；宠物大小在设置里单独调整。
> 拖动到小组件边界外时会被窗口裁掉，这是 Plasma 桌面部件的限制。

## 配置

右键 → **设置…**，或在组件上悬停后点齿轮：

- **宠物大小**：160–720 px（画框宽度，角色本体约 37.5%）
- **活跃程度**：安静 / 正常 / 活泼
- **允许自主走动**：关闭后只在原地待机与随机动作
- **点击音效**
- **抛掷力度**：0.5–2.0
- **重力**：0 = 无重力（会一直飘），默认 1400
- **初始角落**：左上 / 右上 / 左下 / 右下

## 兼容性

- KDE Plasma 6.0+（开发环境：Plasma 6.3.6 / Qt 6.8 / Debian 13）
- 需要 Qt 的 WebP 图片插件（`libqwebp.so`，Debian/Ubuntu 的 `qt6-image-formats-plugins` 或发行版等价包；Plasma 桌面通常已自带）
- 动画格式为 384×216 带 Alpha 的动画 WebP，由 Qt `AnimatedImage` 解码；不依赖 QtMultimedia 视频透明，因此 Wayland / X11 表现一致

## 从源码构建

```bash
# 生成 .plasmoid
./tools/build.sh

# 安装
./tools/install.sh
```

构建产物在 `dist/deepseek大肥鱼.plasmoid`。`package/` 是可直接安装的 KPackage 目录。

### 重新生成动画素材

仓库已包含转换好的 108 段 WebP。若要重新转码，先把升级源克隆到 `reference/`：

```bash
git clone --depth 1 https://github.com/MerZlin/dsh-pet-indesktop.git reference/dsh-pet-indesktop
# 睡眠动画与「吃白饭」玩法素材仍在原始 dsh-pet 里，可选：
git clone --depth 1 https://github.com/PC2005-cloud/dsh-pet.git reference/dsh-pet-src

./tools/convert-all.sh
python3 tools/gen-animdata.py
python3 tools/gen-movedata.py
```

升级源与原始仓库的 104 个同名视频里 103 个逐字节一致；本项目的升级点主要是它的 `move_strides.json`（逐帧步态曲线）、`text_clips.json`（不镜像清单）和 `manifest.json`（身体/头部命中框）。睡眠与吃白饭素材来自原始仓库——升级源没有这两组。

转码参数：`384×216`、20 fps、WebP 有损 q50，并把素材背景的 1/255 alpha 归零。`tools/gen-animdata.py` 会重新生成 `package/contents/ui/AnimData.js`（每段动画的帧数与时长）。

## 目录结构

```
package/
  metadata.json                 Plasma 组件元数据
  contents/
    config/main.xml             KConfig 配置项
    config/config.qml           设置分类
    ui/main.qml                 PlasmoidItem 入口
    ui/Pet.qml                  桌宠状态机、物理与交互
    ui/PetMenu.qml              右键菜单
    ui/configGeneral.qml        设置页
    ui/AnimCatalog.js           动画池 / 权重 / 不镜像清单 / 松手初速
    ui/AnimData.js              动画帧数与时长（自动生成）
    ui/MoveData.js              逐帧步态位移曲线（自动生成）
    ui/assets/anim/*.webp       108 段透明动画
    ui/assets/sound/           点击音效
    ui/assets/images/logo.png  图标
tools/                          转码、构建、安装脚本
```

## 致谢

- 独立桌面升级版：[MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT）——逐帧步态曲线、不镜像清单、命中框与行为参考
- 原始项目与全部美术素材：[PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet)（MIT）
- 本项目只做 KDE Plasma 移植与本地化，动画素材版权随上游 MIT 许可

## 许可证

MIT，见 [LICENSE](LICENSE)。
