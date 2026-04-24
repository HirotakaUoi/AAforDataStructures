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
       watchman=None, target=None, weight=1, unused_from=None):
    obj = {
        "id": id, "type": "array1d_cells",
        "values": list(values), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "fills": fills or [], "pointer": ptr,
        "watchman_index": watchman, "target": target,
        "weight": weight,
    }
    if unused_from is not None:
        obj["unused_from"] = int(unused_from)
    return obj

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

def vector_capacity(n, scheme="double", **kwargs):
    """Sample3_1: vector の push_back で capacity が変化する様子を可視化
    scheme="double"  : 満杯になるたびに capacity を 2倍に拡張
    scheme="fixed16" : 満杯になるたびに capacity を +16 ずつ拡張
    再確保時は旧配列・新配列を並列表示してコピーをアニメーション。
    """
    N = max(4, min(int(n), 256))
    seed_vals = [5, 2, 7, 1, 5, 10, 100, 25, 99,
                 42, 77, 33, 88, 14, 61, 50]
    push_vals = (seed_vals + [randint(1, 99)
                              for _ in range(max(0, N - len(seed_vals)))])[:N]

    SCHEME_LABEL = "2倍拡張" if scheme == "double" else "固定+16拡張"

    def sim_cap(size):
        """現在の size に対して必要な capacity を返す"""
        if size == 0:
            return 0
        if scheme == "double":
            c = 1
            while c < size:
                c *= 2
            return c
        else:                   # fixed16
            step = 16
            c = step
            while c < size:
                c += step
            return c

    def vec_obj(data, size, capacity, hl=None):
        """現在の vector を表示するセル (使用済み + unused_from 付き)"""
        display = list(data) + [0] * (capacity - len(data))
        return _c("vec", display,
                  f"vector  size={size},  capacity={capacity}",
                  hl=hl,
                  unused_from=size if capacity > size else None)

    base = [{"message":
             f"vector capacity – {SCHEME_LABEL}  push_back × {N}  (Sample3_1)",
             "color": "white"}]
    vals = []
    cap  = 0

    # ── 初期フレーム ────────────────────────────────────────────────────
    yield _f([_c("vec", [], "vector (空)  size=0,  capacity=0")],
             base + [{"message": "vector を生成  size=0,  capacity=0",
                      "color": "lightgreen"}])

    for v in push_vals:
        old_size = len(vals)
        old_cap  = cap
        vals.append(v)
        new_cap   = sim_cap(len(vals))
        cap_grew  = new_cap > old_cap

        if cap_grew and old_cap > 0:
            # ════════════════════════════════════════════════════════════
            # 再確保 + コピーアニメーション
            # ════════════════════════════════════════════════════════════
            old_vals = vals[:-1]   # v を追加する前の要素列 (old_cap 個)
            hl_full  = {i: "orange" for i in range(old_size)}

            # Step 1: 旧配列が満杯であることを示す
            yield _f(
                [_c("old", old_vals,
                    f"旧配列  size={old_size},  capacity={old_cap}  ← 満杯!",
                    hl=hl_full)],
                base + [{"message":
                         f"push_back({v})  → 配列が満杯!  再確保が必要  ({SCHEME_LABEL})",
                         "color": "orange"}]
            )

            # Step 2: 新しい領域を確保 (全セルが未使用)
            yield _f(
                [
                    _c("old", old_vals,
                       f"旧配列  size={old_size},  capacity={old_cap}",
                       hl=hl_full),
                    _c("new", [0] * new_cap,
                       f"新配列  capacity={new_cap}  (新規確保)",
                       unused_from=0),
                ],
                base + [{"message":
                         f"新しい領域を確保  capacity: {old_cap} → {new_cap}",
                         "color": "orange"}]
            )

            # Step 3: 要素を1つずつコピー
            copied = [0] * new_cap
            for i in range(old_size):
                yield _f(
                    [
                        _c("old", old_vals,
                           f"旧配列  [{i}] をコピー中",
                           hl={i: "yellow"}),
                        _c("new", copied,
                           f"新配列  ({i}/{old_size} コピー済)",
                           unused_from=i),
                    ],
                    base + [{"message":
                             f"コピー: old[{i}] = {old_vals[i]}  →  new[{i}]",
                             "color": "cyan"}]
                )
                copied[i] = old_vals[i]
                yield _f(
                    [
                        _c("old", old_vals,
                           f"旧配列  [{i}] をコピー中",
                           hl={i: "yellow"}),
                        _c("new", copied,
                           f"新配列  ({i+1}/{old_size} コピー済)",
                           hl={i: "#44aaff"},
                           unused_from=(i + 1) if (i + 1) < new_cap else None),
                    ],
                    base + [{"message": f"コピー完了: new[{i}] ← {copied[i]}",
                             "color": "cyan"}]
                )

            # Step 4: コピー完了・旧配列を解放
            yield _f(
                [_c("new", copied,
                    f"新配列  コピー完了  size={old_size},  capacity={new_cap}",
                    unused_from=old_size if new_cap > old_size else None)],
                base + [{"message":
                         f"旧配列を解放  新配列に切り替え  capacity={new_cap}",
                         "color": "orange"}]
            )

            cap = new_cap

            # Step 5: 新要素を追加
            yield _f(
                [vec_obj(vals, len(vals), cap,
                         hl={len(vals) - 1: "yellow"})],
                base + [{"message":
                         f"push_back({v}) 完了  size={len(vals)},"
                         f"  capacity={cap}  ← 再確保!",
                         "color": "orange"}]
            )

        elif cap_grew and old_cap == 0:
            # ── 初回確保 ────────────────────────────────────────────────
            cap = new_cap
            yield _f(
                [vec_obj(vals, len(vals), cap,
                         hl={len(vals) - 1: "yellow"})],
                base + [{"message":
                         f"push_back({v})  初回確保  size={len(vals)},"
                         f"  capacity={cap}",
                         "color": "orange"}]
            )

        else:
            # ── 再確保なし ──────────────────────────────────────────────
            cap = new_cap
            yield _f(
                [vec_obj(vals, len(vals), cap,
                         hl={len(vals) - 1: "yellow"})],
                base + [{"message":
                         f"push_back({v})  →  size={len(vals)},"
                         f"  capacity={cap}",
                         "color": "lightgreen"}]
            )

    # ── 完了フレーム ────────────────────────────────────────────────────
    yield _f(
        [vec_obj(vals, len(vals), cap)],
        base + [{"message":
                 f"完了: size={len(vals)},  capacity={cap}"
                 f"  (拡張回数: {_realloc_count(N, scheme)}回)",
                 "color": "#44aa44"}],
        finished=True
    )


def _realloc_count(n, scheme):
    """push_back × n で発生する再確保回数を返す (表示用)"""
    cap = 0; count = 0
    for i in range(1, n + 1):
        if scheme == "double":
            nc = 1
            while nc < i: nc *= 2
        else:
            nc = 16
            while nc < i: nc += 16
        if nc > cap: cap = nc; count += 1
    return count - (1 if n > 0 else 0)  # 初回確保は除く


def vector_capacity_double(n, **kwargs):
    """vector capacity – 2倍拡張"""
    return vector_capacity(n, scheme="double", **kwargs)


def vector_capacity_fixed16(n, **kwargs):
    """vector capacity – 固定+16拡張"""
    return vector_capacity(n, scheme="fixed16", **kwargs)


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
    # データ数をメニュー設定に従わせる（表示しやすいサイズに制限）
    N = max(4, min(int(n), 20))
    data = [randint(1, 99) for _ in range(N)]
    # 操作ターゲットをデータ内の値で確定（インデックスで選択 → 重複回避）
    del1_v   = data[1]           # deleteNode 1回目
    first_v  = randint(1, 99)    # addFirst に追加する値
    find_v   = data[N // 2]      # find のターゲット（中央付近）
    del2_v   = data[N - 2]       # deleteNode 2回目（末尾付近）

    base = [{"message": f"片方向連結リスト  N={N}  (Sample4_2)", "color": "white"}]
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

    # add N 個の値
    for v in data:
        vals.append(v)
        yield frame({len(vals) - 1: "yellow"}, msg=f"add({v})  →  size={len(vals)}")

    # deleteNode(del1_v)
    yield frame(msg=f"deleteNode({del1_v}): 値 {del1_v} を線形探索...")
    yield from traverse_and_delete(del1_v)
    yield frame(msg=f"deleteNode({del1_v}) 完了  →  size={len(vals)}")

    # addFirst(first_v)
    vals.insert(0, first_v)
    yield frame({0: "yellow"}, msg=f"addFirst({first_v})  →  size={len(vals)}")

    # deleteFirst()
    old_first = vals[0]
    yield _f([_ll("list", list(vals), "Singly Linked List", hl={0: "#ff4444"})],
             base + [{"message": f"deleteFirst(): 先頭 {old_first} を削除", "color": "orange"}],
             text_position="bottom")
    vals.pop(0)
    yield frame(msg=f"deleteFirst() 完了  →  先頭={vals[0]}")

    # find(find_v)
    yield frame(msg=f"find({find_v}): 線形探索...")
    for i in range(len(vals)):
        found = (vals[i] == find_v)
        h = {i: "#ff4444" if found else "yellow"}
        yield _f([_ll("list", list(vals), "Singly Linked List", hl=h)],
                 base + [{"message": f"[{i}] = {vals[i]}  {'→ 発見!' if found else '→ 次へ'}",
                          "color": "red" if found else "lightgreen"}],
                 text_position="bottom")
        if found:
            break

    # deleteNode(del2_v) ― まだリストに残っている場合のみ
    if del2_v in vals:
        yield frame(msg=f"deleteNode({del2_v}): 値 {del2_v} を線形探索...")
        yield from traverse_and_delete(del2_v)
        yield frame(msg=f"deleteNode({del2_v}) 完了  →  size={len(vals)}")

    yield frame(msg=f"全操作完了  size={len(vals)}", finished=True)


def singly_linked_list_avg4(n, **kwargs):
    """Sample4_7: 片方向連結リスト + イテレータで 4 要素ずつの平均を計算"""
    N = max(4, min(int(n), 32))
    data = [randint(1, 99) for _ in range(N)]
    base = [{"message": f"イテレータ: 4 要素ずつの平均  N={N}  (Sample4_7)", "color": "white"}]

    vals   = list(data)   # linked list の内容
    output = []           # 計算済み平均値

    def out_obj():
        if not output:
            return _c("out", [0], "Output (空)", hl={0: "#1a1a2a"}, weight=0.7)
        return _c("out", list(output), f"Output  ({len(output)} 要素)",
                  hl={len(output) - 1: "#ffff44"}, weight=0.7)

    def frame(hl=None, msg="", color="lightgreen", finished=False):
        return _f(
            [_ll("list", list(vals), f"Singly Linked List  (N={N})",
                 hl=hl or {}, is_doubly=False, weight=1.4),
             out_obj()],
            base + [{"message": msg, "color": color}],
            finished=finished, text_position="bottom")

    # 初期フレーム: リスト全体を表示
    yield frame(msg=f"リストを生成  size={N}  (イテレータ it = begin())")

    i = 0
    while i < N:
        grp_end  = min(i + 4, N)
        grp_size = grp_end - i
        scanned  = []
        run_sum  = 0

        # グループ内を 1 ノードずつイテレータで走査
        for step, idx in enumerate(range(i, grp_end)):
            hl = {s: "#4488cc" for s in scanned}   # 走査済み: 青
            hl[idx] = "yellow"                      # 現在ノード: 黄
            yield frame(
                hl=hl,
                msg=f"it → node[{idx}] = {vals[idx]}  ({step + 1}/{grp_size} 要素目)"
                    + (f"  sum={run_sum}+{vals[idx]}={run_sum + vals[idx]}" if step > 0 else ""),
                color="lightgreen")
            run_sum += vals[idx]
            scanned.append(idx)

        # 平均を計算して output へ追加
        avg = run_sum // grp_size
        output.append(avg)
        sum_str = " + ".join(str(vals[j]) for j in range(i, grp_end))
        hl_done = {j: "#44aa44" for j in range(i, grp_end)}
        yield frame(
            hl=hl_done,
            msg=f"平均 = ({sum_str}) / {grp_size} = {run_sum} / {grp_size} = {avg}",
            color="cyan")

        i = grp_end

    yield frame(msg=f"完了: {len(output)} 個の平均を計算", color="#44aa44", finished=True)


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
                  base + [{"message": msg, "color": color}],
                  finished=finished, text_position="bottom")

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
# Ch.6: 二分探索木 (type: "misc")
# ===========================================================================

# ─── BST helpers ─────────────────────────────────────────────────────────

def _bst_apply_hl(node, hl_map):
    if node is None:
        return None
    return {
        "key":       node["key"],
        "color":     node.get("color", "#4472C4"),
        "highlight": hl_map.get(node["key"]),
        "left":      _bst_apply_hl(node["left"],  hl_map),
        "right":     _bst_apply_hl(node["right"], hl_map),
    }

def _bst_obj(id, node, hl_map=None, label="", weight=1):
    return {"id": id, "type": "bst_tree",
            "root": _bst_apply_hl(node, hl_map or {}),
            "label": label, "weight": weight}

def _bst_insert(tree, key):
    if tree is None:
        return {"key": key, "color": "#4472C4", "left": None, "right": None}
    t = dict(tree)
    if key < t["key"]:
        t["left"]  = _bst_insert(t["left"],  key)
    else:
        t["right"] = _bst_insert(t["right"], key)
    return t

def _bst_search_path(tree, key):
    path = []
    node = tree
    while node is not None:
        path.append(node["key"])
        if key == node["key"]:
            break
        node = node["left"] if key < node["key"] else node["right"]
    return path

def _bst_min_node(node):
    while node["left"] is not None:
        node = node["left"]
    return node

def _bst_delete(tree, key):
    if tree is None:
        return None
    t = dict(tree)
    if key < t["key"]:
        t["left"]  = _bst_delete(t["left"],  key)
    elif key > t["key"]:
        t["right"] = _bst_delete(t["right"], key)
    else:
        if t["left"] is None:
            return t["right"]
        if t["right"] is None:
            return t["left"]
        succ = _bst_min_node(t["right"])
        t["key"]   = succ["key"]
        t["right"] = _bst_delete(t["right"], succ["key"])
    return t


def bst_operations(n, **kwargs):
    """Ch.6: 二分探索木 (BST) の挿入・探索・削除"""
    from random import sample
    N = max(5, min(int(n), 24))
    vals = sample(range(1, 200), N)

    base = [{"message": f"二分探索木 (BST)  N={N}  (Ch.6)", "color": "white"}]

    tree = None

    # ── 初期フレーム (空の BST) ────────────────────────────────────
    yield _f([_bst_obj("bst", None, label="BST (空)")],
             base + [{"message": f"BST 初期化 (空)  N={N} 個を挿入します", "color": "lightgreen"}])

    # ── 挿入フェーズ ─────────────────────────────────────────────────
    for v in vals:
        # 挿入パスを可視化
        path = _bst_search_path(tree, v) if tree else []
        if path:
            yield _f([_bst_obj("bst", tree, hl_map={k: "yellow" for k in path},
                               label="BST")],
                     base + [{"message": f"insert({v}): 挿入位置を探索中  path={path}", "color": "cyan"}])
        tree = _bst_insert(tree, v)
        yield _f([_bst_obj("bst", tree, hl_map={v: "#44ff88"}, label="BST")],
                 base + [{"message": f"insert({v}) 完了", "color": "lightgreen"}])

    yield _f([_bst_obj("bst", tree, label="BST")],
             base + [{"message": f"挿入完了  N={N}  ノード数={N}", "color": "white"}])

    # ── 探索フェーズ ─────────────────────────────────────────────────
    not_in = next(x for x in range(1, 200) if x not in set(vals))
    search_targets = [vals[N // 3], vals[2 * N // 3], not_in]
    for target in search_targets:
        path = _bst_search_path(tree, target)
        found = (path and path[-1] == target)
        for step, k in enumerate(path):
            hl = {k: ("#44ff88" if k == target else "yellow")}
            yield _f([_bst_obj("bst", tree, hl_map=hl, label="BST")],
                     base + [{"message": f"search({target}): [{step+1}] key={k}  {'→ 発見!' if k==target else '→ 次へ'}",
                              "color": "lightgreen" if k == target else "cyan"}])
        if not found:
            yield _f([_bst_obj("bst", tree, label="BST")],
                     base + [{"message": f"search({target}): Not Found", "color": "#ff6655"}])

    # ── 削除フェーズ ─────────────────────────────────────────────────
    delete_targets = [vals[1], vals[N // 2]]
    for target in delete_targets:
        path = _bst_search_path(tree, target)
        if path and path[-1] == target:
            yield _f([_bst_obj("bst", tree, hl_map={target: "#ff4444"}, label="BST")],
                     base + [{"message": f"delete({target}): ノードを削除します", "color": "orange"}])
            tree = _bst_delete(tree, target)
            yield _f([_bst_obj("bst", tree, label="BST")],
                     base + [{"message": f"delete({target}) 完了", "color": "lightgreen"}])

    yield _f([_bst_obj("bst", tree, label="BST")],
             base + [{"message": "BST 操作完了", "color": "#44aa44"}],
             finished=True)


# ─── 赤黒木 helpers ───────────────────────────────────────────────────────

class _RBNode:
    __slots__ = ('key', 'color', 'left', 'right', 'parent')
    def __init__(self, key, color='red'):
        self.key    = key
        self.color  = color  # 'red' or 'black'
        self.left   = self.right = self.parent = None


def _rb_left_rotate(root, x, nil):
    y        = x.right
    x.right  = y.left
    if y.left is not nil:
        y.left.parent = x
    y.parent = x.parent
    if x.parent is nil:
        root = y
    elif x is x.parent.left:
        x.parent.left  = y
    else:
        x.parent.right = y
    y.left   = x
    x.parent = y
    return root


def _rb_right_rotate(root, x, nil):
    y        = x.left
    x.left   = y.right
    if y.right is not nil:
        y.right.parent = x
    y.parent = x.parent
    if x.parent is nil:
        root = y
    elif x is x.parent.right:
        x.parent.right = y
    else:
        x.parent.left  = y
    y.right  = x
    x.parent = y
    return root


def _rb_to_dict(node, nil, hl_map=None):
    if node is nil or node is None:
        return None
    color = "#cc3333" if node.color == 'red' else "#4472C4"
    return {
        "key":       node.key,
        "color":     color,
        "highlight": (hl_map or {}).get(node.key),
        "left":      _rb_to_dict(node.left,  nil, hl_map),
        "right":     _rb_to_dict(node.right, nil, hl_map),
    }

def _rb_obj(id, root, nil, hl_map=None, label="", weight=1):
    return {"id": id, "type": "bst_tree",
            "root": _rb_to_dict(root, nil, hl_map or {}),
            "label": label, "weight": weight}


def rb_tree_insert(n, **kwargs):
    """赤黒木: 挿入とバランス調整を可視化"""
    from random import sample
    N = max(4, min(int(n), 24))
    vals = sample(range(1, 200), N)

    base = [{"message": f"赤黒木 (Red-Black Tree)  N={N}", "color": "white"}]

    nil        = _RBNode(-1, 'black')
    nil.left   = nil.right = nil.parent = nil
    root       = nil
    root.parent = nil

    def snapshot(hl_map=None, msg="", color="lightgreen", finished=False):
        r = root if root is not nil else None
        return _f([_rb_obj("rb", r, nil, hl_map, label="Red-Black Tree")],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield snapshot(msg="赤黒木 初期化 (空)")

    for v in vals:
        # Insert as BST
        z         = _RBNode(v, 'red')
        z.left    = z.right = nil
        y         = nil
        x         = root
        while x is not nil:
            y = x
            x = x.left if z.key < x.key else x.right
        z.parent = y
        if y is nil:
            root = z
        elif z.key < y.key:
            y.left = z
        else:
            y.right = z

        yield snapshot({v: "yellow"}, msg=f"insert({v}): BST挿入 (赤ノード)", color="cyan")

        # Fix RB properties
        while z.parent.color == 'red':
            if z.parent is z.parent.parent.left:
                uncle = z.parent.parent.right
                if uncle.color == 'red':
                    # Case 1: recolor
                    z.parent.color        = 'black'
                    uncle.color           = 'black'
                    z.parent.parent.color = 'red'
                    old_z = z
                    z = z.parent.parent
                    yield snapshot(
                        {z.key: "orange", old_z.key: "#44aaff"},
                        msg=f"Case1: 叔父が赤 → 再彩色  祖父{z.key}を赤に",
                        color="orange")
                else:
                    if z is z.parent.right:
                        # Case 2: left rotate
                        z = z.parent
                        root = _rb_left_rotate(root, z, nil)
                        yield snapshot({z.key: "orange"}, msg=f"Case2: 左回転  pivot={z.key}", color="orange")
                    # Case 3: right rotate
                    z.parent.color        = 'black'
                    z.parent.parent.color = 'red'
                    pp = z.parent.parent
                    root = _rb_right_rotate(root, pp, nil)
                    yield snapshot({z.key: "#44ff88"}, msg=f"Case3: 右回転 + 再彩色  pivot={pp.key}", color="cyan")
            else:
                uncle = z.parent.parent.left
                if uncle.color == 'red':
                    z.parent.color        = 'black'
                    uncle.color           = 'black'
                    z.parent.parent.color = 'red'
                    old_z = z
                    z = z.parent.parent
                    yield snapshot(
                        {z.key: "orange", old_z.key: "#44aaff"},
                        msg=f"Case1: 叔父が赤 → 再彩色  祖父{z.key}を赤に",
                        color="orange")
                else:
                    if z is z.parent.left:
                        z = z.parent
                        root = _rb_right_rotate(root, z, nil)
                        yield snapshot({z.key: "orange"}, msg=f"Case2: 右回転  pivot={z.key}", color="orange")
                    z.parent.color        = 'black'
                    z.parent.parent.color = 'red'
                    pp = z.parent.parent
                    root = _rb_left_rotate(root, pp, nil)
                    yield snapshot({z.key: "#44ff88"}, msg=f"Case3: 左回転 + 再彩色  pivot={pp.key}", color="cyan")

        root.color = 'black'
        yield snapshot({v: "#44ff88"}, msg=f"insert({v}) 完了  根は黒", color="lightgreen")

    yield snapshot(msg="赤黒木 構築完了  (赤=赤ノード / 青=黒ノード)", color="#44aa44", finished=True)


# ===========================================================================
# Ch.11: グラフ – DFS / BFS (type: "misc")
# ===========================================================================

def _make_random_graph(n, seed=None):
    """N ノードのランダム連結無向グラフを生成 (円形レイアウト)"""
    import math
    from random import Random
    rng = Random(seed)

    # 円形レイアウト (12時スタート)
    nodes = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = round(0.5 + 0.44 * math.cos(angle), 3)
        y = round(0.5 + 0.44 * math.sin(angle), 3)
        nodes.append({"id": i, "label": str(i), "x": x, "y": y})

    # スパニングツリーで連結性を保証
    perm = list(range(1, n))
    rng.shuffle(perm)
    in_tree = [0]
    edges   = set()
    adj     = {i: [] for i in range(n)}

    for v in perm:
        u = rng.choice(in_tree)
        e = tuple(sorted([u, v]))
        edges.add(e)
        adj[u].append(v)
        adj[v].append(u)
        in_tree.append(v)

    # 追加辺 (n//3 本)
    for _ in range(n // 3):
        for _ in range(30):
            u = rng.randint(0, n - 1)
            v = rng.randint(0, n - 1)
            e = tuple(sorted([u, v]))
            if u != v and e not in edges:
                edges.add(e)
                adj[u].append(v)
                adj[v].append(u)
                break

    return nodes, sorted(edges), adj


def _graph_frame(node_states, visited_edges, gn_list, ge_list,
                 base, msg, color="lightgreen", finished=False):
    COLOR_MAP = {
        "default": "#4472C4",
        "active":  "#ffcc44",
        "visited": "#44aa44",
        "queued":  "#ff8844",
        "start":   "#cc44ff",
    }
    nodes = []
    for nd in gn_list:
        state = node_states.get(nd["id"], "default")
        col   = COLOR_MAP.get(state, "#4472C4")
        hl    = col if state != "default" else None
        nodes.append({**nd, "color": col, "highlight": hl})

    edges = []
    for u, v in ge_list:
        key = frozenset([u, v])
        edges.append({"from": u, "to": v, "directed": False,
                      "highlight": key in visited_edges})

    return _f([{"id": "graph", "type": "graph_view",
                "nodes": nodes, "edges": edges, "label": "Graph", "weight": 1}],
              base + [{"message": msg, "color": color}], finished=finished)


def graph_dfs(n, **kwargs):
    """Ch.11: 深さ優先探索 (DFS)"""
    N = max(4, min(int(n), 24))
    gn_list, ge_list, adj = _make_random_graph(N)

    base    = [{"message": f"深さ優先探索 (DFS)  N={N}  (Ch.11)", "color": "white"}]
    start   = 0
    states  = {i: "default" for i in range(N)}
    v_edges = set()

    def frame(msg, color="lightgreen", finished=False):
        return _graph_frame(states, v_edges, gn_list, ge_list, base, msg, color, finished)

    visited = set()
    stack   = []
    order   = []

    yield frame(f"グラフ初期状態  N={N}  頂点 {N} 個  辺 {len(ge_list)} 本", "cyan")
    states[start] = "start"
    stack.append(start)
    yield frame(f"DFS 開始  N={N}  start={start}  スタックに {start} をプッシュ", "cyan")

    while stack:
        u = stack.pop()
        if u in visited:
            continue
        visited.add(u)
        order.append(u)
        states[u] = "active"
        yield frame(f"Pop {u}  訪問順: {order}", "yellow")

        states[u] = "visited"
        pushed = []
        for w in sorted(adj[u], reverse=True):
            if w not in visited:
                stack.append(w)
                states[w] = "queued"
                v_edges.add(frozenset([u, w]))
                pushed.append(w)
        yield frame(f"ノード {u} 訪問済み  隣接: {sorted(pushed)} をスタックへ", "lightgreen")

    yield frame(f"DFS 完了  訪問順: {order}", "#44aa44", finished=True)


def graph_bfs(n, **kwargs):
    """Ch.11: 幅優先探索 (BFS)"""
    from collections import deque
    N = max(4, min(int(n), 24))
    gn_list, ge_list, adj = _make_random_graph(N)

    base    = [{"message": f"幅優先探索 (BFS)  N={N}  (Ch.11)", "color": "white"}]
    start   = 0
    states  = {i: "default" for i in range(N)}
    v_edges = set()

    def frame(msg, color="lightgreen", finished=False):
        return _graph_frame(states, v_edges, gn_list, ge_list, base, msg, color, finished)

    visited = set()
    queue   = deque()
    order   = []

    yield frame(f"グラフ初期状態  N={N}  頂点 {N} 個  辺 {len(ge_list)} 本", "cyan")
    visited.add(start)
    queue.append(start)
    states[start] = "start"
    yield frame(f"BFS 開始  N={N}  start={start}  キューに {start} を追加", "cyan")

    while queue:
        u = queue.popleft()
        order.append(u)
        states[u] = "active"
        yield frame(f"Dequeue {u}  訪問順: {order}", "yellow")

        states[u] = "visited"
        enqueued = []
        for w in sorted(adj[u]):
            if w not in visited:
                visited.add(w)
                queue.append(w)
                states[w] = "queued"
                v_edges.add(frozenset([u, w]))
                enqueued.append(w)
        yield frame(f"ノード {u} 訪問済み  隣接: {enqueued} をキューへ", "lightgreen")

    yield frame(f"BFS 完了  訪問順: {order}", "#44aa44", finished=True)


# ===========================================================================
# Ch.10: ハッシュ表 (type: "misc")
# ===========================================================================

def _hash_slot(key=None, hl=None, chain=None):
    return {"key": key, "highlight": hl, "chain": chain or []}

def _hash_obj(id, slots, m, label="", active=-1, weight=1):
    return {"id": id, "type": "hash_table",
            "slots": slots, "m": m, "label": label,
            "active": active, "weight": weight}

def _hash_frame(slots, m, active, base, msg, color="lightgreen", finished=False):
    return _f([_hash_obj("ht", slots, m, label=f"Hash Table  m={m}", active=active)],
              base + [{"message": msg, "color": color}], finished=finished)


def hash_open_addressing(n, **kwargs):
    """Ch.10: 開番地法 (線形探索) によるハッシュ表"""
    from random import sample

    def _next_prime(x):
        def _is_prime(v):
            if v < 2: return False
            for i in range(2, int(v**0.5) + 1):
                if v % i == 0: return False
            return True
        while not _is_prime(x):
            x += 1
        return x

    N = max(5, min(int(n), 24))
    M = _next_prime(max(11, int(N * 1.6)))   # 空きスロットを確保する素数
    INSERT_VALS = sample(range(1, 200), N)

    base = [{"message": f"ハッシュ表 (開番地法/線形探索)  m={M}  (Ch.10)", "color": "white"}]

    table  = [None] * M   # None = 空
    slots  = [_hash_slot() for _ in range(M)]

    def h(k): return k % M

    yield _hash_frame(slots, M, -1, base, f"ハッシュ表初期化  m={M}  h(k) = k mod {M}")

    for v in INSERT_VALS:
        idx   = h(v)
        probe = idx
        steps = 0
        # 線形探索でスロットを探す
        while table[probe] is not None and steps < M:
            slots_tmp = [_hash_slot(table[i]) for i in range(M)]
            slots_tmp[probe] = _hash_slot(table[probe], hl="#ff8844")
            yield _hash_frame(slots_tmp, M, probe, base,
                              f"insert({v}): h({v})={idx}  [{probe}] 衝突!  次のスロットへ",
                              color="orange")
            probe = (probe + 1) % M
            steps += 1

        table[probe] = v
        slots = [_hash_slot(table[i]) for i in range(M)]
        slots[probe] = _hash_slot(v, hl="#44ff88")
        yield _hash_frame(slots, M, probe, base,
                          f"insert({v}): [{probe}] に格納  h({v})={idx}"
                          + (f"  (探索{steps}回)" if steps > 0 else ""),
                          color="lightgreen")
        slots = [_hash_slot(table[i]) for i in range(M)]

    # 探索フェーズ
    not_in_oa = next(x for x in range(1, 200) if x not in set(INSERT_VALS))
    search_targets = [INSERT_VALS[1], INSERT_VALS[N//2], not_in_oa]
    for target in search_targets:
        idx   = h(target)
        probe = idx
        steps = 0
        found = False
        while steps < M:
            slots_tmp = [_hash_slot(table[i]) for i in range(M)]
            slots_tmp[probe] = _hash_slot(table[probe], hl="yellow")
            yield _hash_frame(slots_tmp, M, probe, base,
                              f"search({target}): [{probe}]={table[probe]}  {'→ 発見!' if table[probe]==target else '→ 次へ'}",
                              color="lightgreen" if table[probe] == target else "cyan")
            if table[probe] == target:
                found = True
                break
            if table[probe] is None:
                break
            probe = (probe + 1) % M
            steps += 1
        slots_tmp = [_hash_slot(table[i]) for i in range(M)]
        if found:
            slots_tmp[probe] = _hash_slot(table[probe], hl="#44ff88")
        yield _hash_frame(slots_tmp, M, -1, base,
                          f"search({target}): {'Found' if found else 'Not Found'}",
                          color="#44ff88" if found else "#ff6655")
        slots = [_hash_slot(table[i]) for i in range(M)]

    yield _hash_frame(slots, M, -1, base,
                      "ハッシュ表 (開番地法) 完了", "#44aa44", finished=True)


def hash_chaining(n, **kwargs):
    """Ch.10: チェイン法によるハッシュ表"""
    from random import sample

    def _next_prime(x):
        def _is_prime(v):
            if v < 2: return False
            for i in range(2, int(v**0.5) + 1):
                if v % i == 0: return False
            return True
        while not _is_prime(x):
            x += 1
        return x

    N = max(5, min(int(n), 24))
    M = _next_prime(max(5, N // 2))          # チェイン法: バケツ数 ≈ N/2
    INSERT_VALS = sample(range(1, 200), N)

    base = [{"message": f"ハッシュ表 (チェイン法)  m={M}  (Ch.10)", "color": "white"}]

    chains = [[] for _ in range(M)]

    def h(k): return k % M

    def make_slots(hl_idx=-1, hl_chain_idx=-1):
        s = []
        for i in range(M):
            hl = "yellow" if i == hl_idx else None
            s.append({"key": f"[{i}]" if chains[i] else None,
                       "highlight": hl,
                       "chain": list(chains[i]),
                       "chainHL": {hl_chain_idx: "#44ff88"} if hl_chain_idx >= 0 and i == hl_idx else {}})
        return s

    yield _hash_frame(make_slots(), M, -1, base,
                      f"ハッシュ表初期化  m={M}  h(k) = k mod {M}")

    for v in INSERT_VALS:
        idx = h(v)
        chains[idx].append(v)
        slots = make_slots(hl_idx=idx, hl_chain_idx=len(chains[idx])-1)
        yield _hash_frame(slots, M, idx, base,
                          f"insert({v}): h({v})={idx}  チェイン[{idx}]に追加  → {list(chains[idx])}",
                          color="lightgreen")

    # 探索
    not_in_ch = next(x for x in range(1, 200) if x not in set(INSERT_VALS))
    search_targets = [INSERT_VALS[0], INSERT_VALS[N//2], not_in_ch]
    for target in search_targets:
        idx = h(target)
        slots = make_slots(hl_idx=idx)
        yield _hash_frame(slots, M, idx, base,
                          f"search({target}): h({target})={idx}  チェイン[{idx}]を線形探索",
                          color="cyan")
        found = False
        for j, v in enumerate(chains[idx]):
            s2 = make_slots(hl_idx=idx, hl_chain_idx=j)
            yield _hash_frame(s2, M, idx, base,
                              f"search({target}): chain[{idx}][{j}]={v}  {'→ 発見!' if v==target else '→ 次へ'}",
                              color="lightgreen" if v == target else "cyan")
            if v == target:
                found = True
                break
        if not found:
            yield _hash_frame(make_slots(), M, -1, base,
                              f"search({target}): Not Found", color="#ff6655")

    yield _hash_frame(make_slots(), M, -1, base,
                      "ハッシュ表 (チェイン法) 完了", "#44aa44", finished=True)


# ===========================================================================
# Ch.8: B木 (type: "misc")
# ===========================================================================

class _BTNode:
    __slots__ = ('keys', 'children', 'leaf')
    def __init__(self, leaf=True):
        self.keys     = []
        self.children = []
        self.leaf     = leaf


def _bt_clone(node):
    if node is None:
        return None
    n = _BTNode(node.leaf)
    n.keys     = list(node.keys)
    n.children = [_bt_clone(c) for c in node.children]
    return n


def _bt_node_to_dict(node, hl_map=None):
    if node is None:
        return None
    hl = [(hl_map or {}).get(k) for k in node.keys]
    return {
        "keys":      list(node.keys),
        "highlight": hl,
        "children":  [_bt_node_to_dict(c, hl_map) for c in node.children],
    }


def _bt_obj(id, root, hl_map=None, t=2, label="", weight=1):
    return {"id": id, "type": "btree_view",
            "root": _bt_node_to_dict(root, hl_map),
            "t": t, "label": label, "weight": weight}


def _bt_split_child(parent, i, t):
    """parent.children[i] が満杯 → 分割して中央値を parent に昇格"""
    full  = parent.children[i]
    mid   = t - 1
    med   = full.keys[mid]

    new_c       = _BTNode(full.leaf)
    new_c.keys  = full.keys[mid + 1:]
    if not full.leaf:
        new_c.children = full.children[t:]

    full.keys = full.keys[:mid]
    if not full.leaf:
        full.children = full.children[:t]

    parent.keys.insert(i, med)
    parent.children.insert(i + 1, new_c)
    return med


def bt_operations(n, **kwargs):
    """Ch.8: B木 (t=2) の挿入を可視化"""
    from random import sample
    t        = 2
    MAX_KEYS = 2 * t - 1
    N        = max(5, min(int(n), 24))
    vals     = sample(range(1, 200), N)

    base = [{"message": f"B木  t={t} (2-3-4木)  N={N}  (Ch.8)", "color": "white"}]

    root = [_BTNode(leaf=True)]  # root[0] so it can be reassigned in nested scope

    def snap_bt(hl=None, msg="", color="lightgreen", finished=False):
        r = root[0] if root[0].keys else None
        return _f([_bt_obj("btree", r, hl, t, f"B木  t={t}")],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield snap_bt(msg="B木 初期化 (空)")

    for v in vals:
        yield snap_bt(msg=f"insert({v}) 開始  ─ 挿入位置を探索", color="cyan")

        # 根が満杯なら先に分割
        if len(root[0].keys) == MAX_KEYS:
            new_root          = _BTNode(leaf=False)
            new_root.children = [root[0]]
            med = _bt_split_child(new_root, 0, t)
            root[0] = new_root
            yield _f([_bt_obj("btree", root[0], {med: "orange"}, t, f"B木  t={t}")],
                     base + [{"message": f"insert({v}): 根が満杯 → 分割  中央値={med} が新根へ",
                              "color": "orange"}])

        # 降下しながら挿入
        node = root[0]
        while not node.leaf:
            i = len(node.keys) - 1
            while i >= 0 and v < node.keys[i]:
                i -= 1
            i += 1

            yield _f([_bt_obj("btree", root[0], {k: "#44aaff" for k in node.keys}, t, f"B木  t={t}")],
                     base + [{"message": f"insert({v}): node={node.keys}  → children[{i}] へ降下",
                              "color": "cyan"}])

            child = node.children[i]
            if len(child.keys) == MAX_KEYS:
                med = _bt_split_child(node, i, t)
                yield _f([_bt_obj("btree", root[0], {med: "orange"}, t, f"B木  t={t}")],
                         base + [{"message": f"insert({v}): children[{i}] が満杯 → 分割  中央値={med}",
                                  "color": "orange"}])
                if v > med:
                    i += 1
            node = node.children[i]

        # 葉に挿入
        idx = len(node.keys)
        node.keys.append(None)
        while idx > 0 and v < node.keys[idx - 1]:
            node.keys[idx] = node.keys[idx - 1]
            idx -= 1
        node.keys[idx] = v

        yield _f([_bt_obj("btree", root[0], {v: "#44ff88"}, t, f"B木  t={t}")],
                 base + [{"message": f"insert({v}) 完了  葉={node.keys}", "color": "lightgreen"}])

    yield snap_bt(msg=f"B木 構築完了  {N}個挿入", finished=True)


# ===========================================================================
# Ch.7: 二分木の走査 (Sample7_2)
# ===========================================================================

def _make_complete_btree(vals):
    """配列から完全二分木を構築 (index ベース)"""
    N = len(vals)
    def build(i):
        if i >= N:
            return None
        return {
            "key":       vals[i],
            "color":     "#4472C4",
            "highlight": None,
            "dim":       False,
            "left":      build(2 * i + 1),
            "right":     build(2 * i + 2),
        }
    return build(0)


def _clone_bt(node, visited_keys=None, active_key=None):
    """二分木をディープコピーし、visited_keys を highlight 付きで返す"""
    if node is None:
        return None
    v = node["key"]
    is_active  = (active_key  is not None and v == active_key)
    is_visited = (visited_keys is not None and v in visited_keys)
    hl = "yellow" if is_active else ("#44aa44" if is_visited else None)
    return {
        "key":       v,
        "color":     node.get("color", "#4472C4"),
        "highlight": hl,
        "dim":       False,
        "left":      _clone_bt(node["left"],  visited_keys, active_key),
        "right":     _clone_bt(node["right"], visited_keys, active_key),
    }


def _bfs_order(root):
    from collections import deque
    order = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            continue
        order.append(node["key"])
        q.append(node["left"])
        q.append(node["right"])
    return order


def _preorder(root):
    if root is None:
        return []
    return [root["key"]] + _preorder(root["left"]) + _preorder(root["right"])


def _inorder(root):
    if root is None:
        return []
    return _inorder(root["left"]) + [root["key"]] + _inorder(root["right"])


def _postorder(root):
    if root is None:
        return []
    return _postorder(root["left"]) + _postorder(root["right"]) + [root["key"]]


def _bst_obj(id_, root_dict, label="", weight=3):
    return {"id": id_, "type": "bst_tree", "root": root_dict,
            "label": label, "weight": weight}


def btree_traversals(n, **kwargs):
    """Ch.7: 二分木の BFS / DFS 前順・中順・後順 (Sample7_2)"""
    from random import sample as _sample
    N = max(4, min(int(n), 15))
    vals = _sample(range(1, 100), N)
    root = _make_complete_btree(vals)

    base = [{"message": f"完全二分木  N={N}", "color": "white"}]

    # ── 初期フレーム (全ノード未訪問) ──
    yield _f([_bst_obj("tree", _clone_bt(root))], base)

    traversals = [
        ("BFS (幅優先・レベル順)",     _bfs_order(root)),
        ("DFS 前順 (pre-order: 根→左→右)", _preorder(root)),
        ("DFS 中順 (in-order:  左→根→右)", _inorder(root)),
        ("DFS 後順 (post-order: 左→右→根)", _postorder(root)),
    ]

    for tname, order in traversals:
        visited = set()
        # タイトルフレーム
        yield _f([_bst_obj("tree", _clone_bt(root))],
                 base + [{"message": f"── {tname} ──", "color": "cyan"}])

        for key in order:
            visited.add(key)
            tree_snap = _clone_bt(root, visited_keys=visited - {key}, active_key=key)
            seq_str = " → ".join(str(k) for k in order[:len(visited)])
            yield _f(
                [_bst_obj("tree", tree_snap)],
                base + [
                    {"message": f"── {tname} ──", "color": "cyan"},
                    {"message": f"訪問: {key}", "color": "yellow"},
                    {"message": f"順序: {seq_str}", "color": "lightgreen"},
                ],
            )

        # 完了フレーム（全ノード緑）
        seq_str = " → ".join(str(k) for k in order)
        yield _f(
            [_bst_obj("tree", _clone_bt(root, visited_keys=set(order)))],
            base + [
                {"message": f"── {tname} 完了 ──", "color": "cyan"},
                {"message": f"順序: {seq_str}", "color": "#44aa44"},
            ],
        )

    yield _f(
        [_bst_obj("tree", _clone_bt(root, visited_keys=set(vals)))],
        base + [{"message": "全走査完了", "color": "#44aa44"}],
        finished=True,
    )


# ===========================================================================
# Ch.7: 演算木の構築 (Sample7_3)
# ===========================================================================

def _expr_node_dict(node_id, key, color="#c87040",
                    highlight=None, dim=False, left=None, right=None):
    return {"key": key, "color": color, "highlight": highlight,
            "dim": dim, "left": left, "right": right, "_id": node_id}


def _build_expr_tree(tokens):
    """RPN トークンリストから演算木を構築し、ルートを返す。
    各ノードに一意の _id (連番) を付与する。"""
    stack = []
    _ctr = [0]
    OPERATORS = set("+-*/")

    def new_id():
        _ctr[0] += 1
        return _ctr[0]

    for tok in tokens:
        nid = new_id()
        if tok in OPERATORS:
            right = stack.pop()
            left  = stack.pop()
            node = _expr_node_dict(nid, tok, color="#c05020", left=left, right=right)
        else:
            node = _expr_node_dict(nid, tok, color="#4472C4")
        stack.append(node)
    return stack[0]


def _clone_expr_tree(node, done_ids, active_id=None):
    """演算木をコピー。done_ids に含まれないノードは dim=True。"""
    if node is None:
        return None
    nid = node["_id"]
    is_done   = nid in done_ids
    is_active = nid == active_id
    hl = "yellow" if is_active else ("#44aa44" if is_done else None)
    return {
        "key":       node["key"],
        "color":     node["color"],
        "highlight": hl,
        "dim":       not is_done,
        "left":      _clone_expr_tree(node["left"],  done_ids, active_id),
        "right":     _clone_expr_tree(node["right"], done_ids, active_id),
        "_id":       nid,
    }


def _all_ids(node):
    if node is None:
        return []
    return [node["_id"]] + _all_ids(node["left"]) + _all_ids(node["right"])


def _postorder_nodes(node):
    """ノードオブジェクトを後順で返す (演算木構築順 = 後順)"""
    if node is None:
        return []
    return _postorder_nodes(node["left"]) + _postorder_nodes(node["right"]) + [node]


def expression_tree(n, **kwargs):
    """Ch.7: 演算木の構築 (RPN → スタック → 二分木) (Sample7_3)"""
    # データ数に応じてプリセット式を選択
    PRESETS = [
        (["2", "3", "+"],                                "2 + 3",              3),
        (["4", "2", "-", "3", "*"],                      "(4-2) × 3",          5),
        (["2", "3", "+", "8", "1", "-", "*"],            "(2+3) × (8-1)",      7),
        (["5", "1", "-", "4", "2", "+", "*", "3", "/"],  "((5-1)×(4+2)) ÷ 3", 9),
    ]
    level = max(0, min(int(n) // 6 - 1, len(PRESETS) - 1))
    tokens, expr_str, _ = PRESETS[level]

    base = [
        {"message": f"演算木の構築: {expr_str}", "color": "white"},
        {"message": f"逆ポーランド記法 (RPN): {' '.join(tokens)}", "color": "cyan"},
    ]

    # 完全な演算木を事前構築
    full_tree = _build_expr_tree(tokens)
    all_node_ids = set(_all_ids(full_tree))

    # スタック状態 (表示用: リスト of 文字列)
    OPERATORS = set("+-*/")

    def _tree_to_str(node):
        if node is None:
            return ""
        if node["left"] is None and node["right"] is None:
            return node["key"]
        return f"({_tree_to_str(node['left'])}{node['key']}{_tree_to_str(node['right'])})"

    def _frame(objs, extra_texts, finished=False):
        return _f(objs, base + extra_texts, finished=finished,
                  text_position="bottom")

    # ── 初期フレーム: トークンテープ + 全ノード dim ──
    token_cells = _c("tokens", tokens, label="RPN トークン", weight=1)
    tree_snap   = _clone_expr_tree(full_tree, done_ids=set())
    yield _frame(
        [token_cells, _bst_obj("tree", tree_snap, label="演算木", weight=2.5)],
        [{"message": "スタック: []", "color": "lightgreen"}],
    )

    # full_tree の後順リスト = tokens の順序（RPN の性質）
    postorder_full = _postorder_nodes(full_tree)

    sim_stack2 = []
    done_ids2  = set()

    for i, (tok, node) in enumerate(zip(tokens, postorder_full)):
        nid = node["_id"]
        hl_map = {i: "yellow"}
        token_cells = _c("tokens", tokens, label="RPN トークン", hl=hl_map, weight=1)

        done_ids2.add(nid)
        tree_snap = _clone_expr_tree(full_tree, done_ids=done_ids2, active_id=nid)

        if tok in OPERATORS:
            r = sim_stack2.pop()
            l = sim_stack2.pop()
            sim_stack2.append(node)
            stack_disp = [_tree_to_str(nd) for nd in sim_stack2]
            msg = f"演算子 '{tok}': 2値をポップ → ノード作成 → プッシュ"
        else:
            sim_stack2.append(node)
            stack_disp = [_tree_to_str(nd) for nd in sim_stack2]
            msg = f"オペランド '{tok}' をプッシュ"

        stack_str = "[" + ",  ".join(stack_disp) + "]"
        yield _frame(
            [token_cells, _bst_obj("tree", tree_snap, label="演算木", weight=2.5)],
            [
                {"message": msg, "color": "yellow"},
                {"message": f"スタック: {stack_str}", "color": "lightgreen"},
            ],
        )

    # ── 完了フレーム ──
    result_str = _tree_to_str(full_tree)
    yield _frame(
        [_c("tokens", tokens, label="RPN トークン", weight=1),
         _bst_obj("tree", _clone_expr_tree(full_tree, done_ids=all_node_ids),
                  label="演算木", weight=2.5)],
        [{"message": f"構築完了  演算木 = {result_str}", "color": "#44aa44"}],
        finished=True,
    )


# ===========================================================================
# アルゴリズム一覧 / データサイズ一覧
# ===========================================================================

AlgorithmList = [
    # ── Ch.3: vector / イテレータ ──
    ("vector capacity – 2倍拡張  (Ch.3)",    vector_capacity_double,  {"type": "misc"}),
    ("vector capacity – 固定+16拡張  (Ch.3)", vector_capacity_fixed16, {"type": "misc"}),
    ("vector 操作  (Ch.3)",        vector_ops,         {"type": "misc"}),
    ("イテレータ・3要素合計  (Ch.3)", iterator_sum3,      {"type": "misc"}),
    # ── Ch.4: 連結リスト ──
    ("片方向連結リスト  (Ch.4)",              singly_linked_list,      {"type": "misc"}),
    ("イテレータ・4要素平均  (Ch.4)",         singly_linked_list_avg4, {"type": "misc"}),
    ("双方向連結リスト  (Ch.4)",              doubly_linked_list,      {"type": "misc"}),
    # ── Ch.5: スタック / キュー / RPN ──
    ("連結リストスタック  (Ch.5)",  stack_linked_list,  {"type": "misc"}),
    ("連結リストキュー  (Ch.5)",    queue_linked_list,  {"type": "misc"}),
    ("配列スタック  (Ch.5)",        stack_array,        {"type": "misc"}),
    ("循環キュー  (Ch.5)",          queue_circular,     {"type": "misc"}),
    ("RPN 変換・評価  (Ch.5)",      rpn_eval,           {"type": "misc"}),
    # ── Ch.6: 二分探索木 ──
    ("BST 挿入・探索・削除  (Ch.6)", bst_operations,    {"type": "misc"}),
    # ── Ch.7: 二分木走査 / 演算木 ──
    ("二分木の走査 BFS/DFS  (Ch.7)", btree_traversals,  {"type": "misc"}),
    ("演算木の構築  (Ch.7)",         expression_tree,   {"type": "misc"}),
    # ── Ch.8: 赤黒木・B木 ──
    ("赤黒木 挿入  (Ch.8)",         rb_tree_insert,     {"type": "misc"}),
    ("B木 挿入  (Ch.8)",            bt_operations,      {"type": "misc"}),
    # ── Ch.11: グラフ ──
    ("深さ優先探索 DFS  (Ch.11)",    graph_dfs,          {"type": "misc"}),
    ("幅優先探索 BFS  (Ch.11)",      graph_bfs,          {"type": "misc"}),
    # ── Ch.10: ハッシュ表 ──
    ("ハッシュ表 開番地法  (Ch.10)", hash_open_addressing, {"type": "misc"}),
    ("ハッシュ表 チェイン法  (Ch.10)", hash_chaining,    {"type": "misc"}),
]

DataSizeList = [8, 12, 16, 20, 24, 32, 48, 64, 96, 128, 192, 256]
