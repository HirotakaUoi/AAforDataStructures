"""
algorithms.py – AAforDataStructures
データ構造アニメーション (Ch.3: vector / Ch.4: 連結リスト)

オブジェクト種別:
  array1d_cells  – 正方形セル配列（主力）
"""

from random import randint

# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------

def _f(objects, texts=None, finished=False, found=None, text_position="top"):
    return {"objects": objects, "texts": texts or [], "finished": finished,
            "found": found, "text_position": text_position}

def _c(id, values, label="", hl=None, fills=None, ptr=None,
       watchman=None, target=None, weight=1):
    return {
        "id": id, "type": "array1d_cells",
        "values": list(values), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "fills": fills or [], "pointer": ptr,
        "watchman_index": watchman, "target": target,
        "weight": weight,
    }

def _ptr(index, label, color="#cc00cc"):
    return {"index": index, "label": str(label), "color": color}


# ===========================================================================
# Ch.3: vector / イテレータ (type: "misc")
# ===========================================================================

def vector_capacity(n, **kwargs):
    """Sample3_1: vector の push_back で capacity が倍増する様子を可視化"""
    N = max(4, min(int(n), 20))
    seed_vals = [5, 2, 7, 1, 5, 10, 100, 25, 99]
    push_vals = (seed_vals + [randint(1, 99) for _ in range(max(0, N - len(seed_vals)))])[:N]

    def sim_cap(size):
        if size == 0:
            return 0
        c = 1
        while c < size:
            c *= 2
        return c

    base = [{"message": f"vector の capacity と size の変化  push_back × {N}  (Sample3_1)",
             "color": "white"}]
    vals = []
    cap = 0

    yield _f([_c("vec", [0], "vector (空)", hl={0: "#1a2a1a"})],
             base + [{"message": "vector を生成  size=0,  capacity=0", "color": "lightgreen"}])

    for v in push_vals:
        vals.append(v)
        new_cap = sim_cap(len(vals))
        cap_grew = new_cap > cap
        cap = new_cap

        display = list(vals) + [0] * (cap - len(vals))
        hl = {i: "#1e2e1e" for i in range(len(vals), cap)}   # unused slots: 暗色
        hl[len(vals) - 1] = "yellow"                          # 追加した要素: 黄

        color = "orange" if cap_grew else "lightgreen"
        msg = f"push_back({v})  →  size={len(vals)},  capacity={cap}"
        if cap_grew:
            msg += "  ← 再確保!"

        yield _f([_c("vec", display, f"vector  size={len(vals)},  capacity={cap}", hl=hl)],
                 base + [{"message": msg, "color": color}])

    display = list(vals) + [0] * (cap - len(vals))
    hl = {i: "#1e2e1e" for i in range(len(vals), cap)}
    yield _f([_c("vec", display, f"vector  size={len(vals)},  capacity={cap}", hl=hl)],
             base + [{"message": f"完了: size={len(vals)},  capacity={cap}", "color": "#44aa44"}],
             finished=True)


def vector_ops(n, **kwargs):
    """Sample3_2: vector の push_back / erase / insert / reverse 操作列"""
    base = [{"message": "vector 操作列  (Sample3_2)", "color": "white"}]
    v = [2, 3, 4, 5, 6]

    def frame(extra_hl=None, msg="", color="lightgreen", finished=False):
        return _f([_c("vec", list(v), f"vector  size={len(v)}", hl=extra_hl or {})],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg=f"初期状態: {list(v)}")

    # push_back × 5
    for val in [2, 7, 1, 5, 3]:
        v.append(val)
        yield frame({len(v) - 1: "yellow"}, msg=f"push_back({val})  →  size={len(v)}")

    # erase(find(5)) — 最初の 5 を検索して削除
    idx = v.index(5)
    yield frame({idx: "yellow"}, msg=f"find(5) → index={idx},  v[{idx}]={v[idx]}")
    yield frame({idx: "#ff4444"}, msg=f"erase(find(5)): v[{idx}]={v[idx]} を削除", color="orange")
    v.pop(idx)
    yield frame(msg=f"erase 後: {list(v)}")

    # insert(begin, 4) — 先頭に 4
    v.insert(0, 4)
    yield frame({0: "yellow"}, msg=f"insert(begin, 4): 先頭に 4 を挿入")

    # insert(begin+2, 6) — index 2 に 6
    v.insert(2, 6)
    yield frame({2: "yellow"}, msg=f"insert(begin+2, 6): index=2 に 6 を挿入")

    # insert(end, 10) — 末尾に 10
    v.append(10)
    yield frame({len(v) - 1: "yellow"}, msg=f"insert(end, 10): 末尾に 10 を挿入")

    # erase(begin+3) — index 3 を削除
    yield frame({3: "#ff4444"}, msg=f"erase(begin+3): v[3]={v[3]} を削除", color="orange")
    v.pop(3)
    yield frame(msg=f"erase 後: {list(v)}")

    # t = copy of v; t.reverse()
    t = list(v)
    t.reverse()
    yield _f([_c("vec", list(v), "vector v"),
              _c("rev", t, "vector t  (reverse後)",
                 hl={i: "#4488ff" for i in range(len(t))})],
             base + [{"message": f"t = v をコピーして t.reverse()  →  {t}", "color": "cyan"}],
             finished=True)


def iterator_sum3(n, **kwargs):
    """Sample3_3: イテレータで 3 要素ずつの合計を計算"""
    N = max(6, min(int(n), 30))
    data = [randint(1, 99) for _ in range(N)]
    base = [{"message": f"イテレータ: 3 要素ずつの合計  N={N}  (Sample3_3)", "color": "white"}]

    output = []
    i = 0

    yield _f([_c("input", data, "Input"),
              _c("output", [0], "Output (空)", hl={0: "#1a1a2a"})], base)

    while i < N:
        grp = [i + k for k in range(3) if i + k < N]
        hl_in = {k: "yellow" for k in grp}

        yield _f([_c("input", data, "Input", hl=hl_in),
                  _c("output", list(output) + [0], f"Output  ({len(output)} 要素)",
                     hl={len(output): "#334455"})],
                 base + [{"message": f"イテレータ → index {grp}", "color": "lightgreen"}])

        s = sum(data[j] for j in grp)
        output.append(s)

        yield _f([_c("input", data, "Input", hl=hl_in),
                  _c("output", list(output), f"Output  ({len(output)} 要素)",
                     hl={len(output) - 1: "#ffff44"})],
                 base + [{"message": f"sum = {' + '.join(str(data[j]) for j in grp)} = {s}",
                          "color": "cyan"}])
        i += len(grp)

    yield _f([_c("input", data, "Input"),
              _c("output", output, f"Output  ({len(output)} 要素)")],
             base + [{"message": f"完了: {len(output)} 個の合計を計算", "color": "#44aa44"}],
             finished=True)


# ===========================================================================
# Ch.4: 連結リスト (type: "misc")
# ===========================================================================

def singly_linked_list(n, **kwargs):
    """Sample4_2: 片方向連結リストの操作 (add / addFirst / deleteFirst / deleteNode / find)"""
    base = [{"message": "片方向連結リスト  (Sample4_2)", "color": "white"}]
    vals = []

    def ll_hl(extra=None):
        h = dict(extra or {})
        if vals:
            if 0 not in h:
                h[0] = "#44aa44"              # first: 緑
            if len(vals) - 1 not in h:
                h[len(vals) - 1] = "#4488cc"  # last:  青
        return h

    def frame(extra_hl=None, msg="", color="lightgreen", finished=False):
        display = list(vals) if vals else [0]
        return _f([_c("list", display, "Linked List  first ──→ last", hl=ll_hl(extra_hl))],
                  base + [{"message": msg, "color": color}], finished=finished)

    def traverse_and_delete(target):
        """target を線形探索してフレームを生成し、削除する"""
        idx = vals.index(target)
        for i in range(idx + 1):
            found = (vals[i] == target)
            h = {0: "#44aa44", len(vals) - 1: "#4488cc",
                 i: "#ff4444" if found else "yellow"}
            yield _f([_c("list", list(vals), "Linked List", hl=h)],
                     base + [{"message": f"[{i}] = {vals[i]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}])
        vals.pop(idx)

    yield frame(msg="連結リスト生成 (空)")

    # add(3), add(1), add(8), add(4), add(5)
    for v in [3, 1, 8, 4, 5]:
        vals.append(v)
        yield frame({len(vals) - 1: "yellow"}, msg=f"add({v})  →  {list(vals)}")

    # deleteNode(1)
    yield frame(msg="deleteNode(1): 値 1 を線形探索...")
    yield from traverse_and_delete(1)
    yield frame(msg=f"deleteNode(1) 完了  →  {list(vals)}")

    # addFirst(0)
    vals.insert(0, 0)
    yield frame({0: "yellow"}, msg=f"addFirst(0)  →  {list(vals)}")

    # add(10..13)
    for v in range(10, 14):
        vals.append(v)
    yield frame(msg=f"add(10)〜add(13) 完了  →  size={len(vals)}")

    # deleteFirst()
    old_first = vals[0]
    yield _f([_c("list", list(vals), "Linked List",
                 hl={0: "#ff4444", len(vals) - 1: "#4488cc"})],
             base + [{"message": f"deleteFirst(): 先頭 {old_first} を削除", "color": "orange"}])
    vals.pop(0)
    yield frame(msg=f"deleteFirst() 完了  →  先頭={vals[0]}")

    # find(8)
    target_find = 8
    yield frame(msg=f"find({target_find}): 線形探索...")
    for i in range(len(vals)):
        found = (vals[i] == target_find)
        h = {0: "#44aa44", len(vals) - 1: "#4488cc",
             i: "#ff4444" if found else "yellow"}
        yield _f([_c("list", list(vals), "Linked List", hl=h)],
                 base + [{"message": f"[{i}] = {vals[i]}  {'→ 発見!' if found else '→ 次へ'}",
                          "color": "red" if found else "lightgreen"}])
        if found:
            break

    # deleteNode(12)
    yield frame(msg="deleteNode(12): 値 12 を線形探索...")
    yield from traverse_and_delete(12)
    yield frame(msg=f"deleteNode(12) 完了  →  {list(vals)}")

    yield frame(msg=f"全操作完了  size={len(vals)}", finished=True)


def doubly_linked_list(n, **kwargs):
    """Sample4_5: 双方向連結リストの操作 (add / deleteNode / addFirst / displayReverse / reverse)"""
    base = [{"message": "双方向連結リスト  (Sample4_5)", "color": "white"}]
    vals = []

    def dll_hl(extra=None):
        h = dict(extra or {})
        if vals:
            if 0 not in h:
                h[0] = "#44aa44"
            if len(vals) - 1 not in h:
                h[len(vals) - 1] = "#4488cc"
        return h

    def frame(extra_hl=None, msg="", color="lightgreen", finished=False, objs=None):
        if objs is None:
            display = list(vals) if vals else [0]
            objs = [_c("list", display, "Doubly Linked List  (←→)", hl=dll_hl(extra_hl))]
        return _f(objs, base + [{"message": msg, "color": color}], finished=finished)

    def traverse_and_delete(target):
        idx = vals.index(target)
        for i in range(idx + 1):
            found = (vals[i] == target)
            h = {0: "#44aa44", len(vals) - 1: "#4488cc",
                 i: "#ff4444" if found else "yellow"}
            yield _f([_c("list", list(vals), "Doubly Linked List  (←→)", hl=h)],
                     base + [{"message": f"[{i}] = {vals[i]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}])
        vals.pop(idx)

    yield frame(msg="双方向連結リスト生成 (空)")

    # add: 3, 8, 5, 4, 1
    for v in [3, 8, 5, 4, 1]:
        vals.append(v)
        yield frame({len(vals) - 1: "yellow"}, msg=f"add({v})  →  {list(vals)}")

    # deleteNode(1)
    yield frame(msg="deleteNode(1): 値 1 を探索...")
    yield from traverse_and_delete(1)
    yield frame(msg=f"deleteNode(1) 完了  →  {list(vals)}")

    # deleteNode(3)
    yield frame(msg="deleteNode(3): 値 3 を探索...")
    yield from traverse_and_delete(3)
    yield frame(msg=f"deleteNode(3) 完了  →  {list(vals)}")

    # addFirst(6)
    vals.insert(0, 6)
    yield frame({0: "yellow"}, msg=f"addFirst(6)  →  {list(vals)}")

    # display() — 先頭から順方向に走査
    yield frame(msg="display(): 先頭から順に走査 →")
    for i in range(len(vals)):
        h = {0: "#44aa44", len(vals) - 1: "#4488cc", i: "yellow"}
        yield _f([_c("list", list(vals), "Doubly Linked List  (→)", hl=h)],
                 base + [{"message": f"→  {vals[i]}", "color": "lightgreen"}])

    # displayReverse() — 末尾から逆方向に走査
    yield frame(msg="displayReverse(): 末尾から逆順に走査 ←")
    for i in range(len(vals) - 1, -1, -1):
        h = {0: "#44aa44", len(vals) - 1: "#4488cc", i: "yellow"}
        yield _f([_c("list", list(vals), "Doubly Linked List  (←)", hl=h)],
                 base + [{"message": f"←  {vals[i]}", "color": "cyan"}])

    # reverse() — 逆順リストを生成して並べて表示
    rev = list(reversed(vals))
    yield frame(
        msg=f"reverse(): 逆順リストを生成  →  {rev}",
        color="cyan",
        finished=True,
        objs=[
            _c("list", list(vals), "元のリスト",
               hl={0: "#44aa44", len(vals) - 1: "#4488cc"}),
            _c("rev",  rev,        "reversed リスト",
               hl={0: "#44aa44", len(rev) - 1: "#4488cc"}),
        ],
    )


# ===========================================================================
# アルゴリズム一覧 / データサイズ一覧
# ===========================================================================

AlgorithmList = [
    # ── Ch.3: vector / イテレータ ──
    ("vector capacity  (Ch.3)",    vector_capacity,    {"type": "misc"}),
    ("vector 操作  (Ch.3)",        vector_ops,         {"type": "misc"}),
    ("イテレータ・3要素合計  (Ch.3)", iterator_sum3,      {"type": "misc"}),
    # ── Ch.4: 連結リスト ──
    ("片方向連結リスト  (Ch.4)",    singly_linked_list, {"type": "misc"}),
    ("双方向連結リスト  (Ch.4)",    doubly_linked_list, {"type": "misc"}),
]

DataSizeList = [8, 12, 16, 20, 24]
