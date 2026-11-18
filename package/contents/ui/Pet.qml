import QtQuick
import QtMultimedia
import "AnimCatalog.js" as Catalog
import "AnimData.js" as AnimData
import "MoveData.js" as MoveData

/*
 * DeepSeek 大肥鱼本体。
 *
 * 行为完全本地：待机、随机动作、走动、点击回应、拖拽甩抛、落地 Q 弹、睡觉。
 * 不含任何联网、余额、对话或语音逻辑。
 */
Item {
    id: pet

    // ---------- 外部配置（由 main.qml 注入） ----------
    property int petSize: 420
    property bool allowRoam: true
    property int activityLevel: 1          // 0 安静 / 1 正常 / 2 活泼
    property bool clickSoundEnabled: true
    property real throwPower: 1.0
    property int gravity: 1400
    property int startCorner: 3            // 0 左上 / 1 右上 / 2 左下 / 3 右下
    property string petName: "DeepSeek 大肥鱼"

    signal configureRequested()
    // 供自动化测试/外部脚本检查菜单状态。
    property var contextMenu: menu

    // ---------- 尺寸与几何 ----------
    readonly property real petWidth: {
        var limit = petSize;
        if (width > 0) {
            limit = Math.min(limit, width);
        }
        if (height > 0) {
            limit = Math.min(limit, height * 16 / 9);
        }
        return Math.max(96, limit);
    }
    readonly property real petHeight: petWidth * 9 / 16
    // 角色脚底在 640×360 画布上的 y=330；画框比脚底多出这一截，让它能贴住容器底边。
    readonly property real feetPad: petHeight / 12
    // 命中框来自升级源 manifest.json 的 body_box [212, 60, 428, 330]（640×360 画布）。
    // 身体可以贴住容器边缘，画框探出去也没关系。
    readonly property real sideAllow: petWidth * 212 / 640

    readonly property real hitX: petWidth * 212 / 640
    readonly property real hitY: petHeight * 60 / 360
    readonly property real hitW: petWidth * 216 / 640
    readonly property real hitH: petHeight * 270 / 360

    // ---------- 位置与运动 ----------
    property real bodyX: 0
    property real bodyY: 0
    property bool initialized: false

    property bool pressing: false
    property bool dragging: false
    property bool flying: false
    property bool walking: false
    readonly property bool motionActive: flying || dragging

    property real flightVX: 0
    property real flightVY: 0
    property bool pendingAfterFlight: false

    property real dragTargetX: 0
    property real dragTargetY: 0
    property real dragVelocityX: 0
    property real dragVelocityY: 0

    property real walkStartX: 0
    property real walkTargetX: 0
    property real walkStartY: 0
    property string walkActionName: ""
    property int walkLoops: 1
    property int walkLoopsDone: 0
    property int lastWalkFrame: -1
    property var pendingWalk: null

    property real lastTick: 0

    // ---------- 动画状态 ----------
    property string facing: "left"
    property string currentAnim: ""
    property bool animOnce: true
    property bool endHandled: false
    property bool loadingAnim: false
    property bool frontIsA: true
    property int playToken: 0

    // ---------- 睡觉 ----------
    readonly property var sleepSets: Catalog.SLEEP_SETS
    readonly property bool hasSleep: sleepSets.length > 0
    property bool sleeping: false
    property string sleepPhase: ""
    property var currentSleepSet: null

    // ---------- 挤压 ----------
    property real squashScale: 1
    property real squashDepth: 0.55

    // ---------- 交互内部状态 ----------
    property var trail: []
    property real pressX: 0
    property real pressY: 0
    property real pressAnchorX: 0
    property real pressAnchorY: 0
    property real grabOffX: 0
    property real grabOffY: 0
    property real lastPressTime: 0
    property bool pressSling: false
    property real justDraggedUntil: 0

    Component.onCompleted: {
        initialized = true;
        resetPosition();
        playIdleOnce();
    }

    onWidthChanged: if (initialized) clampPlacement()
    onHeightChanged: if (initialized) clampPlacement()
    onPetWidthChanged: if (initialized) clampPlacement()

    // ---------- 画面 ----------
    Item {
        id: spriteHolder
        x: pet.bodyX
        y: pet.bodyY
        width: pet.petWidth
        height: pet.petHeight

        transform: Scale {
            origin.x: pet.petWidth / 2
            origin.y: pet.feetPad > 0 ? pet.petHeight * 330 / 360 : pet.petHeight
            xScale: 1
            yScale: pet.squashScale
        }

        AnimatedImage {
            id: imgA
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            smooth: true
            cache: false
            playing: false
            opacity: 0
            mirror: pet.facing === "right"
            onCurrentFrameChanged: pet.checkEnded(imgA)
            onStatusChanged: pet.spriteStatusChanged(imgA)
            Behavior on opacity { NumberAnimation { duration: 140 } }
        }

        AnimatedImage {
            id: imgB
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            smooth: true
            cache: false
            playing: false
            opacity: 0
            mirror: pet.facing === "right"
            onCurrentFrameChanged: pet.checkEnded(imgB)
            onStatusChanged: pet.spriteStatusChanged(imgB)
            Behavior on opacity { NumberAnimation { duration: 140 } }
        }

        MouseArea {
            id: hit
            x: pet.hitX
            y: pet.hitY
            width: pet.hitW
            height: pet.hitH
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            cursorShape: pet.dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor

            onPressed: function (mouse) {
                pet.beginPress(mouse);
            }
            onPositionChanged: function (mouse) {
                if (pet.pressing) {
                    pet.moveDrag(mouse);
                }
            }
            onReleased: function (mouse) {
                pet.finishPress(mouse);
            }
            onClicked: function (mouse) {
                if (mouse.button === Qt.RightButton) {
                    pet.openMenuAt(mouse);
                } else {
                    pet.handleClick();
                }
            }
        }
    }

    // ---------- 计时器 ----------
    Timer {
        id: tick
        interval: 16
        repeat: true
        running: pet.motionActive
        onRunningChanged: if (running) pet.lastTick = Date.now()
        onTriggered: pet.tick()
    }

    // 逐帧判定之外的兜底：万一某段动画不产生 currentFrame 信号，也保证能回到随机链。
    Timer {
        id: endFallback
        repeat: false
        onTriggered: {
            if (!pet.endHandled && pet.animOnce) {
                pet.endHandled = true;
                pet.handleEnded();
            }
        }
    }

    SequentialAnimation {
        id: squashSeq
        NumberAnimation {
            target: pet
            property: "squashScale"
            to: pet.squashDepth
            duration: 95
            easing.type: Easing.InQuad
        }
        NumberAnimation {
            target: pet
            property: "squashScale"
            to: 1.0
            duration: 125
            easing.type: Easing.OutBack
            easing.overshoot: 1.7
        }
    }

    SoundEffect {
        id: clickSound
        source: Qt.resolvedUrl("assets/sound/click-duck.wav")
        volume: 0.5
    }

    PetMenu {
        id: menu
        categories: Catalog.CATEGORIES
        moves: moveNames()
        clicks: Catalog.CLICKS
        petSleeping: pet.sleeping
        hasSleep: pet.hasSleep

        onPlayRequested: function (name) { pet.playChosen(name); }
        onWalkRequested: function (name) { pet.walkChosen(name); }
        onIdleRequested: pet.playIdleOnce()
        onTurnRequested: pet.playTurn()
        onSleepRequested: pet.startSleep()
        onWakeRequested: pet.wake()
        onResetRequested: pet.resetPosition()
        onConfigureRequested: pet.configureRequested()
    }

    // ---------- 动画播放 ----------
    function frontSprite() {
        return frontIsA ? imgA : imgB;
    }

    function pendingSprite() {
        return frontIsA ? imgB : imgA;
    }

    function playAnim(name, once) {
        if (!name || !AnimData.DATA[name]) {
            if (name) {
                console.warn("[deepseek-pet] unknown animation:", name);
            }
            return;
        }
        var target = pendingSprite();
        var token = ++playToken;
        currentAnim = name;
        animOnce = once;
        endHandled = false;
        loadingAnim = true;
        endFallback.stop();
        target.playing = false;
        target.opacity = 0;
        target.source = "";
        var url = Qt.resolvedUrl("assets/anim/" + name + ".webp");
        Qt.callLater(function () {
            if (token !== playToken) {
                return;
            }
            target.source = url;
            target.playing = true;
        });
    }

    function spriteStatusChanged(img) {
        if (img.status === Image.Error) {
            console.warn("[deepseek-pet] failed to load animation:", img.source);
            if (img === pendingSprite()) {
                loadingAnim = false;
            }
            if (img === pendingSprite() && currentAnim !== Catalog.IDLE[0]) {
                if (walking) {
                    walking = false;
                    pendingWalk = null;
                }
                playIdleOnce();
            }
            return;
        }
        if (img.status !== Image.Ready) {
            return;
        }
        if (img !== pendingSprite()) {
            return;
        }
        var outgoing = frontSprite();
        frontIsA = !frontIsA;
        loadingAnim = false;
        img.opacity = 1;
        outgoing.opacity = 0;
        outgoing.playing = false;
        endHandled = false;
        if (animOnce) {
            var dur = AnimData.duration(currentAnim);
            endFallback.interval = Math.max(200, dur * 1000 + 80);
            endFallback.restart();
        } else {
            endFallback.stop();
        }
    }

    function checkEnded(img) {
        if (img !== frontSprite()) {
            return;
        }
        if (walking && !loadingAnim) {
            updateWalkFrame(img);
        }
        if (!animOnce || endHandled || loadingAnim) {
            return;
        }
        if (img.frameCount > 1 && img.currentFrame >= img.frameCount - 1) {
            endHandled = true;
            endFallback.stop();
            handleEnded();
        }
    }

    function handleEnded() {
        if (sleeping) {
            if (sleepPhase === "start") {
                sleepPhase = "loop";
                if (currentSleepSet) {
                    playAnim(Catalog.pick(currentSleepSet.loop), false);
                }
            } else if (sleepPhase === "end") {
                sleeping = false;
                sleepPhase = "";
                currentSleepSet = null;
                playIdleOnce();
            }
            return;
        }
        if (dragging) {
            return;
        }
        if (flying) {
            pendingAfterFlight = true;
            return;
        }
        if (walking) {
            return;
        }
        if (Catalog.TURN.indexOf(currentAnim) >= 0) {
            facing = (facing === "left" ? "right" : "left");
            if (pendingWalk) {
                var plan = pendingWalk;
                pendingWalk = null;
                startWalkPlan(plan);
                return;
            }
            pickNext();
            return;
        }
        if (Catalog.DRAG.indexOf(currentAnim) >= 0 || Catalog.CLICKS.indexOf(currentAnim) >= 0) {
            playIdleOnce();
            return;
        }
        pickNext();
    }

    function playIdleOnce() {
        if (Catalog.IDLE.length === 0) {
            return;
        }
        playAnim(Catalog.pick(Catalog.IDLE, currentAnim), true);
    }

    function playTurn() {
        if (sleeping) {
            wake();
            return;
        }
        if (Catalog.TURN.length === 0) {
            return;
        }
        stopMotion();
        playAnim(Catalog.pick(Catalog.TURN, currentAnim), true);
    }

    function playChosen(name) {
        if (!name) {
            return;
        }
        if (sleeping) {
            wake();
            return;
        }
        stopMotion();
        if (Catalog.isNoMirror(name) && facing === "right") {
            // 含文字的动画不镜像，翻回正面。
            facing = "left";
        }
        playAnim(name, true);
    }

    function walkChosen(name) {
        if (sleeping) {
            wake();
            return;
        }
        stopMotion();
        if (!tryWalk(name)) {
            playIdleOnce();
        }
    }

    // ---------- 随机链 ----------
    function currentWeights() {
        var w = { idle: 30, turn: 10, move: 20 };
        if (activityLevel === 0) {
            w = { idle: 55, turn: 5, move: 5 };
        } else if (activityLevel === 2) {
            w = { idle: 10, turn: 10, move: 30 };
        }
        if (!allowRoam) {
            w.move = 0;
        }
        return w;
    }

    // 升级源的「朝内」判据：离中线超过 7% 滞回带才建议转向，避免中线附近反复翻面。
    function desiredInwardFacing() {
        var halfW = petWidth / 2;
        var margin = Catalog.MOVES.default.margin;
        var center = bodyX + halfW;
        var leftBound = margin + halfW - sideAllow;
        var rightBound = width - margin - halfW + sideAllow;
        var mid = (leftBound + rightBound) / 2;
        var band = Math.max(1, (rightBound - leftBound) * 0.07);
        if (center < mid - band) {
            return "right";
        }
        if (center > mid + band) {
            return "left";
        }
        return "";
    }

    function pickNext() {
        if (sleeping || dragging || flying || walking || pressing) {
            return;
        }
        var kind = Catalog.rollKind(Math.random(), currentWeights());
        if (kind === "idle") {
            playIdleOnce();
            return;
        }
        if (kind === "turn") {
            var want = desiredInwardFacing();
            if (Catalog.TURN.length > 0 && want !== "" && want !== facing) {
                playAnim(Catalog.pick(Catalog.TURN, currentAnim), true);
                return;
            }
            playIdleOnce();
            return;
        } else if (kind === "move") {
            if (tryWalk()) {
                return;
            }
        }
        var action = Catalog.pickCategoryAction(Catalog.CATEGORIES, Catalog.IDLE, facing, currentAnim);
        if (action.name) {
            playAnim(action.name, true);
        }
    }

    function moveNames() {
        var names = [];
        for (var i = 0; i < Catalog.MOVES.actions.length; i++) {
            names.push(Catalog.MOVES.actions[i].name);
        }
        return names;
    }

    // ---------- 走动 ----------
    // 升级源代码的移动模型：先按两侧剩余空间选方向，再把距离量化成整圈步态，
    // 位置完全由解码帧号 + move_strides 曲线推进，静帧段不走，脚不滑。
    function tryWalk(preferredName) {
        if (walking || flying || dragging || sleeping || pendingWalk) {
            return false;
        }
        var actions = Catalog.MOVES.actions;
        if (actions.length === 0) {
            return false;
        }
        var action = null;
        if (preferredName) {
            for (var i = 0; i < actions.length; i++) {
                if (actions[i].name === preferredName) {
                    action = actions[i];
                    break;
                }
            }
        } else {
            action = actions[Math.floor(Math.random() * actions.length)];
        }
        if (!action) {
            return false;
        }

        var halfW = petWidth / 2;
        var margin = Catalog.MOVES.default.margin;
        var centerX = bodyX + halfW;
        var leftBound = margin + halfW - sideAllow;
        var rightBound = width - margin - halfW + sideAllow;
        var roomLeft = centerX - leftBound;
        var roomRight = rightBound - centerX;
        var minDistance = 60;
        var maxDistance = 240;
        var dir;
        if (roomLeft >= minDistance && roomRight >= minDistance) {
            dir = Math.random() < 0.5 ? -1 : 1;
        } else if (roomLeft >= minDistance) {
            dir = -1;
        } else if (roomRight >= minDistance) {
            dir = 1;
        } else {
            return false;
        }
        var room = dir < 0 ? roomLeft : roomRight;
        var far = Math.min(maxDistance, room);
        if (far < minDistance) {
            return false;
        }
        var desired = Catalog.randomBetween(minDistance, far);
        var stride = MoveData.stride(action.name) * petWidth / 640;
        if (!(stride > 0)) {
            stride = 120 * petWidth / 640;
        }
        var loops = Math.max(1, Math.round(desired / stride));
        while (loops > 1 && loops * stride > room) {
            loops -= 1;
        }
        var distance = Math.min(loops * stride, room);
        var targetX = centerX + dir * distance - halfW;
        var face = dir > 0 ? "right" : "left";
        var plan = {
            actionName: action.name,
            dir: dir,
            loops: loops,
            targetX: targetX
        };
        if (face !== facing && Catalog.TURN.length > 0) {
            // 先播转向，翻完朝向再由 handleEnded 启动这段走位。
            pendingWalk = plan;
            playAnim(Catalog.pick(Catalog.TURN, currentAnim), true);
            return true;
        }
        facing = face;
        startWalkPlan(plan);
        return true;
    }

    function startWalkPlan(plan) {
        walkStartX = bodyX;
        walkTargetX = plan.targetX;
        walkStartY = bodyY;
        walkActionName = plan.actionName;
        walkLoops = Math.max(1, plan.loops);
        walkLoopsDone = 0;
        lastWalkFrame = -1;
        walking = true;
        playAnim(plan.actionName, false);
    }

    function updateWalkFrame(img) {
        if (img.frameCount <= 1) {
            return;
        }
        if (lastWalkFrame >= 0 && img.currentFrame < lastWalkFrame) {
            walkLoopsDone += 1;
        }
        lastWalkFrame = img.currentFrame;
        if (walkLoopsDone >= walkLoops) {
            bodyX = walkTargetX;
            bodyY = walkStartY;
            walking = false;
            clampPlacement();
            playIdleOnce();
            return;
        }
        var p = MoveData.curveProgress(walkActionName, img.currentFrame, img.frameCount);
        var ratio = Math.min(1, (walkLoopsDone + p) / walkLoops);
        bodyX = walkStartX + (walkTargetX - walkStartX) * ratio;
        bodyY = walkStartY;
    }

    // ---------- 拖拽与抛掷 ----------
    function beginPress(mouse) {
        if (mouse.button !== Qt.LeftButton) {
            return;
        }
        var now = Date.now();
        pressSling = (now - lastPressTime < 200);
        lastPressTime = now;
        pressing = true;
        dragging = false;
        var pt = hit.mapToItem(pet, mouse.x, mouse.y);
        pressX = pt.x;
        pressY = pt.y;
        grabOffX = pt.x - (bodyX + petWidth / 2);
        grabOffY = pt.y - (bodyY + petHeight / 2);
        pressAnchorX = bodyX + petWidth / 2;
        pressAnchorY = bodyY + petHeight / 2;
        dragTargetX = bodyX;
        dragTargetY = bodyY;
        dragVelocityX = 0;
        dragVelocityY = 0;
        trail = [{ t: now, x: pt.x, y: pt.y }];
        if (flying) {
            flying = false;
            flightVX = 0;
            flightVY = 0;
        }
        if (walking) {
            walking = false;
            pendingWalk = null;
        }
    }

    function moveDrag(mouse) {
        if (!pressing) {
            return;
        }
        var pt = hit.mapToItem(pet, mouse.x, mouse.y);
        var dx = pt.x - pressX;
        var dy = pt.y - pressY;
        if (!dragging && Math.sqrt(dx * dx + dy * dy) >= 6) {
            dragging = true;
            if (sleeping) {
                sleeping = false;
                sleepPhase = "";
                currentSleepSet = null;
            }
            playAnim(Catalog.pick(Catalog.DRAG, currentAnim), true);
        }
        if (dragging) {
            dragTargetX = pt.x - grabOffX - petWidth / 2;
            dragTargetY = pt.y - grabOffY - petHeight / 2;
            var now = Date.now();
            trail.push({ t: now, x: pt.x, y: pt.y });
            trail = trail.filter(function (s) { return now - s.t <= 200; });
        }
    }

    function finishPress(mouse) {
        if (!pressing) {
            return;
        }
        pressing = false;
        if (!dragging) {
            return;
        }
        dragging = false;
        justDraggedUntil = Date.now() + 150;
        trail = trail.filter(function (s) { return Date.now() - s.t <= 200; });

        // 弹弓：第二次快速按下后拖远再松手，力度看拉距而不是手速。
        if (pressSling) {
            var pullX = (bodyX + petWidth / 2) - pressAnchorX;
            var pullY = (bodyY + petHeight / 2) - pressAnchorY;
            var dist = Math.sqrt(pullX * pullX + pullY * pullY);
            if (dist > 12) {
                var power = dist / (petWidth * 0.6);
                var speed = 1200 * power * throwPower;
                var rad = Math.atan2(pullY, -pullX);
                startFlight(Math.cos(rad) * speed, -Math.sin(rad) * speed);
                return;
            }
        }

        var velocity = Catalog.estimateVelocity(trail, Date.now(), throwPower);
        if (velocity) {
            startFlight(velocity.vx, velocity.vy);
            return;
        }
        clampPlacement();
        playIdleOnce();
    }

    function handleClick() {
        if (Date.now() < justDraggedUntil) {
            return;
        }
        if (sleeping) {
            wake();
            return;
        }
        if (flying) {
            flying = false;
            flightVX = 0;
            flightVY = 0;
        }
        if (walking) {
            walking = false;
            pendingWalk = null;
        }
        if (clickSoundEnabled) {
            clickSound.play();
        }
        squash(0.55);
        playAnim(Catalog.pick(Catalog.CLICKS, currentAnim), true);
    }

    function startFlight(vx, vy) {
        if (sleeping) {
            return;
        }
        flying = true;
        pendingAfterFlight = false;
        flightVX = vx;
        flightVY = vy;
        playIdleOnce();
    }

    function stepFlight(dt) {
        var steps = Math.min(64, Math.max(1, Math.ceil(Math.max(Math.abs(flightVX), Math.abs(flightVY)) * dt / 8)));
        var sdt = dt / steps;
        var minX = -sideAllow;
        var maxX = width - petWidth + sideAllow;
        var maxY = height - petHeight + feetPad;
        var friction = Math.max(0, 1 - 2.5 * sdt);

        for (var i = 0; i < steps; i++) {
            flightVY += gravity * sdt;
            bodyX += flightVX * sdt;
            bodyY += flightVY * sdt;

            if (bodyX < minX) {
                bodyX = minX;
                flightVX = Math.abs(flightVX) > 40 ? -flightVX * 0.78 : 0;
                flightVY *= friction;
            } else if (bodyX > maxX) {
                bodyX = maxX;
                flightVX = Math.abs(flightVX) > 40 ? -flightVX * 0.78 : 0;
                flightVY *= friction;
            }

            if (bodyY < 0 && bodyY > -10000) {
                bodyY = 0;
                flightVY = Math.abs(flightVY) > 40 ? -flightVY * 0.78 : 0;
                flightVX *= friction;
            }

            if (bodyY > maxY) {
                bodyY = maxY;
                var impact = Math.abs(flightVY);
                flightVY = impact > 40 ? -impact * 0.78 : 0;
                flightVX *= friction;
                if (impact > 300) {
                    squash(landingSquash(impact));
                }
            }
        }

        if (bodyY >= maxY - 0.5 && Math.abs(flightVY) < 20 && Math.abs(flightVX) < 15) {
            flying = false;
            bodyY = maxY;
            flightVX = 0;
            flightVY = 0;
            if (pendingAfterFlight) {
                pendingAfterFlight = false;
                playIdleOnce();
            }
        }
    }

    function landingSquash(impact) {
        var t = Math.min(Math.max((Math.abs(impact) - 300) / 1200, 0), 1);
        return Math.min(0.8, 1 - t * (1 - 0.55));
    }

    function squash(depth) {
        squashDepth = depth;
        squashSeq.stop();
        squashScale = 1;
        squashSeq.start();
    }

    // ---------- 每帧驱动 ----------
    function tick() {
        var now = Date.now();
        var dt = Math.min(Math.max((now - lastTick) / 1000, 0), 0.05);
        lastTick = now;
        if (dragging) {
            var sdt = Math.min(dt, 1 / 30);
            dragVelocityX += ((dragTargetX - bodyX) * 200 - dragVelocityX * 30) * throwPower * sdt;
            dragVelocityY += ((dragTargetY - bodyY) * 200 - dragVelocityY * 30) * throwPower * sdt;
            bodyX += dragVelocityX * sdt;
            bodyY += dragVelocityY * sdt;
        } else if (flying) {
            stepFlight(dt);
        }
    }

    // ---------- 位置 ----------
    function clampPlacement() {
        var minX = -sideAllow;
        var maxX = Math.max(minX, width - petWidth + sideAllow);
        var maxY = Math.max(0, height - petHeight + feetPad);
        bodyX = Math.max(minX, Math.min(bodyX, maxX));
        bodyY = Math.max(0, Math.min(bodyY, maxY));
    }

    function resetPosition() {
        flying = false;
        walking = false;
        pendingWalk = null;
        dragging = false;
        pressing = false;
        var margin = 24;
        var maxY = Math.max(0, height - petHeight + feetPad);
        if (startCorner === 0) {
            bodyX = margin;
            bodyY = margin;
        } else if (startCorner === 1) {
            bodyX = width - petWidth - margin;
            bodyY = margin;
        } else if (startCorner === 2) {
            bodyX = margin;
            bodyY = maxY - margin;
        } else {
            bodyX = width - petWidth - margin;
            bodyY = maxY - margin;
        }
        clampPlacement();
        facing = "left";
        if (!sleeping) {
            playIdleOnce();
        }
    }

    function stopMotion() {
        flying = false;
        walking = false;
        pendingWalk = null;
        flightVX = 0;
        flightVY = 0;
        pendingAfterFlight = false;
    }

    // ---------- 睡觉 ----------
    function startSleep() {
        if (!hasSleep || sleeping) {
            return;
        }
        var set = Catalog.pickSleepSet();
        if (!set) {
            return;
        }
        currentSleepSet = set;
        stopMotion();
        pressing = false;
        dragging = false;
        sleeping = true;
        sleepPhase = "start";
        playAnim(Catalog.pick(set.start), true);
    }

    function wake() {
        if (!sleeping) {
            return;
        }
        if (sleepPhase === "start") {
            // 还没真正睡着就被叫醒：取消入睡，不播「起来」。
            sleeping = false;
            sleepPhase = "";
            currentSleepSet = null;
            playIdleOnce();
            return;
        }
        if (sleepPhase === "loop") {
            sleepPhase = "end";
            if (currentSleepSet) {
                playAnim(Catalog.pick(currentSleepSet.end), true);
            }
        }
    }

    // ---------- 菜单 ----------
    function openMenuAt(mouse) {
        var pt = hit.mapToItem(pet, mouse.x, mouse.y);
        menu.x = Math.max(0, Math.min(pt.x, Math.max(0, width - menu.width)));
        menu.y = Math.max(0, Math.min(pt.y, Math.max(0, height - menu.height)));
        menu.open();
    }
}
