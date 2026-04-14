"""
algorithms.py – AAforDataStructures
データ構造アニメーション (Ch.3: vector / Ch.4: 連結リスト)

オブジェクト種別:
  array1d_cells  – 正方形セル配列
  linked_list    – 矢印接続ノード列
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

def _tape(id, cells, head, label="", color="#4472C4", weight=1):
    return {
        "id": id, "type": "tape",
        "cells": list(cells), "head": int(head),
        "label": label, "color": color,
        "weight": weight,
    }

def _ll(id, nodes, label="", hl=None, is_doubly=False, is_vertical=False,
        ptr_labels=None, ptr_colors=None, weight=1):
    obj = {
        "id": id, "type": "linked_list",
        "nodes": list(nodes), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "is_doubly": is_doubly, "is_vertical": is_vertical,
        "weight": weight,
    }
    if ptr_labels: obj["ptr_labels"] = ptr_labels
    if ptr_colors: obj["ptr_colors"] = ptr_colors
    return obj

def _stack_v(id, values, top, max_size, label="", hl=None, weight=1):
    return {
        "id": id, "type": "stack_v",
        "values": list(values), "top": int(top), "max_size": int(max_size),
        "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "weight": weight,
    }

def _queue_circ(id, values, front, back, count, label="", hl=None, weight=1):
    return {
        "id": id, "type": "queue_circ",
        "values": list(values), "front": int(front),
        "back": int(back % len(values)) if values else 0,
        "count": int(count), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "weight": weight,
    }


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

    yield _f([_tape("input", data, 0, "Input"),
              _c("output", [0], "Output (空)", hl={0: "#1a1a2a"})], base)

    while i < N:
        grp = [i + k for k in range(3) if i + k < N]

        # テープを 3 要素ぶん 1 つずつスキャン
        for step, idx in enumerate(grp):
            yield _f([_tape("input", data, idx, "Input"),
                      _c("output", list(output) + [0], f"Output  ({len(output)} 要素)",
                         hl={len(output): "#334455"})],
                     base + [{"message": f"it → data[{idx}] = {data[idx]}  ({step+1}/3)",
                               "color": "lightgreen"}])

        s = sum(data[j] for j in grp)
        output.append(s)

        yield _f([_tape("input", data, grp[-1], "Input"),
                  _c("output", list(output), f"Output  ({len(output)} 要素)",
                     hl={len(output) - 1: "#ffff44"})],
                 base + [{"message": f"sum = {' + '.join(str(data[j]) for j in grp)} = {s}",
                          "color": "cyan"}])
        i += len(grp)

    yield _f([_tape("input", data, N - 1, "Input"),
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

    def frame(extra_hl=None, msg="", color="lightgreen", finished=False):
        nodes = list(vals) if vals else []
        return _f([_ll("list", nodes, "Singly Linked List", hl=extra_hl or {}, is_doubly=False)],
                  base + [{"message": msg, "color": color}], finished=finished,
                  text_position="bottom")

    def traverse_and_delete(target):
        idx = vals.index(target)
        for i in range(idx + 1):
            found = (vals[i] == target)
            h = {i: "#ff4444" if found else "yellow"}
            yield _f([_ll("list", list(vals), "Singly Linked List", hl=h)],
                     base + [{"message": f"[{i}] = {vals[i]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}],
                     text_position="bottom")
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
    yield _f([_ll("list", list(vals), "Singly Linked List", hl={0: "#ff4444"})],
             base + [{"message": f"deleteFirst(): 先頭 {old_first} を削除", "color": "orange"}])
    vals.pop(0)
    yield frame(msg=f"deleteFirst() 完了  →  先頭={vals[0]}")

    # find(8)
    target_find = 8
    yield frame(msg=f"find({target_find}): 線形探索...")
    for i in range(len(vals)):
        found = (vals[i] == target_find)
        h = {i: "#ff4444" if found else "yellow"}
        yield _f([_ll("list", list(vals), "Singly Linked List", hl=h)],
                 base + [{"message": f"[{i}] = {vals[i]}  {'→ 発見!' if found else '→ 次へ'}",
                          "color": "red" if found else "lightgreen"}],
                 text_position="bottom")
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

    def frame(extra_hl=None, msg="", color="lightgreen", finished=False, objs=None):
        if objs is None:
            nodes = list(vals) if vals else []
            objs = [_ll("list", nodes, "Doubly Linked List", hl=extra_hl or {}, is_doubly=True)]
        return _f(objs, base + [{"message": msg, "color": color}], finished=finished,
                  text_position="bottom")

    def traverse_and_delete(target):
        idx = vals.index(target)
        for i in range(idx + 1):
            found = (vals[i] == target)
            h = {i: "#ff4444" if found else "yellow"}
            yield _f([_ll("list", list(vals), "Doubly Linked List", hl=h, is_doubly=True)],
                     base + [{"message": f"[{i}] = {vals[i]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}],
                     text_position="bottom")
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
        h = {i: "yellow"}
        yield _f([_ll("list", list(vals), "Doubly Linked List  (→)", hl=h, is_doubly=True)],
                 base + [{"message": f"→  {vals[i]}", "color": "lightgreen"}],
                 text_position="bottom")

    # displayReverse() — 末尾から逆方向に走査
    yield frame(msg="displayReverse(): 末尾から逆順に走査 ←")
    for i in range(len(vals) - 1, -1, -1):
        h = {i: "yellow"}
        yield _f([_ll("list", list(vals), "Doubly Linked List  (←)", hl=h, is_doubly=True)],
                 base + [{"message": f"←  {vals[i]}", "color": "cyan"}],
                 text_position="bottom")

    # reverse() — 逆順リストを生成して並べて表示
    rev = list(reversed(vals))
    yield frame(
        msg=f"reverse(): 逆順リストを生成  →  {rev}",
        color="cyan",
        finished=True,
        objs=[
            _ll("list", list(vals), "元のリスト", is_doubly=True),
            _ll("rev",  rev,        "reversed リスト", is_doubly=True),
        ],
    )


# ===========================================================================
# Ch.5: スタック / キュー / RPN (type: "misc")
# ===========================================================================

def stack_linked_list(n, **kwargs):
    """Sample5_1: 連結リストによるスタックの Push/Pop（縦方向表示）"""
    base = [{"message": "連結リストスタック  (Sample5_1)", "color": "white"}]
    vals = []   # vals[0] = top (先頭が top)

    def frame(hl=None, msg="", color="lightgreen", finished=False):
        return _f([_ll("stack", list(vals), "Stack  (top → bottom)",
                       hl=hl or {}, is_doubly=False, is_vertical=True,
                       ptr_labels=["top", "bottom"], ptr_colors=["#44cc66", "#4499dd"])],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg="スタック生成 (空)")

    for v in [3, 7, 1, 5, 2, 8]:
        vals.insert(0, v)                  # Push: 先頭に追加
        yield frame({0: "yellow"}, msg=f"Push({v})  top={vals[0]}  size={len(vals)}")

    yield frame(msg=f"isEmpty? = {len(vals) == 0}", color="cyan")

    for _ in range(3):
        val = vals[0]
        yield frame({0: "#ff4444"}, msg=f"Pop() = {val}  (top を削除)", color="orange")
        vals.pop(0)
        new_top = str(vals[0]) if vals else "None"
        yield frame(msg=f"Pop 完了  新 top={new_top}  size={len(vals)}")

    for v in [9, 4]:
        vals.insert(0, v)
        yield frame({0: "yellow"}, msg=f"Push({v})  top={vals[0]}  size={len(vals)}")

    yield frame(msg="全 Pop 開始...")
    while vals:
        val = vals[0]
        yield frame({0: "#ff4444"}, msg=f"Pop() = {val}", color="orange")
        vals.pop(0)

    yield frame(msg="isEmpty? = True  全操作完了", color="#44aa44", finished=True)


def queue_linked_list(n, **kwargs):
    """Sample5_8: 連結リストによるキューの Enqueue/Dequeue"""
    base = [{"message": "連結リストキュー  (Sample5_8)", "color": "white"}]
    vals = []   # vals[0] = front, vals[-1] = back

    def frame(hl=None, msg="", color="lightgreen", finished=False):
        return _f([_ll("queue", list(vals), "Queue  front → … → back",
                       hl=hl or {}, is_doubly=False,
                       ptr_labels=["front", "back"], ptr_colors=["#44cc66", "#ff8844"])],
                  base + [{"message": msg, "color": color}], finished=finished,
                  text_position="bottom")

    yield frame(msg="キュー生成 (空)")

    for v in [3, 7, 1, 5, 2, 8]:
        vals.append(v)                     # Enqueue: 末尾に追加
        yield frame({len(vals) - 1: "yellow"},
                    msg=f"Enqueue({v})  back={vals[-1]}  size={len(vals)}")

    yield frame(msg=f"isEmpty? = {len(vals) == 0}", color="cyan")

    for _ in range(3):
        val = vals[0]
        yield frame({0: "#ff4444"}, msg=f"Dequeue() = {val}  (front を削除)", color="orange")
        vals.pop(0)
        new_front = str(vals[0]) if vals else "None"
        yield frame(msg=f"Dequeue 完了  新 front={new_front}  size={len(vals)}")

    for v in [9, 4, 6]:
        vals.append(v)
        yield frame({len(vals) - 1: "yellow"},
                    msg=f"Enqueue({v})  back={vals[-1]}  size={len(vals)}")

    yield frame(msg="全 Dequeue 開始...")
    while vals:
        val = vals[0]
        yield frame({0: "#ff4444"}, msg=f"Dequeue() = {val}", color="orange")
        vals.pop(0)

    yield frame(msg="isEmpty? = True  全操作完了", color="#44aa44", finished=True)



def stack_array(n, **kwargs):
    """Sample5_4: 配列によるスタックの Push/Pop（縦方向表示）"""
    MAXSIZE = 8
    base = [{"message": "配列スタック  (Sample5_4)", "color": "white"}]
    data = [0] * MAXSIZE
    top = -1

    def frame(hl_extra=None, msg="", color="lightgreen", finished=False):
        hl = hl_extra or {}
        return _f([_stack_v("stack", list(data), top, MAXSIZE,
                            f"Stack  max={MAXSIZE}", hl=hl)],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg="スタック生成 (空)  top=-1")

    for v in [3, 7, 1, 5, 2, 8]:
        top += 1
        data[top] = v
        yield frame({top: "yellow"}, msg=f"Push({v})  →  top={top}")

    yield frame(msg=f"isFull? = {top == MAXSIZE - 1}", color="cyan")

    for _ in range(3):
        val = data[top]
        yield frame({top: "#ff4444"}, msg=f"Pop() = {val}  (top={top})", color="orange")
        data[top] = 0
        top -= 1
        yield frame(msg=f"Pop 完了  top={top}")

    for v in [9, 4]:
        top += 1
        data[top] = v
        yield frame({top: "yellow"}, msg=f"Push({v})  →  top={top}")

    yield frame(msg="全 Pop 開始...")
    while top >= 0:
        val = data[top]
        yield frame({top: "#ff4444"}, msg=f"Pop() = {val}", color="orange")
        data[top] = 0
        top -= 1

    yield frame(msg=f"isEmpty? = {top == -1}  全操作完了", color="#44aa44", finished=True)


def queue_circular(n, **kwargs):
    """Sample5_9: 配列による循環キューの Enqueue/Dequeue（円形表示）"""
    MAXSIZE = 8
    base = [{"message": "循環キュー (配列)  (Sample5_9)", "color": "white"}]
    data = [0] * MAXSIZE
    front = back = count = 0

    def frame(hl_extra=None, msg="", color="lightgreen", finished=False):
        hl = hl_extra or {}
        return _f([_queue_circ("queue", list(data), front, back, count,
                               f"CircularQueue  max={MAXSIZE}  count={count}", hl=hl)],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg="循環キュー生成 (空)")

    for v in [1, 2, 3, 4, 5, 6]:
        data[back] = v
        back = (back + 1) % MAXSIZE
        count += 1
        yield frame({(back - 1) % MAXSIZE: "yellow"},
                    msg=f"Enqueue({v})  count={count}  back={back % MAXSIZE}")

    yield frame(msg=f"isFull? = {count == MAXSIZE}", color="cyan")

    for _ in range(3):
        val = data[front]
        yield frame({front: "#ff4444"}, msg=f"Dequeue() = {val}  front={front}", color="orange")
        data[front] = 0
        front = (front + 1) % MAXSIZE
        count -= 1
        yield frame(msg=f"Dequeue 完了  count={count}  front={front}")

    for v in [7, 8, 9, 10]:
        data[back] = v
        back = (back + 1) % MAXSIZE
        count += 1
        yield frame({(back - 1) % MAXSIZE: "yellow"},
                    msg=f"Enqueue({v})  count={count}  back={back % MAXSIZE}  ← 循環ラップ!")

    yield frame(msg="全 Dequeue 開始...")
    while count > 0:
        val = data[front]
        yield frame({front: "#ff4444"}, msg=f"Dequeue() = {val}", color="orange")
        data[front] = 0
        front = (front + 1) % MAXSIZE
        count -= 1

    yield frame(msg=f"isEmpty? = {count == 0}  全操作完了", color="#44aa44", finished=True)


def rpn_eval(n, **kwargs):
    """Sample5_7: B型単純式 → 逆ポーランド記法変換 + スタック評価"""
    # B型単純式: *(+(2 3) -(8 1))  → RPN: 2 3 + 8 1 - *  → 結果: 35
    expr = list("*(+(2 3) -(8 1))")
    expr_str = "".join(expr)
    base = [{"message": f"B型単純式 → RPN  (Sample5_7)  式: {expr_str}", "color": "white"}]

    oprs = []    # 演算子スタック (char)
    output = []  # 出力トークンリスト
    opr = ' '

    PAD = 8  # 表示用パディング幅

    def cvt_frame(ci, msg, color="lightgreen"):
        s_disp = list(oprs) + [' '] * max(0, PAD - len(oprs))
        s_hl   = {i: "#0e0e1e" for i in range(len(oprs), PAD)}
        if oprs:
            s_hl[len(oprs) - 1] = "#ff8844"   # stack top: オレンジ
        o_disp = list(output) + [' '] * max(0, PAD - len(output))
        o_hl   = {i: "#ffff44" for i in range(len(output))}
        o_hl.update({i: "#0e0e1e" for i in range(len(output), PAD)})
        return _f([
            _tape("expr", expr, ci, "B型式", "#9966cc"),
            _c("oprs", s_disp, f"演算子スタック ({len(oprs)})", hl=s_hl,
               ptr=_ptr(len(oprs) - 1, "top", "#ff8844") if oprs else None),
            _c("out",  o_disp, f"出力 ({len(output)} トークン)", hl=o_hl),
        ], base + [{"message": msg, "color": color}])

    yield cvt_frame(0, "変換開始")

    for ci, c in enumerate(expr):
        if c in '+-*/':
            opr = c
            yield cvt_frame(ci, f"演算子 '{c}' を一時保存  opr='{opr}'", color="cyan")
        elif c == '(':
            if opr != ' ':
                oprs.append(opr)
                opr = ' '
                yield cvt_frame(ci, f"'(' → opr をスタックに Push: '{oprs[-1]}'", color="#ff8844")
            else:
                yield cvt_frame(ci, "'(' スキップ (opr なし)")
        elif c == ')':
            if oprs:
                popped = oprs.pop()
                output.append(popped)
                yield cvt_frame(ci, f"')' → Pop '{popped}' して出力", color="orange")
        elif c.isdigit():
            output.append(c)
            yield cvt_frame(ci, f"数字 '{c}' を出力", color="lightgreen")
            if opr != ' ':
                output.append(opr)
                opr = ' '
                yield cvt_frame(ci, f"保存演算子 '{output[-1]}' も出力", color="cyan")

    while oprs:
        popped = oprs.pop()
        output.append(popped)
        yield cvt_frame(len(expr) - 1, f"残り演算子 '{popped}' を出力", color="orange")

    rpn_str = " ".join(output)
    o_disp = list(output) + [' '] * max(0, PAD - len(output))
    o_hl   = {i: "#44aaff" for i in range(len(output))}
    o_hl.update({i: "#0e0e1e" for i in range(len(output), PAD)})
    yield _f([_c("rpn", o_disp, f"RPN: {rpn_str}", hl=o_hl)],
             base + [{"message": f"変換完了!  RPN = {rpn_str}", "color": "cyan"}])

    # ── RPN 評価フェーズ ──
    base2 = [{"message": f"RPN 評価: {rpn_str}", "color": "white"}]
    nums = []

    def eval_frame(ti, msg, color="lightgreen", finished=False):
        n_disp = [str(x) for x in nums] + [' '] * max(0, PAD - len(nums))
        n_hl   = {i: "#0e0e1e" for i in range(len(nums), PAD)}
        if nums:
            n_hl[len(nums) - 1] = "#44cc66"   # top: 緑
        r_disp = list(output) + [' '] * max(0, PAD - len(output))
        r_hl   = {ti: "#ff8844"} if ti < len(output) else {}
        return _f([
            _tape("rpn", output, ti, "RPN", "#4499cc"),
            _c("nums", n_disp, f"数値スタック ({len(nums)})", hl=n_hl,
               ptr=_ptr(len(nums) - 1, "top", "#44cc66") if nums else None),
        ], base2 + [{"message": msg, "color": color}], finished=finished)

    yield eval_frame(0, "RPN 評価開始")

    for ti, tok in enumerate(output):
        if tok in '+-*/':
            b = nums.pop()
            a = nums.pop()
            res = (a + b if tok == '+' else a - b if tok == '-'
                   else a * b if tok == '*' else a // b)
            nums.append(res)
            yield eval_frame(ti, f"{a} {tok} {b} = {res}  → Push({res})", color="orange")
        elif tok.isdigit():
            nums.append(int(tok))
            yield eval_frame(ti, f"数字 '{tok}' → Push({tok})", color="lightgreen")

    result = nums[0] if nums else '?'
    yield _f([_c("result", [str(result)], f"結果 = {result}", hl={0: "#44cc66"})],
             base2 + [{"message": f"評価完了!  {expr_str} = {result}", "color": "#44aa44"}],
             finished=True)


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
    # ── Ch.5: スタック / キュー / RPN ──
    ("連結リストスタック  (Ch.5)",  stack_linked_list,  {"type": "misc"}),
    ("連結リストキュー  (Ch.5)",    queue_linked_list,  {"type": "misc"}),
    ("配列スタック  (Ch.5)",        stack_array,        {"type": "misc"}),
    ("循環キュー  (Ch.5)",          queue_circular,     {"type": "misc"}),
    ("RPN 変換・評価  (Ch.5)",      rpn_eval,           {"type": "misc"}),
]

DataSizeList = [8, 12, 16, 20, 24]
