.pragma library

// 桌宠动画目录：从原 dsh-pet 的 animations 配置整理而来，
// 只保留桌宠自身行为，余额、AI 对话、语音、碎碎念等联网功能全部移除。

var IDLE = ["待机呼吸休闲"];
var TURN = ["东张西望"];
var DRAG = ["被鼠标拖拽悬空反馈"];
var CLICKS = [
    "点击回应-开心跃动",
    "点击回应-害羞惊讶",
    "点击回应-傲娇生气",
    "点击回应-挠痒咯咯笑",
    "点击回应-元气挥手"
];

var MOVES = {
    default: { minDist: 60, maxDist: 240, margin: 20, leadSec: 2, tailSec: 2 },
    actions: [
        { name: "螃蟹走路" },
        { name: "原地漂浮踏步", params: { minDist: 40, maxDist: 120 } },
        { name: "原地左转奔跑", params: { minDist: 120, maxDist: 320, leadSec: 1.75, tailSec: 4.8 } }
    ]
};

// weight = 随机链中的出现权重；noMirror = 带文字，镜像后会颠倒，
// 宠物面向右（素材被镜像）时不参与随机抽取。weight 0 的条目只出现在菜单里。
var CATEGORIES = [
    { id: "小动作", weight: 20, actions: [
        "悠闲哼歌", "超大伸懒腰", "原地敲击桌面互动", "原地重力下蹲压缩", "哈欠连天",
        "原地小憩沉眠", "女仆屈膝礼仪", "被吓一跳", "小幅度原地360度旋转展示",
        "偷吃零食被抓住", "用鲸鱼尾巴拍打地面", "打瞌睡被惊醒", "照镜子", "整体换装试色",
        "轻快记录", "写代码", "摇扇纳凉", "晨间刷牙",
        "碎碎念-擦桌碎碎念", "碎碎念-发呆碎碎念", "碎碎念-对屏碎碎念",
        "工作状态-思考冒泡", "工作状态-忙碌点按", "工作状态-清点归档",
        "工作状态-原地踱步张望", "工作状态-雀跃庆祝", "工作状态-垂头叹气冒汗",
        "开心小跑", "侧身急躁跑", "期待开饭"
    ] },
    { id: "玩耍", weight: 20, actions: [
        "原地专心玩魔方", "原地蹲下玩玩具汽车", "鲸鱼吐泡泡特效", "原地跳跃抓碎头顶物品",
        "玩游戏气急败坏", "玩水枪", "小提琴演奏", "蓝鲸现世", "优雅女仆舞", "轻快摇摆舞",
        "可爱宅舞", "吹气球", "动物环绕", "放风筝", "拆礼物", "变鸽子", "扑克魔术",
        "抽陀螺", "吹笛子", "蝴蝶蜜蜂环绕头顶开花", "撸猫", "凭空生花", "骑木马",
        "三球抛接", "踢毽子", "下五子棋", "荡秋千"
    ] },
    { id: "吃什么", weight: 16, actions: [
        "吃白饭", "大口吃零食", "吃Token", "吃早餐", "吃午餐", "吃晚餐", "吃冰淇淋融化",
        "吃大闸蟹", "吃糖葫芦", "吃长寿面", "吃西瓜", "涮火锅", "吃饭·碗饭"
    ] },
    { id: "时节", weight: 14, actions: [
        "被落叶淹没", "中秋赏月吃月饼", "堆雪人", "放烟花", "吃粽子", "吃年糕", "吃青团",
        "吃腊八粥", "吃重阳糕", "收红包", "写福字", "穿针乞巧", "舞狮头", "讨糖南瓜灯",
        "插茱萸赏菊", "放河灯", "萌化小幽灵", "装点圣诞树", "放孔明灯", "吃汤圆", "吃饺子"
    ] },
    { id: "文字", weight: 10, noMirror: true, actions: [
        "是啊，吃什么", "深度思考碎碎念"
    ] }
];

var SLEEP_SETS = [
    { start: ["睡觉-开始"], loop: ["睡觉-循环"], end: ["睡觉-起来"] }
];

var WEIGHTS = { idle: 30, turn: 10, move: 20 };

// 升级源 text_clips.json：含可读文字，面向右（素材被镜像）时不播，否则文字是反的。
var NO_MIRROR = [
    "是啊，吃什么",
    "写代码",
    "写福字",
    "收红包",
    "吃Token",
    "深度思考碎碎念"
];

function isNoMirror(name) {
    return NO_MIRROR.indexOf(name) >= 0;
}

function pick(pool, exclude) {
    if (!pool || pool.length === 0) {
        return "";
    }
    var src = pool;
    if (exclude !== undefined && exclude !== "" && pool.length > 1) {
        var filtered = pool.filter(function (name) { return name !== exclude; });
        if (filtered.length > 0) {
            src = filtered;
        }
    }
    return src[Math.floor(Math.random() * src.length)];
}

function randomBetween(min, max) {
    return min + Math.random() * (max - min);
}

function rollKind(roll, weights) {
    var idle = weights.idle || 0;
    var turn = weights.turn || 0;
    var move = weights.move || 0;
    var total = Math.max(0, Math.min(100, idle + turn + move));
    if (roll < idle / 100) {
        return "idle";
    }
    if (roll < (idle + turn) / 100) {
        return "turn";
    }
    if (roll < total / 100) {
        return "move";
    }
    return "action";
}

function eligibleActions(category, facing) {
    if (facing !== "right") {
        return category.actions;
    }
    var out = category.actions.filter(function (name) { return !isNoMirror(name); });
    return out.length > 0 ? out : category.actions;
}

function pickWeightedCategory(categories, facing) {
    var cats = categories.filter(function (c) {
        if (!c.actions || c.actions.length === 0 || !(c.weight > 0)) {
            return false;
        }
        if (facing === "right") {
            // 整类都是文字动画时，面向右直接跳过这一类。
            return c.actions.some(function (name) { return !isNoMirror(name); });
        }
        return true;
    });
    if (cats.length === 0) {
        cats = categories.filter(function (c) {
            return c.actions && c.actions.length > 0 && c.weight > 0;
        });
    }
    if (cats.length === 0) {
        return null;
    }
    var total = 0;
    for (var i = 0; i < cats.length; i++) {
        total += cats[i].weight;
    }
    var t = Math.random() * total;
    for (var j = 0; j < cats.length; j++) {
        t -= cats[j].weight;
        if (t <= 0) {
            return cats[j];
        }
    }
    return cats[cats.length - 1];
}

function pickCategoryAction(categories, idlePool, facing, current) {
    var cat = pickWeightedCategory(categories, facing);
    if (!cat) {
        return { id: "IDLE", name: pick(idlePool, current) };
    }
    return { id: cat.id, name: pick(eligibleActions(cat, facing), current) };
}

function pickSleepSet() {
    return pick(SLEEP_SETS);
}

function mergeParams(action) {
    var out = {};
    for (var k in MOVES.default) {
        out[k] = MOVES.default[k];
    }
    if (action && action.params) {
        for (var p in action.params) {
            out[p] = action.params[p];
        }
    }
    return out;
}

// 鼠标轨迹估算松手初速，参数与 dsh-pet 的 shared/physics/release.ts 一致。
function estimateVelocity(trail, now, throwPower) {
    if (!trail || trail.length === 0) {
        return null;
    }
    var last = trail[trail.length - 1];
    if (now - last.t > 150) {
        return null;
    }
    var win = trail.filter(function (s) { return now - s.t <= 150; });
    if (win.length < 2) {
        return null;
    }
    var t0 = win[0].t;
    var x0 = win[0].x;
    var y0 = win[0].y;
    var t1 = win[win.length - 1].t;
    var x1 = win[win.length - 1].x;
    var y1 = win[win.length - 1].y;
    var spanMs = t1 - t0;
    if (spanMs < 20) {
        return null;
    }
    var baseVx = (x1 - x0) / spanMs * 1000;
    var baseVy = (y1 - y0) / spanMs * 1000;
    var baseSpeed = Math.sqrt(baseVx * baseVx + baseVy * baseVy);
    if (baseSpeed < 1e-6) {
        return null;
    }
    var segSpeeds = [];
    var px = x0;
    var py = y0;
    var pt = t0;
    for (var i = 1; i < win.length; i++) {
        var s = win[i];
        var dt = s.t - pt;
        if (dt >= 8) {
            segSpeeds.push({
                speed: Math.sqrt((s.x - px) * (s.x - px) + (s.y - py) * (s.y - py)) / dt * 1000,
                tEnd: s.t
            });
            px = s.x;
            py = s.y;
            pt = s.t;
        }
    }
    var peakSpeed = baseSpeed;
    for (var j = 0; j < segSpeeds.length; j++) {
        if (segSpeeds[j].speed > peakSpeed) {
            peakSpeed = segSpeeds[j].speed;
        }
    }
    var accel = 0;
    if (segSpeeds.length >= 2) {
        var lastSeg = segSpeeds[segSpeeds.length - 1];
        var firstSeg = segSpeeds[0];
        accel = (lastSeg.speed - firstSeg.speed) /
            Math.max((lastSeg.tEnd - firstSeg.tEnd) / 1000, 0.02);
    }
    var beforeClamp = (0.5 * baseSpeed + 0.5 * peakSpeed) *
        (1 + Math.min(Math.max(accel, 0) / 8000, 1) * 0.6);
    var speed = 3600 * (1 - Math.exp(-beforeClamp / 3600)) * throwPower;
    if (speed < 500) {
        return null;
    }
    return { vx: baseVx / baseSpeed * speed, vy: baseVy / baseSpeed * speed };
}
