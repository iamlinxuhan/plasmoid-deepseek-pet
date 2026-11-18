"""大肥鱼宣传片时间轴（与配乐共用）。"""

SCENES = [
    ("intro", 5.0),
    ("desktop", 9.0),
    ("anims", 11.0),
    ("throw", 10.0),
    ("menu", 9.0),
    ("outro", 9.0),
]
TR = 0.7

START = []
_t = 0.0
for _i, (_name, _dur) in enumerate(SCENES):
    START.append(round(_t, 3))
    _t += _dur - (TR if _i < len(SCENES) - 1 else 0.0)
DUR = round(_t, 3)

def cues():
    return {
        "dur": DUR,
        "fps": 60,
        "bpm": 92,
        "scenes": [
            {"name": n, "start": START[i], "dur": d}
            for i, (n, d) in enumerate(SCENES)
        ],
        "trans": [round(START[i] + SCENES[i][1] - TR, 3) for i in range(len(SCENES) - 1)],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(cues(), ensure_ascii=False, indent=1))
    print("DUR", DUR)
