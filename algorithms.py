"""
algorithms.py – AAforDataStructures
データ構造アニメーション (Ch.3: vector / Ch.4: 連結リスト)

オブジェクト種別:
  array1d_cells  – 正方形セル配列
  linked_list    – 矢印接続ノード列
"""

import random
from random import randint

# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------

def _f(objects, texts=None, finished=False, found=None, text_position="top", result=None):
    return {"objects": objects, "texts": texts or [], "finished": finished,
            "found": found, "text_position": text_position, "result": result}

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

def _stack_v(id, values, top, max_size, label="", hl=None, weight=1, pad_bottom=0):
    return {
        "id": id, "type": "stack_v",
        "values": list(values), "top": int(top), "max_size": int(max_size),
        "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "weight": weight,
        "pad_bottom": pad_bottom,
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


# ---------------------------------------------------------------------------
# 操作列ヘルパー (vector_ops / singly_linked_list / doubly_linked_list 共用)
# ---------------------------------------------------------------------------

def _op_list_obj(ops_labels, current_idx, weight=1.2):
    """操作列を表示する op_list オブジェクトを生成する"""
    return {
        "id":          "oplist",
        "type":        "op_list",
        "ops":         list(ops_labels),
        "current_idx": current_idx,
        "label":       "操作列",
        "weight":      weight,
    }

def _parse_op_list(ops_strs):
    """文字列リスト ["add(5)", "deleteNode(3)"] → [{"op":..., "args":..., "display":...}]"""
    import re as _re
    result = []
    for s in ops_strs:
        s = s.strip()
        if not s or s.startswith("#"):
            continue
        m = _re.match(r'(\w+)\s*\(([^)]*)\)', s)
        if m:
            name     = m.group(1)
            args_str = m.group(2).strip()
            args     = []
            for tok in (args_str.split(",") if args_str else []):
                tok = tok.strip()
                if tok:
                    try:
                        args.append(int(tok))
                    except ValueError:
                        args.append(tok)   # 文字列引数 ("end" など)
        else:
            parts = s.split()
            name  = parts[0]
            args  = []
            for tok in parts[1:]:
                try:
                    args.append(int(tok))
                except ValueError:
                    args.append(tok)
        result.append({"op": name, "args": args, "display": s})
    return result


# ===========================================================================
# Ch.3: vector / イテレータ (type: "misc")
# ===========================================================================

def vector_capacity(n, scheme="double", **kwargs):
    """Sample3_1: vector の push_back で capacity が変化する様子を可視化
    scheme="double"  : 満杯になるたびに capacity を 2倍に拡張
    scheme="fixed16" : 満杯になるたびに capacity を +16 ずつ拡張
    再確保時は旧配列・新配列を並列表示してコピーをアニメーション。
    """
    init_data = kwargs.get("init_data")
    if init_data and len(init_data) >= 1:
        push_vals = [max(1, min(999, int(v))) for v in init_data]
        N = len(push_vals)
    else:
        N = max(4, min(int(n), 256))
        seed_vals = [5, 2, 7, 1, 5, 10, 100, 25, 99,
                     42, 77, 33, 88, 14, 61, 50]
        _rng_cap = random.Random(kwargs.get("seed", 0))
        push_vals = (seed_vals + [_rng_cap.randint(1, 99)
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
                  unused_from=size)

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
    """Sample3_2: vector の push_back / erase / insert / find_erase / reverse 操作列
    ユーザーが操作列を指定可能 (ops kwarg)。デフォルトは従来の固定シーケンス。
    利用可能操作: push_back(x) / erase(i) / insert(i,x) / find_erase(x) / reverse()
    """
    base      = [{"message": "vector 操作列  (Sample3_2)", "color": "white"}]
    init_data = kwargs.get("init_data")
    ops_strs  = kwargs.get("ops")

    if init_data and len(init_data) >= 1:
        v = [max(1, min(999, int(x))) for x in init_data]
    else:
        v = [2, 3, 4, 5, 6]

    # 操作列の組み立て
    if ops_strs:
        ops = _parse_op_list(ops_strs)
    else:
        ops = [
            {"op": "push_back",  "args": [2],    "display": "push_back(2)"},
            {"op": "push_back",  "args": [7],    "display": "push_back(7)"},
            {"op": "push_back",  "args": [1],    "display": "push_back(1)"},
            {"op": "push_back",  "args": [5],    "display": "push_back(5)"},
            {"op": "push_back",  "args": [3],    "display": "push_back(3)"},
            {"op": "find_erase", "args": [5],    "display": "erase(find(5))"},
            {"op": "insert",     "args": [0, 4], "display": "insert(0, 4)"},
            {"op": "insert",     "args": [2, 6], "display": "insert(2, 6)"},
            {"op": "push_back",  "args": [10],   "display": "push_back(10)"},
            {"op": "erase",      "args": [3],    "display": "erase(3)"},
            {"op": "reverse",    "args": [],     "display": "reverse()"},
        ]

    ops_labels = [op["display"] for op in ops]
    total      = len(ops)

    def mk_frame(hl=None, op_idx=-1, msg="", color="lightgreen",
                 finished=False, extra_objs=None):
        vec_obj = _c("vec", list(v), f"vector  size={len(v)}", hl=hl or {}, weight=2)
        ol_obj  = _op_list_obj(ops_labels, op_idx, weight=1.2)
        objs    = (extra_objs + [ol_obj]) if extra_objs else [vec_obj, ol_obj]
        return _f(objs, base + ([{"message": msg, "color": color}] if msg else []),
                  finished=finished)

    # 初期フレーム: 初期状態 + 操作列全体を提示
    yield mk_frame(op_idx=-1, msg=f"初期状態: {list(v)}")

    for i, op in enumerate(ops):
        name = op["op"]
        args = op["args"]

        if name == "push_back":
            x = args[0] if args else 0
            v.append(x)
            yield mk_frame({len(v)-1: "yellow"}, op_idx=i,
                           msg=f"push_back({x})  →  size={len(v)}")

        elif name == "erase":
            idx = args[0] if args else 0
            if 0 <= idx < len(v):
                yield mk_frame({idx: "#ff4444"}, op_idx=i,
                               msg=f"erase({idx}): v[{idx}]={v[idx]} を削除", color="orange")
                v.pop(idx)
                yield mk_frame(op_idx=i, msg=f"erase 後: {list(v)}")
            else:
                yield mk_frame(op_idx=i, msg=f"erase({idx}): インデックスが範囲外", color="orange")

        elif name == "find_erase":
            x = args[0] if args else 0
            if x in v:
                idx = v.index(x)
                yield mk_frame({idx: "yellow"}, op_idx=i,
                               msg=f"find({x}) → index={idx}")
                yield mk_frame({idx: "#ff4444"}, op_idx=i,
                               msg=f"erase(find({x})): v[{idx}]={v[idx]} を削除", color="orange")
                v.pop(idx)
                yield mk_frame(op_idx=i, msg=f"erase 後: {list(v)}")
            else:
                yield mk_frame(op_idx=i, msg=f"find({x}): 値が見つからない", color="orange")

        elif name == "insert":
            if len(args) >= 2:
                idx, x = args[0], args[1]
            else:
                idx, x = 0, (args[0] if args else 0)
            idx = max(0, min(idx, len(v)))
            v.insert(idx, x)
            yield mk_frame({idx: "yellow"}, op_idx=i,
                           msg=f"insert({idx}, {x}): index={idx} に {x} を挿入")

        elif name == "reverse":
            t = list(v); t.reverse()
            yield mk_frame(
                op_idx=i,
                extra_objs=[
                    _c("vec", list(v), "vector v",                 weight=1.5),
                    _c("rev", t,       "vector t  (reverse後)",
                       hl={j: "#4488ff" for j in range(len(t))},   weight=1.5),
                ],
                msg=f"t = v をコピーして t.reverse()  →  {t}", color="cyan")

    yield mk_frame(op_idx=total, msg="完了", color="#44aa44", finished=True)


def iterator_sum3(n, **kwargs):
    """Sample3_3: イテレータで 3 要素ずつの合計を計算"""
    init_data = kwargs.get("init_data")
    if init_data and len(init_data) >= 1:
        data = [max(1, min(999, int(x))) for x in init_data]
        N = len(data)
    else:
        N_raw = max(6, min(int(n), 30))
        # 3 の倍数の場合は -1 して端数グループを必ず含める
        N = N_raw - 1 if N_raw % 3 == 0 else N_raw
        rng = random.Random(kwargs.get("seed"))
        data = [rng.randint(1, 99) for _ in range(N)]

    full_grps = N // 3
    remainder = N % 3
    grp_info  = f"= {full_grps}×3 + 端数{remainder}" if remainder else f"= {full_grps}×3"
    base = [{"message": f"イテレータ: 3 要素ずつの合計  N={N} {grp_info}  (Sample3_3)",
             "color": "white"}]

    output = []
    i = 0

    def out_c(out_hl=None):
        if not output:
            return _c("output", [0], "Output (空)", unused_from=0, weight=1.0)
        return _c("output", list(output), f"Output  ({len(output)} 要素)",
                  hl=out_hl, weight=1.0)

    def vars_obj(sum_val, count_val, sum_hl=None, count_hl=None):
        hl = {}
        if sum_hl:   hl[0] = sum_hl
        if count_hl: hl[1] = count_hl
        return _c("vars_cell", [sum_val, count_val], "sum  /  count",
                  hl=hl or None, weight=0.45)

    def mk(head, sum_val=0, count_val=0, sum_hl=None, count_hl=None,
           sum_mode=False, out_hl=None, extra=None, finished=False):
        if sum_mode:
            var_c = _c("vars_cell", [sum_val], "sum",
                       hl={0: "cyan"}, weight=0.45)
        else:
            var_c = vars_obj(sum_val, count_val, sum_hl, count_hl)
        return _f([
            _tape("input", data, head, "Input", weight=1.5),
            var_c,
            out_c(out_hl),
        ], base + (extra or []), finished=finished)

    # 初期フレーム
    yield mk(0)

    while i < N:
        grp      = [i + k for k in range(3) if i + k < N]
        is_partial = len(grp) < 3   # 端数グループ

        # 端数グループの予告
        if is_partial:
            yield mk(i, extra=[{
                "message": f"端数グループ: 残り {len(grp)} 要素 ({len(grp)}/3)",
                "color": "#ffaa44"}])

        # テープを 1 要素ずつスキャンしながら sum/count セルを更新
        partial = 0
        for step, idx in enumerate(grp):
            partial += data[idx]
            cnt = step + 1
            msg_color = "#ffaa44" if is_partial else "lightgreen"
            yield mk(idx, partial, cnt, sum_hl="yellow", count_hl="yellow",
                     extra=[{"message": f"it → data[{idx}] = {data[idx]}  ({cnt}/{len(grp)})  sum = {partial}",
                             "color": msg_color}])

        s = partial
        output.append(s)

        # グループ完了: vars セルを sum 単体に差し替え、output 末尾を黄色で確定
        sum_str   = " + ".join(str(data[j]) for j in grp)
        done_color = "#ffaa44" if is_partial else "cyan"
        suffix     = f"  ※端数グループ ({len(grp)}/3 要素)" if is_partial else ""
        yield mk(grp[-1], s, sum_mode=True,
                 out_hl={len(output) - 1: "#ffff44"},
                 extra=[{"message": f"sum = {sum_str} = {s}{suffix}",
                         "color": done_color}])

        # sum/count セルをリセット（次のグループへ）
        if i + len(grp) < N:
            yield mk(grp[-1],
                     out_hl={len(output) - 1: "#44aa44"},
                     extra=[{"message": f"{len(output)} 個の合計を計算済み", "color": "#44aa44"}])

        i += len(grp)

    # 完了フレーム
    yield mk(N - 1, s, sum_mode=True, finished=True,
             extra=[{"message": f"完了: {len(output)} 個の合計を計算", "color": "#44aa44"}])


# ===========================================================================
# Ch.4: 連結リスト (type: "misc")
# ===========================================================================

def singly_linked_list(n, **kwargs):
    """Sample4_2: 片方向連結リストの操作 (add / addFirst / deleteFirst / deleteNode / find)
    ユーザーが操作列を指定可能 (ops kwarg)。デフォルトは従来の固定シーケンス。
    利用可能操作: add(x) / addFirst(x) / deleteFirst() / deleteNode(x) / find(x)
    """
    init_data = kwargs.get("init_data")
    ops_strs  = kwargs.get("ops")
    _rng      = random.Random(kwargs.get("seed", 0))

    if init_data and len(init_data) >= 2:
        data = [max(1, min(999, int(x))) for x in init_data]
        N    = len(data)
    else:
        N    = max(4, min(int(n), 20))
        data = [_rng.randint(1, 99) for _ in range(N)]

    # 操作列の組み立て
    if ops_strs:
        ops = _parse_op_list(ops_strs)
    else:
        del1_v  = data[min(1, N - 1)]
        first_v = _rng.randint(1, 99)
        find_v  = data[N // 2]
        del2_v  = data[max(0, N - 2)]
        ops = (
            [{"op": "add", "args": [v], "display": f"add({v})"} for v in data]
            + [
                {"op": "deleteNode",  "args": [del1_v],  "display": f"deleteNode({del1_v})"},
                {"op": "addFirst",    "args": [first_v], "display": f"addFirst({first_v})"},
                {"op": "deleteFirst", "args": [],        "display": "deleteFirst()"},
                {"op": "find",        "args": [find_v],  "display": f"find({find_v})"},
                {"op": "deleteNode",  "args": [del2_v],  "display": f"deleteNode({del2_v})"},
            ]
        )

    base       = [{"message": "片方向連結リスト  (Sample4_2)", "color": "white"}]
    ops_labels = [op["display"] for op in ops]
    total      = len(ops)
    vals       = []

    def mk_frame(hl=None, op_idx=-1, msg="", color="lightgreen", finished=False):
        ll_obj = _ll("list", list(vals), f"Singly Linked List  (size={len(vals)})",
                     hl=hl or {}, is_doubly=False, weight=2)
        ol_obj = _op_list_obj(ops_labels, op_idx, weight=1.2)
        return _f([ll_obj, ol_obj],
                  base + ([{"message": msg, "color": color}] if msg else []),
                  finished=finished, text_position="bottom")

    def _delete_traverse_frames(target, op_idx):
        """値 target を線形探索して削除するフレーム列を yield"""
        idx = vals.index(target)
        for j in range(idx + 1):
            found = (vals[j] == target)
            hl    = {j: "#ff4444" if found else "yellow"}
            ll_hl = _ll("list", list(vals), f"Singly Linked List  (size={len(vals)})",
                        hl=hl, is_doubly=False, weight=2)
            yield _f([ll_hl, _op_list_obj(ops_labels, op_idx, weight=1.2)],
                     base + [{"message": f"[{j}] = {vals[j]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}],
                     text_position="bottom")
        vals.pop(idx)

    # 初期フレーム: 空リスト + 操作列全体を提示
    yield mk_frame(op_idx=-1, msg="連結リスト生成 (空)")

    for i, op in enumerate(ops):
        name = op["op"]
        args = op["args"]

        if name == "add":
            x = args[0] if args else 0
            vals.append(x)
            yield mk_frame({len(vals)-1: "yellow"}, op_idx=i,
                           msg=f"add({x})  →  size={len(vals)}")

        elif name == "addFirst":
            x = args[0] if args else 0
            vals.insert(0, x)
            yield mk_frame({0: "yellow"}, op_idx=i,
                           msg=f"addFirst({x})  →  size={len(vals)}")

        elif name == "deleteFirst":
            if not vals:
                yield mk_frame(op_idx=i, msg="deleteFirst(): リストが空", color="orange")
            else:
                old = vals[0]
                ll_hl = _ll("list", list(vals), f"Singly Linked List  (size={len(vals)})",
                            hl={0: "#ff4444"}, is_doubly=False, weight=2)
                yield _f([ll_hl, _op_list_obj(ops_labels, i, weight=1.2)],
                         base + [{"message": f"deleteFirst(): 先頭 {old} を削除",
                                  "color": "orange"}],
                         text_position="bottom")
                vals.pop(0)
                head_str = f"  先頭={vals[0]}" if vals else ""
                yield mk_frame(op_idx=i,
                               msg=f"deleteFirst() 完了  →  size={len(vals)}{head_str}")

        elif name == "deleteNode":
            x = args[0] if args else 0
            if x not in vals:
                yield mk_frame(op_idx=i, msg=f"deleteNode({x}): 値 {x} は存在しない",
                               color="orange")
            else:
                yield mk_frame(op_idx=i, msg=f"deleteNode({x}): 値 {x} を線形探索...")
                yield from _delete_traverse_frames(x, i)
                yield mk_frame(op_idx=i,
                               msg=f"deleteNode({x}) 完了  →  size={len(vals)}")

        elif name == "find":
            x = args[0] if args else 0
            yield mk_frame(op_idx=i, msg=f"find({x}): 線形探索...")
            found_flag = False
            for j in range(len(vals)):
                found = (vals[j] == x)
                hl    = {j: "#ff4444" if found else "yellow"}
                ll_hl = _ll("list", list(vals), f"Singly Linked List  (size={len(vals)})",
                            hl=hl, is_doubly=False, weight=2)
                yield _f([ll_hl, _op_list_obj(ops_labels, i, weight=1.2)],
                         base + [{"message": f"[{j}] = {vals[j]}  {'→ 発見!' if found else '→ 次へ'}",
                                  "color": "red" if found else "lightgreen"}],
                         text_position="bottom")
                if found:
                    found_flag = True
                    break
            if not found_flag:
                yield mk_frame(op_idx=i, msg=f"find({x}): 見つからなかった", color="orange")

    yield mk_frame(op_idx=total, msg=f"全操作完了  size={len(vals)}",
                   color="#44aa44", finished=True)


def singly_linked_list_avg4(n, **kwargs):
    """Sample4_7: 片方向連結リスト + イテレータで 4 要素ずつの平均を計算"""
    init_data = kwargs.get("init_data")
    if init_data and len(init_data) >= 1:
        data = [max(1, min(999, int(x))) for x in init_data]
        N = len(data)
    else:
        N_raw = max(5, min(int(n), 32))
        # 4 の倍数の場合は -1 して端数グループを必ず含める
        N = N_raw - 1 if N_raw % 4 == 0 else N_raw
        rng = random.Random(kwargs.get("seed"))
        data = [rng.randint(1, 99) for _ in range(N)]

    full_grps = N // 4
    remainder = N % 4
    grp_info  = f"= {full_grps}×4 + 端数{remainder}" if remainder else f"= {full_grps}×4"
    base = [{"message": f"イテレータ: 4 要素ずつの平均  N={N} {grp_info}  (Sample4_7)",
             "color": "white"}]

    vals   = list(data)
    output = []

    def out_obj(out_hl=None):
        if not output:
            return _c("out", [0], "Output (空)", unused_from=0, weight=0.7)
        return _c("out", list(output), f"Output  ({len(output)} 要素)",
                  hl=out_hl, weight=0.7)

    def vars_obj(sum_val, count_val, sum_hl=None, count_hl=None):
        hl = {}
        if sum_hl:   hl[0] = sum_hl
        if count_hl: hl[1] = count_hl
        return _c("vars_cell", [sum_val, count_val], "sum  /  count",
                  hl=hl or None, weight=0.45)

    def frame(hl=None, msg="", color="lightgreen", finished=False,
              sum_val=0, count_val=0, sum_hl=None, count_hl=None,
              avg_mode=False, avg_val=0, out_hl=None):
        if avg_mode:
            var_c = _c("vars_cell", [avg_val], "avg",
                       hl={0: "cyan"}, weight=0.45)
        else:
            var_c = vars_obj(sum_val, count_val, sum_hl, count_hl)
        return _f(
            [_ll("list", list(vals), f"Singly Linked List  (N={N})",
                 hl=hl or {}, is_doubly=False, weight=1.4),
             var_c,
             out_obj(out_hl)],
            base + [{"message": msg, "color": color}],
            finished=finished, text_position="bottom")

    # 初期フレーム: リスト全体を表示
    yield frame(msg=f"リストを生成  size={N}  (イテレータ it = begin())")

    i = 0
    avg = 0
    while i < N:
        grp_end    = min(i + 4, N)
        grp_size   = grp_end - i
        is_partial = grp_size < 4
        scanned    = []
        run_sum    = 0

        # 端数グループの予告
        if is_partial:
            yield frame(
                msg=f"端数グループ: 残り {grp_size} 要素 ({grp_size}/4)",
                color="#ffaa44")

        # グループ内を 1 ノードずつイテレータで走査
        for step, idx in enumerate(range(i, grp_end)):
            run_sum += vals[idx]
            scanned.append(idx)
            hl = {s: "#4488cc" for s in scanned[:-1]}
            hl[idx] = "yellow"
            msg_color = "#ffaa44" if is_partial else "lightgreen"
            yield frame(
                hl=hl,
                msg=f"it → node[{idx}] = {vals[idx]}  ({step + 1}/{grp_size} 要素目)  sum = {run_sum}",
                color=msg_color,
                sum_val=run_sum, count_val=step + 1,
                sum_hl="yellow", count_hl="yellow")

        # 平均を計算して output へ追加
        avg = run_sum // grp_size
        output.append(avg)
        sum_str    = " + ".join(str(vals[j]) for j in range(i, grp_end))
        hl_done    = {j: "#44aa44" for j in range(i, grp_end)}
        done_color = "#ffaa44" if is_partial else "cyan"
        suffix     = f"  ※端数グループ ({grp_size}/4 要素)" if is_partial else ""
        yield frame(
            hl=hl_done,
            msg=f"avg = ({sum_str}) / {grp_size} = {run_sum} / {grp_size} = {avg}{suffix}",
            color=done_color,
            avg_mode=True, avg_val=avg,
            out_hl={len(output) - 1: "#ffff44"})

        if grp_end < N:
            yield frame(
                msg=f"{len(output)} 個の平均を計算済み", color="#44aa44",
                out_hl={len(output) - 1: "#44aa44"})

        i = grp_end

    yield frame(msg=f"完了: {len(output)} 個の平均を計算", color="#44aa44",
                avg_mode=True, avg_val=avg, finished=True)


def doubly_linked_list(n, **kwargs):
    """Sample4_5: 双方向連結リストの操作 (add / addFirst / deleteNode / display / displayReverse / reverse)
    ユーザーが操作列を指定可能 (ops kwarg)。デフォルトは従来の固定シーケンス。
    利用可能操作: add(x) / addFirst(x) / deleteNode(x) / display() / displayReverse() / reverse()
    """
    init_data = kwargs.get("init_data")
    ops_strs  = kwargs.get("ops")

    if ops_strs is None:
        # デフォルト操作列を構築
        if init_data and len(init_data) >= 2:
            add_seq = [max(1, min(999, int(x))) for x in init_data]
        else:
            add_seq = [3, 8, 5, 4, 1]
        del1_v      = add_seq[-1]
        del2_v      = add_seq[0]
        add_first_v = 6
        ops = (
            [{"op": "add",    "args": [v], "display": f"add({v})"} for v in add_seq]
            + [
                {"op": "deleteNode",    "args": [del1_v],      "display": f"deleteNode({del1_v})"},
                {"op": "deleteNode",    "args": [del2_v],      "display": f"deleteNode({del2_v})"},
                {"op": "addFirst",      "args": [add_first_v], "display": f"addFirst({add_first_v})"},
                {"op": "display",       "args": [],            "display": "display()"},
                {"op": "displayReverse","args": [],            "display": "displayReverse()"},
                {"op": "reverse",       "args": [],            "display": "reverse()"},
            ]
        )
    else:
        ops = _parse_op_list(ops_strs)

    base       = [{"message": "双方向連結リスト  (Sample4_5)", "color": "white"}]
    ops_labels = [op["display"] for op in ops]
    total      = len(ops)
    vals       = []

    def mk_frame(hl=None, op_idx=-1, msg="", color="lightgreen", finished=False):
        ll_obj = _ll("list", list(vals), f"Doubly Linked List  (size={len(vals)})",
                     hl=hl or {}, is_doubly=True, weight=2)
        ol_obj = _op_list_obj(ops_labels, op_idx, weight=1.2)
        return _f([ll_obj, ol_obj],
                  base + ([{"message": msg, "color": color}] if msg else []),
                  finished=finished, text_position="bottom")

    def _delete_traverse_frames(target, op_idx):
        """値 target を線形探索して削除するフレーム列を yield"""
        idx = vals.index(target)
        for j in range(idx + 1):
            found = (vals[j] == target)
            hl    = {j: "#ff4444" if found else "yellow"}
            ll_hl = _ll("list", list(vals), f"Doubly Linked List  (size={len(vals)})",
                        hl=hl, is_doubly=True, weight=2)
            yield _f([ll_hl, _op_list_obj(ops_labels, op_idx, weight=1.2)],
                     base + [{"message": f"[{j}] = {vals[j]}  {'→ 削除!' if found else '→ 次へ'}",
                              "color": "red" if found else "lightgreen"}],
                     text_position="bottom")
        vals.pop(idx)

    # 初期フレーム: 空リスト + 操作列全体を提示
    yield mk_frame(op_idx=-1, msg="双方向連結リスト生成 (空)")

    for i, op in enumerate(ops):
        name = op["op"]
        args = op["args"]

        if name == "add":
            x = args[0] if args else 0
            vals.append(x)
            yield mk_frame({len(vals)-1: "yellow"}, op_idx=i,
                           msg=f"add({x})  →  size={len(vals)}")

        elif name == "addFirst":
            x = args[0] if args else 0
            vals.insert(0, x)
            yield mk_frame({0: "yellow"}, op_idx=i,
                           msg=f"addFirst({x})  →  size={len(vals)}")

        elif name == "deleteNode":
            x = args[0] if args else 0
            if x not in vals:
                yield mk_frame(op_idx=i, msg=f"deleteNode({x}): 値 {x} は存在しない",
                               color="orange")
            else:
                yield mk_frame(op_idx=i, msg=f"deleteNode({x}): 値 {x} を線形探索...")
                yield from _delete_traverse_frames(x, i)
                yield mk_frame(op_idx=i,
                               msg=f"deleteNode({x}) 完了  →  size={len(vals)}")

        elif name == "display":
            yield mk_frame(op_idx=i, msg="display(): 先頭から順方向に走査 →")
            for j in range(len(vals)):
                hl    = {j: "yellow"}
                ll_hl = _ll("list", list(vals), "Doubly Linked List  (→)",
                            hl=hl, is_doubly=True, weight=2)
                yield _f([ll_hl, _op_list_obj(ops_labels, i, weight=1.2)],
                         base + [{"message": f"→  {vals[j]}", "color": "lightgreen"}],
                         text_position="bottom")

        elif name == "displayReverse":
            yield mk_frame(op_idx=i, msg="displayReverse(): 末尾から逆順に走査 ←")
            for j in range(len(vals) - 1, -1, -1):
                hl    = {j: "yellow"}
                ll_hl = _ll("list", list(vals), "Doubly Linked List  (←)",
                            hl=hl, is_doubly=True, weight=2)
                yield _f([ll_hl, _op_list_obj(ops_labels, i, weight=1.2)],
                         base + [{"message": f"←  {vals[j]}", "color": "cyan"}],
                         text_position="bottom")

        elif name == "reverse":
            rev = list(reversed(vals))
            ll_orig = _ll("list", list(vals), "元のリスト", is_doubly=True)
            ll_rev  = _ll("rev",  rev,        "reversed リスト", is_doubly=True)
            ol_obj  = _op_list_obj(ops_labels, i, weight=1.2)
            yield _f([ll_orig, ll_rev, ol_obj],
                     base + [{"message": f"reverse(): 逆順リストを生成  →  {rev}",
                              "color": "cyan"}],
                     text_position="bottom")
            vals[:] = rev

        else:
            yield mk_frame(op_idx=i, msg=f"不明な操作: {op['display']}", color="orange")

    yield mk_frame(op_idx=total, msg=f"全操作完了  size={len(vals)}",
                   color="#44aa44", finished=True)


# ===========================================================================
# Ch.5: スタック / キュー / RPN (type: "misc")
# ===========================================================================

def stack_linked_list(n, **kwargs):
    """Sample5_1: 連結リストによるスタックの Push/Pop（縦方向表示）"""
    init_data = kwargs.get("init_data")
    push_seq  = [max(1, min(999, int(x))) for x in init_data] if init_data else [3, 7, 1, 5, 2, 8]
    pop_count = max(1, len(push_seq) // 2)   # 前半をポップ

    base = [{"message": "連結リストスタック  (Sample5_1)", "color": "white"}]
    vals = []   # vals[0] = top (先頭が top)

    def frame(hl=None, msg="", color="lightgreen", finished=False):
        return _f([_ll("stack", list(vals), "Stack  (top → bottom)",
                       hl=hl or {}, is_doubly=False, is_vertical=True,
                       ptr_labels=["top", "bottom"], ptr_colors=["#44cc66", "#4499dd"])],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg="スタック生成 (空)")

    for v in push_seq:
        vals.insert(0, v)
        yield frame({0: "yellow"}, msg=f"Push({v})  top={vals[0]}  size={len(vals)}")

    yield frame(msg=f"isEmpty? = {len(vals) == 0}", color="cyan")

    for _ in range(min(pop_count, len(vals))):
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
    init_data = kwargs.get("init_data")
    enq_seq   = [max(1, min(999, int(x))) for x in init_data] if init_data else [3, 7, 1, 5, 2, 8]
    deq_count = max(1, len(enq_seq) // 2)

    base = [{"message": "連結リストキュー  (Sample5_8)", "color": "white"}]
    vals = []   # vals[0] = front, vals[-1] = back

    def frame(hl=None, msg="", color="lightgreen", finished=False):
        return _f([_ll("queue", list(vals), "Queue  front → … → back",
                       hl=hl or {}, is_doubly=False,
                       ptr_labels=["front", "back"], ptr_colors=["#44cc66", "#ff8844"])],
                  base + [{"message": msg, "color": color}], finished=finished,
                  text_position="bottom")

    yield frame(msg="キュー生成 (空)")

    for v in enq_seq:
        vals.append(v)
        yield frame({len(vals) - 1: "yellow"},
                    msg=f"Enqueue({v})  back={vals[-1]}  size={len(vals)}")

    yield frame(msg=f"isEmpty? = {len(vals) == 0}", color="cyan")

    for _ in range(min(deq_count, len(vals))):
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
    init_data = kwargs.get("init_data")
    MAXSIZE   = 8
    push_seq  = [max(1, min(999, int(x))) for x in init_data][:MAXSIZE] if init_data else [3, 7, 1, 5, 2, 8]
    pop_count = max(1, len(push_seq) // 2)

    base = [{"message": "配列スタック  (Sample5_4)", "color": "white"}]
    data = [0] * MAXSIZE
    top  = -1

    def frame(hl_extra=None, msg="", color="lightgreen", finished=False):
        hl = hl_extra or {}
        return _f([_stack_v("stack", list(data), top, MAXSIZE,
                            f"Stack  max={MAXSIZE}", hl=hl)],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(msg="スタック生成 (空)  top=-1")

    for v in push_seq:
        top += 1
        data[top] = v
        yield frame({top: "yellow"}, msg=f"Push({v})  →  top={top}")

    yield frame(msg=f"isFull? = {top == MAXSIZE - 1}", color="cyan")

    for _ in range(min(pop_count, top + 1)):
        val = data[top]
        yield frame({top: "#ff4444"}, msg=f"Pop() = {val}  (top={top})", color="orange")
        data[top] = 0
        top -= 1
        yield frame(msg=f"Pop 完了  top={top}")

    for v in [9, 4]:
        if top + 1 < MAXSIZE:
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
    init_data = kwargs.get("init_data")
    MAXSIZE   = 8
    # 最初の Enqueue 列: MAXSIZE-2 以下に制限（後で追加 Enqueue して循環を見せるため）
    if init_data:
        enq_seq1 = [max(1, min(999, int(x))) for x in init_data][: MAXSIZE - 2]
    else:
        enq_seq1 = [1, 2, 3, 4, 5, 6]
    deq_count = max(1, len(enq_seq1) // 2)

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

    for v in enq_seq1:
        data[back] = v
        back = (back + 1) % MAXSIZE
        count += 1
        yield frame({(back - 1) % MAXSIZE: "yellow"},
                    msg=f"Enqueue({v})  count={count}  back={back % MAXSIZE}")

    yield frame(msg=f"isFull? = {count == MAXSIZE}", color="cyan")

    for _ in range(min(deq_count, count)):
        val = data[front]
        yield frame({front: "#ff4444"}, msg=f"Dequeue() = {val}  front={front}", color="orange")
        data[front] = 0
        front = (front + 1) % MAXSIZE
        count -= 1
        yield frame(msg=f"Dequeue 完了  count={count}  front={front}")

    # 循環ラップを見せる追加 Enqueue
    for v in [7, 8, 9, 10]:
        if count < MAXSIZE:
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
    """Sample5_6 + Sample5_2: B型式(中置記法)→ A型式(RPN)変換 + スタック評価"""
    # init_data: B型式の式文字列（空白除去済み）を受け取る
    _ALLOWED = set("0123456789+-*/()")
    init_data = kwargs.get("init_data")
    if init_data:
        raw = "".join(str(x) for x in init_data).replace(" ", "")
        expr = list(raw) if raw and all(c in _ALLOWED for c in raw) else list("(2+3)*(8-1)")
    else:
        expr = list("(2+3)*(8-1)")
    expr_str = "".join(expr)
    base = [{"message": f"B型式(中置) → A型式(RPN)  式: {expr_str}", "color": "white"}]

    oprs   = []   # 演算子スタック (Sample5_6: Stack_char oprs)
    output = []   # RPN 出力トークン
    opr    = ' '  # 直前の演算子を一時保存 (Sample5_6: char opr = ' ')

    # 変換フェーズの演算子スタック最大深さを事前推定
    _oprs_max = max(3, sum(1 for c in expr if c == '(') + 1)

    def cvt_frame(ci, msg, color="lightgreen"):
        e_hl = {j: "#4466aa" for j in range(ci)}   # 処理済み: 薄青
        e_hl[ci] = "#bb66ff"                        # 現在位置: 紫
        s_hl      = {len(oprs) - 1: "#ff8844"} if oprs else {}
        o_hl      = {i: "#ffff44" for i in range(len(output))}
        opr_color = "cyan" if opr != ' ' else "#888888"
        # row レイアウト: [Opr/Oprs] 縦並び左 → [B型式/RPN] 縦並び右 (2×2 グリッド)
        row_obj = {"type": "row", "weight": 1, "children": [
            {"type": "col", "weight": 1.2, "children": [
                _c("opr_var", [opr if opr != ' ' else '空'], "Opr",
                   hl={0: opr_color}, weight=1),
                _stack_v("oprs", list(oprs), len(oprs) - 1, _oprs_max,
                         "Oprs", hl=s_hl, weight=1),
            ]},
            {"type": "col", "weight": 1.5, "children": [
                _c("expr", expr,         f"B型式: {expr_str}", hl=e_hl, weight=1),
                _c("out",  list(output), f"A型式(RPN) ({len(output)} トークン)",
                   hl=o_hl, weight=1),
            ]},
        ]}
        return _f([row_obj], base + [{"message": msg, "color": color}])

    yield cvt_frame(0, "変換開始  (Sample5_6)")

    # ── B型式(中置記法) → A型式(RPN) 変換  ≡ Sample5_6.cpp ──
    for ci, c in enumerate(expr):
        if c in '+-*/':
            opr = c
            yield cvt_frame(ci, f"演算子 '{c}' を opr に保存", color="cyan")
        elif c == '(':
            if opr != ' ':
                oprs.append(opr)
                opr = ' '
                yield cvt_frame(ci, f"'(' → opr '{oprs[-1]}' をスタックに Push", color="#ff8844")
            else:
                yield cvt_frame(ci, "'(' スキップ  (opr なし)")
        elif c == ')':
            if oprs:
                popped = oprs.pop()
                output.append(popped)
                yield cvt_frame(ci, f"')' → Pop '{popped}' して RPN 出力", color="orange")
        elif c.isdigit():
            output.append(c)
            yield cvt_frame(ci, f"数字 '{c}' → RPN 出力", color="lightgreen")
            if opr != ' ':
                output.append(opr)
                opr = ' '
                yield cvt_frame(ci, f"保存演算子 '{output[-1]}' も RPN 出力", color="cyan")

    while oprs:
        popped = oprs.pop()
        output.append(popped)
        yield cvt_frame(len(expr) - 1, f"残り演算子 '{popped}' → RPN 出力", color="orange")

    rpn_str = " ".join(output)
    o_hl = {i: "#44aaff" for i in range(len(output))}
    yield _f([_c("rpn", list(output), f"A型式(RPN): {rpn_str}", hl=o_hl)],
             base + [{"message": f"変換完了!  RPN = {rpn_str}", "color": "cyan"}])

    # ── A型式(RPN) 評価フェーズ  ≡ Sample5_2.cpp ──
    base2 = [{"message": f"A型式(RPN) 評価: {rpn_str}  (Sample5_2)", "color": "white"}]
    nums  = []
    # 評価フェーズの数値スタック最大深さを事前推定（数字トークン数 + 余白）
    _nums_max = max(3, sum(1 for tok in output if tok.isdigit()) + 1)

    def eval_frame(ti, msg, color="lightgreen", finished=False, error=False, result=None):
        r_hl = {j: "#336699" for j in range(ti)}
        if ti < len(output): r_hl[ti] = "#ff4444" if error else "#ff8844"
        n_hl = {len(nums) - 1: "#ff4444" if error else "#44cc66"} if nums else {}
        stack_obj = _stack_v("nums", [str(x) for x in nums], len(nums) - 1, _nums_max,
                             f"数値スタック  ({len(nums)})", hl=n_hl, weight=1)
        rpn_obj   = _c("rpn", list(output), f"A型式(RPN): {rpn_str}", hl=r_hl, weight=2)
        row_obj   = {"type": "row", "weight": 1, "children": [stack_obj, rpn_obj]}
        return _f([row_obj], base2 + [{"message": msg, "color": color}],
                  finished=finished, result=result)

    yield eval_frame(0, "RPN 評価開始  (Sample5_2)")

    for ti, tok in enumerate(output):
        if tok in '+-*/':
            if len(nums) < 2:
                yield eval_frame(ti,
                                 f"エラー: スタックが空 (要素数={len(nums)}) なのに演算子 '{tok}' で Pop しようとしました",
                                 color="#ff4444", finished=True, error=True,
                                 result=f"エラー: '{tok}' — スタックが空")
                return
            b = nums.pop()
            a = nums.pop()
            res = (a + b if tok == '+' else a - b if tok == '-'
                   else a * b if tok == '*' else a // b)
            nums.append(res)
            yield eval_frame(ti, f"Pop {b}, Pop {a}  →  {a} {tok} {b} = {res}  → Push {res}",
                             color="orange")
        elif tok.isdigit():
            nums.append(int(tok))
            yield eval_frame(ti, f"数字 '{tok}' → Push {tok}", color="lightgreen")

    if len(nums) != 1:
        yield eval_frame(len(output) - 1,
                         f"エラー: 評価終了後のスタックが {len(nums)} 要素 (正常は1要素のみ)",
                         color="#ff4444", finished=True, error=True,
                         result=f"エラー: {len(nums)} 要素残存 (正常は1)")
        return
    yield eval_frame(len(output) - 1,
                     f"評価完了!  {expr_str} = {nums[0]}", color="#44aa44",
                     finished=True, result=f"= {nums[0]}")


def rpn_eval_array(n, **kwargs):
    """Sample5_2: A型式(RPN) を配列スタックで評価"""
    # init_data: A型式トークン列（空白区切りで入力）を受け取る
    _ALLOWED_TOK = set("0123456789+-*/")
    init_data = kwargs.get("init_data")
    if init_data:
        raw_tokens = " ".join(str(x) for x in init_data).split()
        if raw_tokens and all(all(c in _ALLOWED_TOK for c in t) for t in raw_tokens):
            tokens = raw_tokens
        else:
            tokens = "2 3 + 8 1 - *".split()
    else:
        tokens = "2 3 + 8 1 - *".split()
    rpn_str = " ".join(tokens)
    base    = [{"message": f"A型式(RPN) 評価: {rpn_str}  (Sample5_2・配列スタック)", "color": "white"}]
    nums    = []   # 配列スタック (Python list として模倣)

    def frame(ci, msg, color="lightgreen", finished=False, error=False, result=None):
        e_hl  = {j: "#336699" for j in range(ci)}
        if 0 <= ci < len(tokens):
            e_hl[ci] = "#ff4444" if error else "#ff8844"
        top   = len(nums) - 1
        s_vals = [str(x) for x in nums]
        s_size = max(1, len(nums))
        s_hl  = {top: "#ff4444" if error else "#44cc66"} if nums else {}
        stack_obj = _stack_v("nums", s_vals, top, s_size,
                             f"数値スタック (配列)  top={top}", hl=s_hl, weight=1)
        expr_obj  = _c("rpn", tokens, f"A型式: {rpn_str}", hl=e_hl, weight=2)
        row_obj   = {"type": "row", "weight": 1, "children": [stack_obj, expr_obj]}
        return _f([row_obj], base + [{"message": msg, "color": color}],
                  finished=finished, result=result)

    yield frame(0, "RPN 評価開始  (Sample5_2: 配列スタック)")

    for ci, tok in enumerate(tokens):
        if tok in '+-*/':
            if len(nums) < 2:
                yield frame(ci,
                            f"エラー: スタックが空 (要素数={len(nums)}) なのに演算子 '{tok}' で Pop しようとしました",
                            color="#ff4444", finished=True, error=True,
                            result=f"エラー: '{tok}' — スタックが空")
                return
            b = nums.pop(); a = nums.pop()
            res = (a + b if tok == '+' else a - b if tok == '-'
                   else a * b if tok == '*' else a // b)
            nums.append(res)
            yield frame(ci, f"Pop {b}, Pop {a} → {a} {tok} {b} = {res} → Push {res}",
                        color="orange")
        elif tok.isdigit():
            nums.append(int(tok))
            yield frame(ci, f"数字 '{tok}' → Push {tok}")

    if len(nums) != 1:
        yield frame(len(tokens) - 1,
                    f"エラー: 評価終了後のスタックが {len(nums)} 要素 (正常は1要素のみ)",
                    color="#ff4444", finished=True, error=True,
                    result=f"エラー: {len(nums)} 要素残存 (正常は1)")
        return
    yield frame(len(tokens) - 1,
                f"評価完了!  {rpn_str} = {nums[0]}", color="#44aa44",
                finished=True, result=f"= {nums[0]}")


def rpn_eval_list(n, **kwargs):
    """Sample5_5: A型式(RPN) を連結リストスタックで評価"""
    # init_data: A型式トークン列（空白区切りで入力）を受け取る
    _ALLOWED_TOK = set("0123456789+-*/")
    init_data = kwargs.get("init_data")
    if init_data:
        raw_tokens = " ".join(str(x) for x in init_data).split()
        if raw_tokens and all(all(c in _ALLOWED_TOK for c in t) for t in raw_tokens):
            tokens = raw_tokens
        else:
            tokens = "2 3 + 8 1 - *".split()
    else:
        tokens = "2 3 + 8 1 - *".split()
    rpn_str = " ".join(tokens)
    base    = [{"message": f"A型式(RPN) 評価: {rpn_str}  (Sample5_5・連結リストスタック)", "color": "white"}]
    nums    = []   # 連結リストスタック (top が先頭)

    def frame(ci, msg, color="lightgreen", finished=False, error=False, result=None):
        e_hl = {j: "#336699" for j in range(ci)}
        if 0 <= ci < len(tokens):
            e_hl[ci] = "#ff4444" if error else "#ff8844"
        ll_hl = {0: "#ff4444" if error else "#44cc66"} if nums else {}
        top_color   = "#ff4444" if error else "#44cc66"
        stack_obj = _ll("stack", list(nums),
                        "スタック  top↑" if nums else "スタック (空)",
                        hl=ll_hl, is_vertical=True,
                        ptr_labels=["top", "bottom"],
                        ptr_colors=[top_color, "#4499dd"],
                        weight=1)
        expr_obj  = _c("rpn", tokens, f"A型式: {rpn_str}", hl=e_hl, weight=2)
        row_obj   = {"type": "row", "weight": 1,
                     "children": [stack_obj, expr_obj]}
        return _f([row_obj], base + [{"message": msg, "color": color}],
                  finished=finished, result=result)

    yield frame(0, "RPN 評価開始  (Sample5_5: 連結リストスタック)")

    for ci, tok in enumerate(tokens):
        if tok in '+-*/':
            if len(nums) < 2:
                yield frame(ci,
                            f"エラー: スタックが空 (要素数={len(nums)}) なのに演算子 '{tok}' で Pop しようとしました",
                            color="#ff4444", finished=True, error=True,
                            result=f"エラー: '{tok}' — スタックが空")
                return
            b = nums.pop(0); a = nums.pop(0)
            res = (a + b if tok == '+' else a - b if tok == '-'
                   else a * b if tok == '*' else a // b)
            nums.insert(0, res)   # 先頭に追加 (push)
            yield frame(ci, f"Pop {b}, Pop {a} → {a} {tok} {b} = {res} → Push {res}",
                        color="orange")
        elif tok.isdigit():
            nums.insert(0, int(tok))   # 先頭に追加 (push)
            yield frame(ci, f"数字 '{tok}' → Push {tok}")

    if len(nums) != 1:
        yield frame(len(tokens) - 1,
                    f"エラー: 評価終了後のスタックが {len(nums)} 要素 (正常は1要素のみ)",
                    color="#ff4444", finished=True, error=True,
                    result=f"エラー: {len(nums)} 要素残存 (正常は1)")
        return
    yield frame(len(tokens) - 1,
                f"評価完了!  {rpn_str} = {nums[0]}", color="#44aa44",
                finished=True, result=f"= {nums[0]}")


def rpn_direct_b(n, **kwargs):
    """Sample5_7_1_2_3: B型式(中置記法)を 0+番兵 + 演算子先行処理で直接計算
    0+番兵アルゴリズムに「演算子を見たとき opr!='' なら先に do_op」を追加
    → 各数値を個別括弧で囲まなくても正しく計算できる
    例: 3*(2-3+(4/2-1*(5-6/(7/(8-9)))))+100 = 97
        (2+3)*(8-1) = 35
    """
    _ALLOWED = set("0123456789+-*/()")
    init_data = kwargs.get("init_data")
    if init_data:
        raw = "".join(str(x) for x in init_data).replace(" ", "")
        expr_str = raw if raw and all(c in _ALLOWED for c in raw) else "(2+3)*(8-1)"
    else:
        expr_str = "(2+3)*(8-1)"

    expr = list(expr_str)
    N    = len(expr)
    base = [{"message": f"B型式直接計算: {expr_str}  (Sample5_7_1_2_3)", "color": "white"}]

    oprs = []   # 演算子スタック（'(' 時に push）
    nums = [0]  # 数値スタック — 初期値 0 を番兵として Push
    opr  = '+'  # 現在保持している演算子（初期値 '+'）

    _depth    = max(2, sum(1 for c in expr if c == '('))
    _oprs_max = _depth
    _nums_max = _depth + 2

    def do_op(op):
        if len(nums) < 2:
            raise IndexError(f"数値スタックが不足 (演算子 '{op}' 適用不可)")
        val2 = nums.pop(); val1 = nums.pop()
        if   op == '+': res = val1 + val2
        elif op == '-': res = val1 - val2
        elif op == '*': res = val1 * val2
        elif op == '/':
            if val2 == 0:
                raise ZeroDivisionError(f"0 除算: {val1} / {val2}")
            res = val1 // val2
        else:
            res = val1 + val2   # フォールバック
        nums.append(res)
        return val1, val2, res

    def frame(ci, msg, color="lightgreen", finished=False):
        e_hl      = {j: "#4466aa" for j in range(ci)}
        if 0 <= ci < N:
            e_hl[ci] = "#bb66ff"
        o_top     = len(oprs) - 1
        n_top     = len(nums) - 1
        o_hl      = {o_top: "#ff8844"} if oprs else {}
        n_hl      = {n_top: "#44cc66"} if nums  else {}
        opr_color = "cyan" if opr not in (' ', '') else "#888888"
        row_obj = {"type": "row", "weight": 1, "children": [
            _stack_v("oprs", list(oprs), o_top, _oprs_max,
                     f"演算子スタック  top={o_top}", hl=o_hl, weight=1.0),
            _stack_v("nums", [str(x) for x in nums], n_top, _nums_max,
                     f"数値スタック  top={n_top}", hl=n_hl, weight=1.0),
            _c("opr_var", [opr if opr not in (' ', '') else '空'], "opr",
               hl={0: opr_color}, weight=0.5),
            _c("expr", expr, f"B型式: {expr_str}", hl=e_hl, weight=1.5),
        ]}
        return _f([row_obj], base + [{"message": msg, "color": color}], finished=finished)

    def error_frame(ci, msg):
        return frame(ci, f"エラー: {msg}", color="#ff4444", finished=True)

    yield frame(0, "初期状態: opr='+', numbers=[0]  (= '0+式' として処理開始)")

    i = 0
    while i < N:
        c = expr[i]

        if c in '+-*/':
            # ★ 演算子を見たとき: 保留中の opr があれば先に適用して番兵0を消費
            if opr != ' ':
                try:
                    v1, v2, res = do_op(opr)
                    yield frame(i, f"先行処理 do_op('{opr}'):  {v1} {opr} {v2} = {res}", color="orange")
                except (IndexError, ZeroDivisionError) as e:
                    yield error_frame(i, str(e)); return
                opr = ' '
            opr = c
            yield frame(i, f"演算子 '{c}' を opr に保存", color="cyan")

        elif c == '(':
            pushed_opr = opr
            oprs.append(opr)
            opr = '+'
            nums.append(0)
            yield frame(i,
                        f"'(' → opr='{pushed_opr}' を oprs に Push / nums に 0 Push / opr='+' にリセット",
                        color="#ff8844")

        elif c == ')':
            # 数字の直後でまだ opr が残っていれば先に適用
            if opr != ' ':
                try:
                    v1, v2, res = do_op(opr)
                    yield frame(i, f"')' 前処理 do_op('{opr}'):  {v1} {opr} {v2} = {res}", color="orange")
                except (IndexError, ZeroDivisionError) as e:
                    yield error_frame(i, str(e)); return
                opr = ' '
            if not oprs:
                yield error_frame(i, "oprs スタックが空なのに ')' が現れました — 括弧が不正です"); return
            popped = oprs.pop()
            opr = popped
            yield frame(i, f"')' → oprs から '{popped}' を Pop → opr='{popped}'", color="#ff8844")
            try:
                v1, v2, res = do_op(opr)
            except (IndexError, ZeroDivisionError) as e:
                yield error_frame(i, str(e)); return
            opr = ' '
            yield frame(i, f"do_op('{popped}'):  {v1} {popped} {v2} = {res}  → opr=' '", color="orange")

        elif c.isdigit():
            num = int(c)
            while i + 1 < N and expr[i + 1].isdigit():
                i += 1
                num = num * 10 + int(expr[i])
            nums.append(num)
            yield frame(i, f"数字 '{num}' → nums に Push", color="lightgreen")
            # 次が ')' または末尾なら即 do_op（従来通り）
            j = i + 1
            while j < N and expr[j] == ' ':
                j += 1
            if j >= N or expr[j] == ')':
                cur_opr = opr
                try:
                    v1, v2, res = do_op(opr)
                except (IndexError, ZeroDivisionError) as e:
                    yield error_frame(i, str(e)); return
                opr = ' '
                yield frame(i, f"次が ')' → do_op('{cur_opr}'):  {v1} {cur_opr} {v2} = {res}  → opr=' '",
                            color="orange")

        i += 1

    result = nums[-1] if nums else '?'
    yield frame(N - 1, f"計算完了!  {expr_str} = {result}", color="#44aa44", finished=True)


# ===========================================================================
# Ch.7: 二分探索木 (type: "misc")
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
    """Ch.7: 二分探索木 (BST) の挿入・探索・削除"""
    # 初期木: 高さ3のランダム形状 (N=4〜6: 4以上で高さ3が確定、7だと完全二分木固定になるため6まで)
    N   = max(4, min(int(n), 6))
    rng = random.Random(kwargs.get("seed", N))
    init_vals = _bst_insertion_order(rng, N, max_depth=3)

    tree = None
    for v in init_vals:
        tree = _bst_insert(tree, v)

    # 挿入値は初期木と重複しないよう別途ランダム生成
    ins_vals = rng.sample([x for x in range(1, 200) if x not in set(init_vals)], 3)
    keys = init_vals + ins_vals

    base = [{"message": f"二分探索木 (BST)  初期木 N={N} (高さ3)  (Ch.7)", "color": "white"}]

    # ── 初期フレーム (初期木を表示) ────────────────────────────────
    yield _f([_bst_obj("bst", tree, label="BST")],
             base + [{"message": f"初期木 (高さ3)  挿入値: {', '.join(map(str, ins_vals))}",
                      "color": "lightgreen"}])

    # ── 挿入フェーズ ─────────────────────────────────────────────────
    for v in ins_vals:
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
             base + [{"message": f"挿入完了  ノード数={len(keys)}", "color": "white"}])

    # ── 探索フェーズ ─────────────────────────────────────────────────
    not_in = next(x for x in range(1, 200) if x not in set(keys))
    search_targets = [init_vals[N // 3], ins_vals[1], not_in]
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
    delete_targets = [ins_vals[0], init_vals[N // 2]]
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


# ─── AVL木 helpers ────────────────────────────────────────────────────────

class _AVLNode:
    __slots__ = ('key', 'height', 'left', 'right')
    def __init__(self, key):
        self.key    = key
        self.height = 1
        self.left   = self.right = None


def _avl_h(nd):  return nd.height if nd else 0
def _avl_bf(nd): return _avl_h(nd.left) - _avl_h(nd.right) if nd else 0
def _avl_uh(nd): nd.height = 1 + max(_avl_h(nd.left), _avl_h(nd.right))

def _avl_rr(y):  # raw right-rotate（イベント記録なし）
    x = y.left; y.left = x.right; x.right = y
    _avl_uh(y); _avl_uh(x); return x

def _avl_rl(x):  # raw left-rotate（イベント記録なし）
    y = x.right; x.right = y.left; y.left = x
    _avl_uh(x); _avl_uh(y); return y


def _avl_nd_to_dict(nd, hl=None):
    """_AVLNode → renderer用 dict (deep copy)"""
    if nd is None: return None
    return {"key": nd.key, "color": "#4472C4",
            "highlight": (hl or {}).get(nd.key),
            "left":  _avl_nd_to_dict(nd.left,  hl),
            "right": _avl_nd_to_dict(nd.right, hl)}


def _avl_apply_hl(d, hl):
    """dict スナップショットにハイライトを上書き（元 dict を変更しない）"""
    if d is None: return None
    return {**d,
            "highlight": hl.get(d["key"]),
            "left":  _avl_apply_hl(d.get("left"),  hl),
            "right": _avl_apply_hl(d.get("right"), hl)}


def _avl_obj_from_dict(id_, root_dict, label="", weight=1, rotation=None):
    obj = {"id": id_, "type": "bst_tree", "root": root_dict,
           "label": label, "weight": weight}
    if rotation:
        obj["rotation"] = rotation
    return obj


class _AVLTree:
    """AVL木 — 挿入・削除時に回転イベントを収集する。Sample8_2 の C++ 実装に対応"""

    def __init__(self):
        self.root  = None
        self._evts = []   # list of (rot_type, bf, pivot_key, snap_before_dict)

    def _snap(self):
        """現在の木全体を dict スナップショットとして返す（回転前の状態保存用）"""
        return _avl_nd_to_dict(self.root)

    # ── 挿入 ─────────────────────────────────────────────────────────
    def _ins(self, nd, key):
        if nd is None:
            return _AVLNode(key)
        if key < nd.key:
            nd.left  = self._ins(nd.left,  key)
        elif key > nd.key:
            nd.right = self._ins(nd.right, key)
        else:
            return nd

        _avl_uh(nd)
        bf = _avl_bf(nd)

        if bf > 1 and key < nd.left.key:        # LL → 右回転
            sb = self._snap()
            r  = _avl_rr(nd)
            self._evts.append(('LL', bf, nd.key, None, sb))
            return r
        if bf < -1 and key > nd.right.key:       # RR → 左回転
            sb = self._snap()
            r  = _avl_rl(nd)
            self._evts.append(('RR', bf, nd.key, None, sb))
            return r
        if bf > 1 and key > nd.left.key:         # LR → 左右二重回転
            child_key = nd.left.key
            sb = self._snap()
            nd.left = _avl_rl(nd.left)
            r = _avl_rr(nd)
            self._evts.append(('LR', bf, nd.key, child_key, sb))
            return r
        if bf < -1 and key < nd.right.key:       # RL → 右左二重回転
            child_key = nd.right.key
            sb = self._snap()
            nd.right = _avl_rr(nd.right)
            r = _avl_rl(nd)
            self._evts.append(('RL', bf, nd.key, child_key, sb))
            return r
        return nd

    def insert(self, key):
        self._evts = []
        self.root  = self._ins(self.root, key)
        return list(self._evts)

    # ── 削除 ─────────────────────────────────────────────────────────
    def _min(self, nd):
        while nd.left: nd = nd.left
        return nd

    def _del(self, nd, key):
        if nd is None: return None
        if key < nd.key:
            nd.left  = self._del(nd.left,  key)
        elif key > nd.key:
            nd.right = self._del(nd.right, key)
        else:
            if nd.left  is None: return nd.right
            if nd.right is None: return nd.left
            s = self._min(nd.right)
            nd.key   = s.key
            nd.right = self._del(nd.right, s.key)

        _avl_uh(nd); bf = _avl_bf(nd)

        if bf > 1 and _avl_bf(nd.left) >= 0:
            sb = self._snap(); r = _avl_rr(nd)
            self._evts.append(('LL', bf, nd.key, None, sb)); return r
        if bf > 1 and _avl_bf(nd.left) < 0:
            child_key = nd.left.key
            sb = self._snap()
            nd.left = _avl_rl(nd.left); r = _avl_rr(nd)
            self._evts.append(('LR', bf, nd.key, child_key, sb)); return r
        if bf < -1 and _avl_bf(nd.right) <= 0:
            sb = self._snap(); r = _avl_rl(nd)
            self._evts.append(('RR', bf, nd.key, None, sb)); return r
        if bf < -1 and _avl_bf(nd.right) > 0:
            child_key = nd.right.key
            sb = self._snap()
            nd.right = _avl_rr(nd.right); r = _avl_rl(nd)
            self._evts.append(('RL', bf, nd.key, child_key, sb)); return r
        return nd

    def delete(self, key):
        self._evts = []
        self.root  = self._del(self.root, key)
        return list(self._evts)

    # ── 探索 ─────────────────────────────────────────────────────────
    def search(self, key):
        path, nd = [], self.root
        while nd:
            path.append(nd.key)
            if key == nd.key: break
            nd = nd.left if key < nd.key else nd.right
        return path


_AVL_ROT_NAMES = {
    'LL': 'LL → 右回転',
    'RR': 'RR → 左回転',
    'LR': 'LR → 左右二重回転',
    'RL': 'RL → 右左二重回転',
}

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
    N   = max(4, min(int(n), 24))
    rng = random.Random(kwargs.get("seed", N))
    vals = rng.sample(range(1, 200), N)

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
# Ch.8 (続き): AVL木 – 挿入・探索・削除 (Sample8_2)
# ===========================================================================

def avl_tree_operations(n, **kwargs):
    """Ch.8: AVL木の挿入・探索・削除 (Sample8_2 相当)"""
    import random
    seed = kwargs.get('seed', 42)
    rng  = random.Random(seed)
    # 初期木: AVL は自己平衡するため N=4〜6 なら高さがちょうど3になる
    # （高さ4には最低7ノード必要）
    # 初期木: AVL は自己平衡するため N=4〜6 なら高さがちょうど3になる
    N    = rng.randint(4, 6)
    init_vals = rng.sample(range(1, 200), N)
    avl  = _AVLTree()
    for v in init_vals:
        avl.insert(v)         # 初期木はアニメーションなしで構築

    # 挿入回数はデータ数 n に追従（初期木の値とは重複しない別の値を挿入）
    INS  = max(1, min(int(n), 40))
    pool = [x for x in range(1, 200) if x not in set(init_vals)]
    ins_vals = rng.sample(pool, min(INS, len(pool)))
    keys = init_vals + ins_vals

    base = [{"message": f"AVL木 (AVL Tree)  初期木 N={N} (高さ3)  (Ch.8)", "color": "white"}]

    def snap(hl=None, msg="", color="white", finished=False):
        return _f([_avl_obj_from_dict("avl",
                                      _avl_nd_to_dict(avl.root, hl or {}),
                                      label="AVL Tree")],
                  base + [{"message": msg, "color": color}],
                  finished=finished)

    def snap_from_dict(root_dict, msg="", color="white", rotation=None):
        return _f([_avl_obj_from_dict("avl", root_dict, label="AVL Tree",
                                      rotation=rotation)],
                  base + [{"message": msg, "color": color}])

    # ── 初期フレーム (初期木を表示) ────────────────────────────────
    ins_preview = ', '.join(map(str, ins_vals[:12])) + (' …' if len(ins_vals) > 12 else '')
    yield snap(msg=f"初期木 (高さ3)  挿入予定 {len(ins_vals)} 個: {ins_preview}",
               color="lightgreen")

    # ── 挿入フェーズ ────────────────────────────────────────────────
    for v in ins_vals:
        path = avl.search(v)
        if path:
            yield snap(hl={k: "yellow" for k in path},
                       msg=f"insert({v}): 挿入位置を探索  path={path}", color="cyan")

        evts = avl.insert(v)

        if not evts:
            h = avl.root.height if avl.root else 0
            yield snap(hl={v: "#44ff88"},
                       msg=f"insert({v}) 完了  回転なし  高さ={h}", color="lightgreen")
        else:
            for rot, bf, pivot, child_key, sb in evts:
                rname = _AVL_ROT_NAMES.get(rot, rot)
                hl = {pivot: "orange"}
                if child_key is not None:
                    hl[child_key] = "#ffaa00"
                # 回転前スナップショット（pivot をオレンジ + 回転弧オーバーレイ）
                yield snap_from_dict(
                    _avl_apply_hl(sb, hl),
                    msg=f"insert({v}): bf={bf:+d} → {rname}  pivot={pivot}",
                    color="orange",
                    rotation={"type": rot, "pivot": pivot, "child": child_key})
            h = avl.root.height if avl.root else 0
            yield snap(hl={v: "#44ff88"},
                       msg=f"insert({v}) 完了  回転あり  高さ={h}", color="lightgreen")

    h = avl.root.height if avl.root else 0
    yield snap(msg=f"挿入完了  ノード数={len(keys)}  木の高さ={h}", color="white")

    # ── 探索フェーズ (挿入回数の約1/3) ──────────────────────────────
    SR = max(1, round(len(ins_vals) / 3))
    not_in = next(x for x in range(1, 200) if x not in set(keys))
    shuffled = list(keys); rng.shuffle(shuffled)
    if SR >= 2:
        search_targets = shuffled[:SR - 1] + [not_in]   # 末尾1個は存在しないキー
    else:
        search_targets = shuffled[:1]
    for target in search_targets:
        path = avl.search(target)
        found = path and path[-1] == target
        for step, k in enumerate(path):
            hl = {k: ("#44ff88" if k == target else "yellow")}
            yield snap(hl=hl,
                       msg=f"search({target}): [{step+1}] key={k}  "
                           f"{'→ 発見!' if k == target else '→ 次へ'}",
                       color="lightgreen" if k == target else "cyan")
        if not found:
            yield snap(msg=f"search({target}): Not Found", color="#ff6655")

    # ── 削除フェーズ (挿入回数の約1/3) ──────────────────────────────
    DEL = max(1, round(len(ins_vals) / 3))
    del_pool = list(keys); rng.shuffle(del_pool)
    delete_targets = del_pool[:DEL]
    for target in delete_targets:
        path = avl.search(target)
        if path and path[-1] == target:
            yield snap(hl={target: "#ff4444"},
                       msg=f"delete({target}): ノードを削除します", color="orange")
            evts = avl.delete(target)
            for rot, bf, pivot, child_key, sb in evts:
                rname = _AVL_ROT_NAMES.get(rot, rot)
                hl = {pivot: "orange"}
                if child_key is not None:
                    hl[child_key] = "#ffaa00"
                yield snap_from_dict(
                    _avl_apply_hl(sb, hl),
                    msg=f"delete({target}): bf={bf:+d} → {rname}  pivot={pivot}",
                    color="orange",
                    rotation={"type": rot, "pivot": pivot, "child": child_key})
            h = avl.root.height if avl.root else 0
            yield snap(msg=f"delete({target}) 完了  高さ={h}", color="lightgreen")

    yield snap(msg="AVL木 操作完了", color="#44aa44", finished=True)


# ===========================================================================
# Ch.11: グラフ – DFS / BFS (type: "misc")
# ===========================================================================

def _make_random_graph(n, seed=None):
    """N ノードのランダム連結無向グラフを生成 (フォースダイレクテッドレイアウト)"""
    import math
    from random import Random
    rng = Random(seed)

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

    # Fruchterman-Reingold フォースダイレクテッドレイアウト
    pos = [[rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9)] for _ in range(n)]
    k = math.sqrt(0.6 / max(n, 1))  # 自然長

    for iteration in range(300):
        t = 0.12 * (1.0 - iteration / 300)  # 温度（冷却）
        disp = [[0.0, 0.0] for _ in range(n)]

        # 反発力（全ノード対）
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[i][0] - pos[j][0]
                dy = pos[i][1] - pos[j][1]
                dist = math.sqrt(dx * dx + dy * dy) + 1e-6
                f = k * k / dist
                disp[i][0] += dx / dist * f
                disp[i][1] += dy / dist * f
                disp[j][0] -= dx / dist * f
                disp[j][1] -= dy / dist * f

        # 引力（辺で結ばれたノード対）
        for u, v in edges:
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = math.sqrt(dx * dx + dy * dy) + 1e-6
            f = dist * dist / k
            disp[u][0] -= dx / dist * f
            disp[u][1] -= dy / dist * f
            disp[v][0] += dx / dist * f
            disp[v][1] += dy / dist * f

        # 変位を適用（温度でクランプ）
        for i in range(n):
            d = math.sqrt(disp[i][0] ** 2 + disp[i][1] ** 2) + 1e-6
            scale = min(d, t) / d
            pos[i][0] = max(0.06, min(0.94, pos[i][0] + disp[i][0] * scale))
            pos[i][1] = max(0.06, min(0.94, pos[i][1] + disp[i][1] * scale))

    nodes = [{"id": i, "label": str(i),
              "x": round(pos[i][0], 3),
              "y": round(pos[i][1], 3)} for i in range(n)]

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
    gn_list, ge_list, adj = _make_random_graph(N, seed=kwargs.get("seed", N))

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
    gn_list, ge_list, adj = _make_random_graph(N, seed=kwargs.get("seed", N))

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


# ---------------------------------------------------------------------------
# ハッシュ表 共通ヘルパー（整数 / 文字列 / 実数 キー対応）
# ---------------------------------------------------------------------------

_HASH_KEY_TYPE_TOKENS = frozenset({"int", "str", "string", "float", "real"})

def _rand_word(rng, length=3):
    """ランダムな大文字 3 文字 (子音–母音–子音) 文字列を生成"""
    _cons = "BCDFGHJKLMNPRSTVWXYZ"
    _vow  = "AEIOU"
    return rng.choice(_cons) + rng.choice(_vow) + rng.choice(_cons)

def _gen_hash_keys(rng, N, key_type):
    """キー型に応じた重複なしキーリストを生成"""
    if key_type == "str":
        keys, seen = [], set()
        attempts = 0
        while len(keys) < N and attempts < 50000:
            w = _rand_word(rng)
            if w not in seen:
                seen.add(w); keys.append(w)
            attempts += 1
        return keys
    elif key_type == "float":
        pool = [round(i * 0.1, 1) for i in range(10, 1000)]   # 1.0 〜 99.9
        return rng.sample(pool, min(N, len(pool)))
    else:  # int
        return rng.sample(range(1, 200), N)

def _not_found_hash_key(rng, key_type, existing):
    """existing に含まれないサンプル探索用キーを 1 つ返す"""
    if key_type == "str":
        k = "ZZZ"
        while k in existing:
            k = _rand_word(rng)
        return k
    elif key_type == "float":
        k = round(rng.uniform(100.1, 199.9), 1)
        while k in existing:
            k = round(rng.uniform(100.1, 199.9), 1)
        return k
    else:
        return next(x for x in range(1, 500) if x not in existing)

def _key_repr(k, key_type):
    """表示用文字列"""
    if k is None:       return "None"
    if key_type == "str":   return f"'{k}'"
    if key_type == "float": return f"{k:.1f}"
    return str(k)

def _parse_hash_init_data(idata, default_m):
    """init_data トークン列から (M, key_type, fn_raw, fn_key) を解析"""
    m_tok = None
    key_type = "int"
    fn_tokens = []
    for t in (idata or []):
        tl = t.lower()
        if t.lstrip("-").isdigit():
            m_tok = t
        elif tl in _HASH_KEY_TYPE_TOKENS:
            key_type = {"string": "str", "real": "float"}.get(tl, tl)
        else:
            fn_tokens.append(t)
    _default_fn = {"int": "mod", "str": "sum", "float": "mult"}
    fn_raw = "".join(fn_tokens).strip() or _default_fn[key_type]
    fn_key = fn_raw.lower()
    M = int(m_tok) if m_tok else default_m
    return M, key_type, fn_raw, fn_key

def _make_hash_fn(key_type, fn_key, fn_raw, M):
    """キー型・関数名からハッシュ関数と説明ラベルを返す"""
    _A = (5 ** 0.5 - 1) / 2   # ≈ 0.6180339887

    if key_type == "str":
        if fn_key == "sum":
            def h(k, _M=M): return sum(ord(c) for c in str(k)) % _M
            label = f"h(k) = Σord(c) mod {M}  [加算折り畳み法]"
        elif fn_key == "poly":
            def h(k, _M=M):
                hv = 0
                for c in str(k): hv = (hv * 31 + ord(c)) % _M
                return hv
            label = f"h(k) = Σ(ord(c)·31ⁱ) mod {M}  [多項式ハッシュ (Horner法)]"
        elif fn_key == "mult":
            def h(k, _M=M, _A=_A):
                return int(_M * ((sum(ord(c) for c in str(k)) * _A) % 1))
            label = f"h(k) = ⌊{M}·(Σord(c)·A mod 1)⌋  A≈0.618  [乗算折り畳み法]"
        else:
            _formula = fn_raw
            def h(k, _f=_formula, _M=M):
                try:
                    return int(eval(_f, {"__builtins__": None},
                                    {"k": k, "m": _M, "int": int, "abs": abs,
                                     "ord": ord, "sum": sum, "len": len, "str": str})) % _M
                except Exception:
                    return sum(ord(c) for c in str(k)) % _M
            label = f"h(k) = {fn_raw}  (m={M})"

    elif key_type == "float":
        if fn_key == "mult":
            def h(k, _M=M, _A=_A): return int(_M * ((k * _A) % 1))
            label = f"h(k) = ⌊{M}·(k·A mod 1)⌋  A≈0.618  [乗算法]"
        elif fn_key == "trunc":
            def h(k, _M=M): return int(k) % _M
            label = f"h(k) = ⌊k⌋ mod {M}  [切り捨て]"
        elif fn_key == "scale":
            def h(k, _M=M): return int(round(k * 100)) % _M
            label = f"h(k) = ⌊k×100⌋ mod {M}  [スケール変換]"
        else:
            _formula = fn_raw
            def h(k, _f=_formula, _M=M):
                try:
                    return int(eval(_f, {"__builtins__": None},
                                    {"k": k, "m": _M, "int": int, "abs": abs,
                                     "round": round, "float": float})) % _M
                except Exception:
                    return int(_M * ((k * _A) % 1))
            label = f"h(k) = {fn_raw}  (m={M})"

    else:  # int
        if fn_key == "mult":
            def h(k, _M=M, _A=_A): return int(_M * ((k * _A) % 1))
            label = f"h(k) = ⌊{M} × (k × A mod 1)⌋   A = (√5−1)/2 ≈ 0.618"
        elif fn_key == "square":
            def h(k, _M=M): return (k * k) % _M
            label = f"h(k) = k² mod {M}"
        elif fn_key not in ("mod", ""):
            _formula = fn_raw
            def h(k, _f=_formula, _M=M):
                try:
                    return int(eval(_f, {"__builtins__": None},
                                    {"k": k, "m": _M, "int": int, "abs": abs})) % _M
                except Exception:
                    return k % _M
            label = f"h(k) = {fn_raw}  (m={M})"
        else:  # mod (default)
            def h(k, _M=M): return k % _M
            label = f"h(k) = k mod {M}"

    return h, label


def hash_open_addressing(n, **kwargs):
    """Ch.10: 開番地法 (線形探索) によるハッシュ表
    init_data: [m] [key_type] [func]
      key_type: int(default) | str | float
      func(int):   mod(default) | mult | square | <式>
      func(str):   sum(default) | poly | mult | <式>
      func(float): mult(default) | trunc | scale | <式>
    """
    def _next_prime(x):
        def _is_prime(v):
            if v < 2: return False
            for i in range(2, int(v**0.5) + 1):
                if v % i == 0: return False
            return True
        while not _is_prime(x):
            x += 1
        return x

    N   = max(5, min(int(n), 24))
    rng = random.Random(kwargs.get("seed", N))

    # ── init_data 解析 ───────────────────────────────────────────
    _idata  = kwargs.get("init_data") or []
    _def_m  = _next_prime(max(11, int(N * 1.6)))
    M, key_type, fn_raw, fn_key = _parse_hash_init_data(_idata, _def_m)
    if M <= N:   # 開番地法: N より十分大きい素数であること
        M = _next_prime(max(11, int(N * 1.6)))

    # ── ハッシュ関数 ─────────────────────────────────────────────
    h, func_label = _make_hash_fn(key_type, fn_key, fn_raw, M)

    INSERT_VALS = _gen_hash_keys(rng, N, key_type)
    kt_label    = {"int": "整数", "str": "文字列", "float": "実数"}[key_type]

    base = [
        {"message": f"ハッシュ表 (開番地法/線形探索)  m={M}  キー: {kt_label}  (Ch.10)", "color": "white"},
        {"message": func_label, "color": "cyan"},
    ]

    table  = [None] * M   # None = 空
    slots  = [_hash_slot() for _ in range(M)]

    yield _hash_frame(slots, M, -1, base, f"ハッシュ表初期化  m={M}")

    for v in INSERT_VALS:
        kr    = _key_repr(v, key_type)
        idx   = h(v)
        probe = idx
        steps = 0
        # 線形探索でスロットを探す
        while table[probe] is not None and steps < M:
            slots_tmp = [_hash_slot(table[i]) for i in range(M)]
            slots_tmp[probe] = _hash_slot(table[probe], hl="#ff8844")
            yield _hash_frame(slots_tmp, M, probe, base,
                              f"insert({kr}): h({kr})={idx}  [{probe}] 衝突!  次のスロットへ",
                              color="orange")
            probe = (probe + 1) % M
            steps += 1

        table[probe] = v
        slots = [_hash_slot(table[i]) for i in range(M)]
        slots[probe] = _hash_slot(v, hl="#44ff88")
        yield _hash_frame(slots, M, probe, base,
                          f"insert({kr}): h({kr})={idx}  → [{probe}] に格納"
                          + (f"  (探索{steps}回)" if steps > 0 else ""),
                          color="lightgreen")
        slots = [_hash_slot(table[i]) for i in range(M)]

    # 探索フェーズ
    existing = set(INSERT_VALS)
    not_in   = _not_found_hash_key(rng, key_type, existing)
    search_targets = [INSERT_VALS[1], INSERT_VALS[N//2], not_in]
    for target in search_targets:
        kr    = _key_repr(target, key_type)
        idx   = h(target)
        probe = idx
        steps = 0
        found = False
        while steps < M:
            slots_tmp = [_hash_slot(table[i]) for i in range(M)]
            slots_tmp[probe] = _hash_slot(table[probe], hl="yellow")
            tab_r = _key_repr(table[probe], key_type)
            yield _hash_frame(slots_tmp, M, probe, base,
                              f"search({kr}): h({kr})={idx}  [{probe}]={tab_r}"
                              f"  {'→ 発見!' if table[probe]==target else '→ 次へ'}",
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
                          f"search({kr}): {'Found' if found else 'Not Found'}",
                          color="#44ff88" if found else "#ff6655")
        slots = [_hash_slot(table[i]) for i in range(M)]

    yield _hash_frame(slots, M, -1, base,
                      "ハッシュ表 (開番地法) 完了", "#44aa44", finished=True)


def hash_chaining(n, **kwargs):
    """Ch.10: チェイン法によるハッシュ表
    init_data: [m] [key_type] [func]
      key_type: int(default) | str | float
      func(int):   mod(default) | mult | square | <式>
      func(str):   sum(default) | poly | mult | <式>
      func(float): mult(default) | trunc | scale | <式>
    """
    def _next_prime(x):
        def _is_prime(v):
            if v < 2: return False
            for i in range(2, int(v**0.5) + 1):
                if v % i == 0: return False
            return True
        while not _is_prime(x):
            x += 1
        return x

    N   = max(5, min(int(n), 24))
    rng = random.Random(kwargs.get("seed", N))

    # ── init_data 解析 ───────────────────────────────────────────
    _idata  = kwargs.get("init_data") or []
    _def_m  = _next_prime(max(5, N // 2))
    M, key_type, fn_raw, fn_key = _parse_hash_init_data(_idata, _def_m)
    if M < 2:
        M = _next_prime(max(5, N // 2))

    # ── ハッシュ関数 ─────────────────────────────────────────────
    h, func_label = _make_hash_fn(key_type, fn_key, fn_raw, M)

    INSERT_VALS = _gen_hash_keys(rng, N, key_type)
    kt_label    = {"int": "整数", "str": "文字列", "float": "実数"}[key_type]

    base = [
        {"message": f"ハッシュ表 (チェイン法)  m={M}  キー: {kt_label}  (Ch.10)", "color": "white"},
        {"message": func_label, "color": "cyan"},
    ]

    chains = [[] for _ in range(M)]

    def make_slots(hl_idx=-1, hl_chain_idx=-1):
        s = []
        for i in range(M):
            hl = "yellow" if i == hl_idx else None
            s.append({"key": f"[{i}]" if chains[i] else None,
                       "highlight": hl,
                       "chain": list(chains[i]),
                       "chainHL": {hl_chain_idx: "#44ff88"} if hl_chain_idx >= 0 and i == hl_idx else {}})
        return s

    yield _hash_frame(make_slots(), M, -1, base, f"ハッシュ表初期化  m={M}")

    for v in INSERT_VALS:
        kr  = _key_repr(v, key_type)
        idx = h(v)
        chains[idx].append(v)
        chain_repr = [_key_repr(x, key_type) for x in chains[idx]]
        slots = make_slots(hl_idx=idx, hl_chain_idx=len(chains[idx])-1)
        yield _hash_frame(slots, M, idx, base,
                          f"insert({kr}): h({kr})={idx}  → チェイン[{idx}]に追加  {chain_repr}",
                          color="lightgreen")

    # 探索
    existing = set(INSERT_VALS)
    not_in   = _not_found_hash_key(rng, key_type, existing)
    search_targets = [INSERT_VALS[0], INSERT_VALS[N//2], not_in]
    for target in search_targets:
        kr  = _key_repr(target, key_type)
        idx = h(target)
        slots = make_slots(hl_idx=idx)
        yield _hash_frame(slots, M, idx, base,
                          f"search({kr}): h({kr})={idx}  → チェイン[{idx}]を線形探索",
                          color="cyan")
        found = False
        for j, v in enumerate(chains[idx]):
            vr = _key_repr(v, key_type)
            s2 = make_slots(hl_idx=idx, hl_chain_idx=j)
            yield _hash_frame(s2, M, idx, base,
                              f"search({kr}): chain[{idx}][{j}]={vr}  {'→ 発見!' if v==target else '→ 次へ'}",
                              color="lightgreen" if v == target else "cyan")
            if v == target:
                found = True
                break
        if not found:
            yield _hash_frame(make_slots(), M, -1, base,
                              f"search({kr}): Not Found", color="#ff6655")

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
    t        = 2
    MAX_KEYS = 2 * t - 1
    N        = max(5, min(int(n), 24))
    rng      = random.Random(kwargs.get("seed", N))
    vals     = rng.sample(range(1, 200), N)

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


def _make_random_btree(vals, rng, max_depth=4):
    """ランダムな形の二分木を構築（深さは max_depth 以下に制限）。
    len(vals) >= 8 かつ max_depth=4 なら高さはちょうど 4 になる
    （深さ3まででは最大7ノードしか収容できないため）。"""
    def mk(v):
        return {"key": v, "color": "#4472C4", "highlight": None,
                "dim": False, "left": None, "right": None}
    root = mk(vals[0])
    for v in vals[1:]:
        while True:
            nd, depth = root, 1
            while True:
                side = "left" if rng.random() < 0.5 else "right"
                if nd[side] is None:
                    break
                nd = nd[side]
                depth += 1
            if depth < max_depth:        # 新ノードは depth+1 段目に入る
                nd[side] = mk(v)
                break
    return root


def _bst_insertion_order(rng, N, max_depth=3):
    """高さ max_depth 以下のランダム形状 BST を作る挿入値列を生成。
    形状を先に決め、ソート済み値を中順で割り当て、
    親が必ず子より先に来るランダム順で返す（この順で挿入すると同じ形が再現される）。"""
    shape = _make_random_btree(list(range(N)), rng, max_depth=max_depth)
    it = iter(sorted(rng.sample(range(1, 200), N)))
    def assign(nd):
        if nd is None:
            return
        assign(nd["left"]); nd["key"] = next(it); assign(nd["right"])
    assign(shape)
    order, frontier = [], [shape]
    while frontier:
        nd = frontier.pop(rng.randrange(len(frontier)))
        order.append(nd["key"])
        frontier += [c for c in (nd["left"], nd["right"]) if c]
    return order


def _clone_bt(node, visited_keys=None, active_key=None, visit_order_map=None):
    """二分木をディープコピーし、visited_keys を highlight 付きで返す。
    visit_order_map: {key: 訪問順番号} を渡すと各ノードに visit_order フィールドを付与。"""
    if node is None:
        return None
    v = node["key"]
    is_active  = (active_key  is not None and v == active_key)
    is_visited = (visited_keys is not None and v in visited_keys)
    hl = "yellow" if is_active else ("#44aa44" if is_visited else None)
    return {
        "key":         v,
        "color":       node.get("color", "#4472C4"),
        "highlight":   hl,
        "dim":         False,
        "visit_order": visit_order_map.get(v) if visit_order_map else None,
        "left":        _clone_bt(node["left"],  visited_keys, active_key, visit_order_map),
        "right":       _clone_bt(node["right"], visited_keys, active_key, visit_order_map),
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


def _btview_obj(id_, root_dict, label="", weight=3):
    return {"id": id_, "type": "bst_tree", "root": root_dict,
            "label": label, "weight": weight}


def btree_traversals(n, **kwargs):
    """Ch.7: 二分木の BFS / DFS 前順・中順・後順 (Sample7_2)"""
    # N を 8〜12 に制限: 8以上で高さ4が保証され、12以下で形のバリエーションが出る
    # （13以上だと高さ4の全15スロットがほぼ埋まり、毎回同じ形に近づくため）
    N   = max(8, min(int(n), 12))
    rng = random.Random(kwargs.get("seed", N))
    vals = rng.sample(range(1, 100), N)
    root = _make_random_btree(vals, rng, max_depth=4)

    traversal = kwargs.get("traversal", "bfs")

    base = [{"message": f"二分木  N={N} (高さ4)", "color": "white"}]

    # ── 初期フレーム (全ノード未訪問) ──
    yield _f([_btview_obj("tree", _clone_bt(root))], base)

    all_traversals = [
        ("bfs",      "BFS (幅優先・レベル順)",          _bfs_order(root)),
        ("preorder", "DFS 前順 (pre-order: 根→左→右)",  _preorder(root)),
        ("inorder",  "DFS 中順 (in-order:  左→根→右)",  _inorder(root)),
        ("postorder","DFS 後順 (post-order: 左→右→根)", _postorder(root)),
    ]
    traversals = [(tname, order) for key, tname, order in all_traversals
                  if traversal in ("all", key)]
    if not traversals:
        traversals = [(all_traversals[0][1], all_traversals[0][2])]

    for tname, order in traversals:
        visited = set()
        # タイトルフレーム
        yield _f([_btview_obj("tree", _clone_bt(root))],
                 base + [{"message": f"── {tname} ──", "color": "cyan"}])

        for step, key in enumerate(order):
            visited.add(key)
            # 訪問済みノードに順番号を付与（現在のノードは step+1 番）
            vom = {k: i + 1 for i, k in enumerate(order[:step + 1])}
            tree_snap = _clone_bt(root, visited_keys=visited - {key}, active_key=key,
                                  visit_order_map=vom)
            seq_str = " → ".join(str(k) for k in order[:step + 1])
            yield _f(
                [_btview_obj("tree", tree_snap)],
                base + [
                    {"message": f"── {tname} ──", "color": "cyan"},
                    {"message": f"訪問: {key}  (#{step + 1})", "color": "yellow"},
                    {"message": f"順序: {seq_str}", "color": "lightgreen"},
                ],
            )

        # 完了フレーム（全ノード緑・全番号表示）
        vom_all = {k: i + 1 for i, k in enumerate(order)}
        seq_str = " → ".join(str(k) for k in order)
        yield _f(
            [_btview_obj("tree", _clone_bt(root, visited_keys=set(order),
                                           visit_order_map=vom_all))],
            base + [
                {"message": f"── {tname} 完了 ──", "color": "cyan"},
                {"message": f"順序: {seq_str}", "color": "#44aa44"},
            ],
        )

    fin_msg = "全走査完了" if len(traversals) > 1 else f"{traversals[0][0]} 完了"
    # 最後の走査の訪問順マップを使って全ノードに番号を残す
    last_order = traversals[-1][1]
    vom_fin = {k: i + 1 for i, k in enumerate(last_order)}
    yield _f(
        [_btview_obj("tree", _clone_bt(root, visited_keys=set(last_order),
                                       visit_order_map=vom_fin))],
        base + [{"message": fin_msg, "color": "#44aa44"}],
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
    """Ch.7: 演算木の構築 (RPN → スタック → 二分木) (Sample7_3)
    スタックアルゴリズムをそのままシミュレートし、ノードを逐次生成して木を組み上げる。
    init_data: A型式(RPN)トークン列（例: 2 3 + 8 1 - *）
    """
    OPERATORS = set("+-*/")

    # ── init_data からユーザー指定の RPN を読み込む ────────────────────
    init_data = kwargs.get("init_data")
    user_tokens = None
    if init_data:
        raw = [str(x).strip() for x in init_data if str(x).strip()]
        # バリデーション: 各トークンは整数 or 演算子のみ
        valid = True
        for t in raw:
            if t not in OPERATORS:
                try:
                    int(t)
                except ValueError:
                    valid = False; break
        # スタックシミュレーションで RPN として正しいか確認
        if valid and raw:
            d = 0
            for t in raw:
                d = d - 1 if t in OPERATORS else d + 1
                if d <= 0:
                    valid = False; break
            if d != 1:
                valid = False
        if valid and raw:
            user_tokens = raw

    if user_tokens:
        tokens   = user_tokens
        expr_str = " ".join(tokens)   # 表示用はそのまま RPN を表示
    else:
        # データサイズ n に応じてプリセットを選ぶ
        PRESETS = [
            (["2", "3", "+"],
             "2 + 3"),                                                          # level 0
            (["4", "2", "-", "3", "*"],
             "(4-2) × 3"),                                                      # level 1
            (["2", "3", "+", "8", "1", "-", "*"],
             "(2+3) × (8-1)"),                                                  # level 2
            (["5", "1", "-", "4", "2", "+", "*", "3", "/"],
             "((5-1) × (4+2)) ÷ 3"),                                           # level 3
            (["3", "2", "+", "8", "1", "-", "*", "4", "3", "*", "-"],
             "(3+2) × (8-1) - 4×3"),                                           # level 4
            (["5", "3", "+", "7", "2", "-", "*", "4", "1", "+", "2", "*", "-"],
             "(5+3) × (7-2) - (4+1) × 2"),                                    # level 5
        ]
        level = max(0, min((int(n) - 8) // 4, len(PRESETS) - 1))
        tokens, expr_str = PRESETS[level]

    base = [
        {"message": f"演算木の構築: {expr_str}", "color": "white"},
        {"message": f"逆ポーランド記法 (RPN): {' '.join(tokens)}", "color": "cyan"},
    ]

    # ── ノード生成ヘルパー ─────────────────────────────────────────────
    def _clr(nd):
        """ノード辞書のハイライトを再帰的にクリア（子を新規コピー）"""
        if nd is None:
            return None
        return {**nd, "highlight": None,
                "left":  _clr(nd.get("left")),
                "right": _clr(nd.get("right"))}

    def _tree_str(nd):
        """デバッグ用: 木を文字列化"""
        if nd is None:
            return ""
        if nd["left"] is None and nd["right"] is None:
            return nd["key"]
        return f"({_tree_str(nd['left'])}{nd['key']}{_tree_str(nd['right'])})"

    def new_leaf(key):
        return {"key": key, "color": "#4472C4",
                "highlight": None, "dim": False, "left": None, "right": None}

    def new_internal(key, left, right):
        """演算子ノードを作成。子サブツリーのハイライトはクリアする"""
        return {"key": key, "color": "#c05020",
                "highlight": None, "dim": False,
                "left": _clr(left), "right": _clr(right)}

    # スタックの最大深さを事前計算（RPN の性質から）
    _max_stk = 0
    _d = 0
    for _t in tokens:
        _d = _d - 1 if _t in OPERATORS else _d + 1
        _max_stk = max(_max_stk, _d)

    # ── フレーム生成 ───────────────────────────────────────────────────
    # スロットごとの色（bottom=0 から順に割り当て）
    SLOT_COLORS = ["#4488cc", "#44aa55", "#cc8833", "#aa44cc"]

    def _clear_hl(nd):
        """ノードのハイライトを再帰的にクリア"""
        if nd is None:
            return None
        return {**nd, "highlight": None,
                "left":  _clear_hl(nd.get("left")),
                "right": _clear_hl(nd.get("right"))}

    def make_frame(stack, token_idx=None, top_hl=None,
                   msg="", color="lightgreen", finished=False):
        # トークンテープ（処理中のトークンをハイライト）
        tok_hl = {token_idx: "yellow"} if token_idx is not None else {}
        tok_cells = _c("tokens", tokens, label="RPN トークン", hl=tok_hl, weight=0.4)

        # スタックアイテムリスト（index 0 = bottom, top = last）
        # 各アイテム: {tree: <ノード辞書>, color: <色>}
        stack_items = []
        for i, nd in enumerate(stack):
            is_top     = (i == len(stack) - 1)
            item_color = (top_hl if (is_top and top_hl)
                          else SLOT_COLORS[i % len(SLOT_COLORS)])
            # ルートのみハイライト、子はクリア済みのはずだが念のため
            if is_top and top_hl:
                item_tree = {**_clear_hl(nd), "highlight": top_hl}
            else:
                item_tree = _clear_hl(nd)
            stack_items.append({"tree": item_tree, "color": item_color})

        stack_view = {
            "type": "expr_stack_view",
            "id":   "stack_view",
            "label": "演算スタック (↑ top)",
            "max_size": _max_stk,
            "stack": stack_items,
            "weight": 3.0,
        }

        return _f([tok_cells, stack_view],
                  base + [{"message": msg, "color": color}],
                  finished=finished, text_position="bottom")

    # ── 初期フレーム ─────────────────────────────────────────────────
    yield make_frame([], msg="スタック初期化  RPN を左から順に処理", color="cyan")

    # ── メインループ: RPN を順に処理してスタックで木を組み上げる ──────
    stack = []
    for i, tok in enumerate(tokens):
        if tok in OPERATORS:
            right = stack[-1]
            left  = stack[-2]

            # ① pop 直後のフレーム: 結合対象の2ノードをスタック先頭に示す
            yield make_frame(stack, token_idx=i, top_hl="orange",
                             msg=f"'{tok}': left='{left['key']}' と right='{right['key']}' を pop",
                             color="orange")
            stack.pop()
            stack.pop()

            # ② 新ノードを作成して push: 部分木が結合される瞬間
            new_nd = new_internal(tok, left, right)
            stack.append(new_nd)
            yield make_frame(stack, token_idx=i, top_hl="yellow",
                             msg=f"'{tok}' ノード作成 → push"
                                 f"  (左='{left['key']}', 右='{right['key']}')",
                             color="cyan")
        else:
            # オペランド: 葉ノードを作成して push
            stack.append(new_leaf(tok))
            yield make_frame(stack, token_idx=i, top_hl="yellow",
                             msg=f"'{tok}': 葉ノード作成 → push",
                             color="lightgreen")

    # ── 完了フレーム: スタックに演算木が1つ残る ────────────────────
    yield make_frame(stack, top_hl="#44aa44",
                     msg=f"演算木 完成!  {expr_str}",
                     color="#44aa44", finished=True)


# ===========================================================================
# アルゴリズム一覧 / データサイズ一覧
# ===========================================================================

# ===========================================================================
# Ch.6: Sample6_1 — ソート+二分探索 vs 逐次探索 (type: "misc")
# ===========================================================================

def _a(id, values, label="", hl=None, target=None, weight=1):
    return {"id": id, "type": "array1d", "values": list(values), "label": label,
            "highlights": {str(k): v for k, v in (hl or {}).items()},
            "fills": [], "pointer": None, "watchman_index": None,
            "target": target, "log_scale": False, "weight": weight}


def _qs_gen(arr):
    """クイックソート（Hoare ライク二方向走査）— arr をインプレース整列しながらフレームを yield"""
    stack = [(0, len(arr) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        pivot = arr[hi]
        i, j = lo, hi - 1
        while True:
            while i < hi and arr[i] < pivot:
                yield list(arr), {i: "yellow", hi: "#ff8844"}
                i += 1
            while j >= lo and arr[j] > pivot:
                yield list(arr), {j: "yellow", hi: "#ff8844"}
                j -= 1
            if i >= j:
                break
            arr[i], arr[j] = arr[j], arr[i]
            yield list(arr), {i: "#88ff88", j: "#88ff88", hi: "#ff8844"}
            i += 1
            j -= 1
        arr[i], arr[hi] = arr[hi], arr[i]
        p = i
        yield list(arr), {p: "#44aa44"}
        if lo < p - 1:   stack.append((lo, p - 1))
        if p + 1 < hi:   stack.append((p + 1, hi))


def _shell_gen(arr):
    """シェルソート — arr をインプレース整列しながらフレームを yield"""
    n, gap = len(arr), len(arr) // 2
    while gap > 0:
        for i in range(gap, n):
            temp, j = arr[i], i
            while j >= gap and arr[j - gap] > temp:
                yield list(arr), {j: "yellow", j - gap: "#ff8844"}
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
            if j != i:
                yield list(arr), {j: "#88ff88"}
        gap //= 2


def _insert_gen(arr):
    """挿入ソート — arr をインプレース整列しながらフレームを yield"""
    for i in range(1, len(arr)):
        key, j = arr[i], i - 1
        yield list(arr), {i: "yellow"}
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            yield list(arr), {j + 1: "#ff8844", j: "yellow"}
            j -= 1
        arr[j + 1] = key
        if j + 1 != i:
            yield list(arr), {j + 1: "#88ff88"}


def _bin_search_gen(sorted_arr, target):
    """二分探索 — (hl_dict, found_idx_or_None) を yield"""
    lo, hi = 0, len(sorted_arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        hl = {i: "#1a3a6a" for i in range(lo, hi + 1)}
        hl[mid] = "yellow"
        yield hl, None
        if sorted_arr[mid] == target:
            yield {mid: "#44aa44"}, mid
            return
        elif sorted_arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    yield {}, -1


def _seq_search_gen(arr, target):
    """逐次探索 — (hl_dict, found_idx_or_None) を yield"""
    for i in range(len(arr)):
        yield {i: "yellow"}, None
        if arr[i] == target:
            yield {i: "#44aa44"}, i
            return
    yield {}, -1


def sample6_1_binary(n, **kwargs):
    """Sample6_1: ソートしてから二分探索 × num_searches 回"""
    import random as _rnd
    N = max(4, int(n))
    init_d = kwargs.get("init_data") or []
    try:
        num_searches = max(1, int(init_d[0]))
    except (IndexError, ValueError, TypeError):
        num_searches = 100
    sort_method = (kwargs.get("sort_method") or "quick").lower()

    rng_data   = _rnd.Random(N * 7919)
    rng_target = _rnd.Random(N * 7919 + 1)
    data = rng_data.sample(range(1, N * 10 + 1), N)
    arr  = list(data)

    SORT_GEN  = {"quick": _qs_gen, "shell": _shell_gen, "insert": _insert_gen}
    SORT_NAME = {"quick": "クイックソート", "shell": "シェルソート", "insert": "挿入ソート"}
    sort_name = SORT_NAME.get(sort_method, "クイックソート")
    sgen_fn   = SORT_GEN.get(sort_method, _qs_gen)

    base = [{"message": f"Sample6_1  {sort_name} + 二分探索  N={N}  探索{num_searches}回  (Ch.6)",
             "color": "white"}]

    def frame(arr_state, hl=None, tgt=None, msg="", color="lightgreen", finished=False):
        return _f([_a("arr", arr_state, label=f"{sort_name} → 二分探索",
                      hl=hl or {}, target=tgt)],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(arr, msg="初期配列（未整列）")

    for s, hl in sgen_fn(arr):
        yield frame(s, hl=hl, msg=f"{sort_name} 中...")

    yield frame(arr, msg=f"{sort_name} 完了 — 二分探索開始", color="cyan")

    targets = [rng_target.randint(1, N * 10 + 1) for _ in range(num_searches)]
    total_steps, found_count = 0, 0

    for idx, tgt in enumerate(targets):
        steps, result = 0, -1
        for hl, found in _bin_search_gen(arr, tgt):
            steps += 1
            yield frame(arr, hl=hl, tgt=tgt,
                        msg=f"二分探索 {idx+1}/{num_searches}  target={tgt}  step={steps}")
            if found is not None:
                result = found
        total_steps += steps
        if result >= 0:
            found_count += 1

    avg = total_steps / num_searches
    yield frame(arr,
                msg=f"完了  {num_searches}回  平均ステップ: {avg:.1f}  発見: {found_count}回",
                color="cyan", finished=True)


def sample6_1_sequential(n, **kwargs):
    """Sample6_1: 逐次探索 × num_searches 回（未整列のまま）"""
    import random as _rnd
    N = max(4, int(n))
    init_d = kwargs.get("init_data") or []
    try:
        num_searches = max(1, int(init_d[0]))
    except (IndexError, ValueError, TypeError):
        num_searches = 100

    rng_data   = _rnd.Random(N * 7919)
    rng_target = _rnd.Random(N * 7919 + 1)
    data = rng_data.sample(range(1, N * 10 + 1), N)
    arr  = list(data)

    base = [{"message": f"Sample6_1  逐次探索  N={N}  探索{num_searches}回  (Ch.6)",
             "color": "white"}]

    def frame(arr_state, hl=None, tgt=None, msg="", color="lightgreen", finished=False):
        return _f([_a("arr", arr_state, label="逐次探索（未整列）",
                      hl=hl or {}, target=tgt)],
                  base + [{"message": msg, "color": color}], finished=finished)

    yield frame(arr, msg="初期配列（未整列）")

    targets = [rng_target.randint(1, N * 10 + 1) for _ in range(num_searches)]
    total_steps, found_count = 0, 0

    for idx, tgt in enumerate(targets):
        steps, result = 0, -1
        for hl, found in _seq_search_gen(arr, tgt):
            steps += 1
            yield frame(arr, hl=hl, tgt=tgt,
                        msg=f"逐次探索 {idx+1}/{num_searches}  target={tgt}  step={steps}")
            if found is not None:
                result = found
        total_steps += steps
        if result >= 0:
            found_count += 1

    avg = total_steps / num_searches
    yield frame(arr,
                msg=f"完了  {num_searches}回  平均ステップ: {avg:.1f}  発見: {found_count}回",
                color="cyan", finished=True)


# ---------------------------------------------------------------------------
# Ch.12: ゲーム木 / α-β 枝刈り
# ---------------------------------------------------------------------------

def _gt_node(id_, player, children=None, leaf_val=None):
    """ゲーム木ノード辞書を生成する"""
    return {
        "id": id_,
        "player": player,       # "MAX" | "MIN" | "LEAF"
        "value": leaf_val,      # 葉は初期値、内部ノードは None から始まる
        "hl": None,             # None | "active" | "pruned" | "done" | "best"
        "alpha": None,          # α-β 用
        "beta": None,
        "pruned_here": False,
        "children": children or [],
    }


def _gt_deep(node):
    """ゲーム木ノードのディープコピー"""
    n = dict(node)
    n["children"] = [_gt_deep(c) for c in node["children"]]
    return n


def _gt_find(root, id_):
    """IDでノードを検索する"""
    if root["id"] == id_:
        return root
    for child in root["children"]:
        found = _gt_find(child, id_)
        if found:
            return found
    return None


def _gt_frame(root, label="", texts=None, finished=False):
    """ゲーム木フレームを生成する"""
    return _f(
        [{"type": "game_tree", "root": _gt_deep(root), "label": label, "weight": 1}],
        texts or [],
        finished=finished,
    )


# 段数ごとの固定シード（同じ段数では常に同じ木を表示）
_GT_SEEDS = {3: 7919, 4: 7793, 5: 7681, 6: 7559}


def _build_game_tree_general(depth, seed=None):
    """depth 段のゲーム木を構築する (depth=3: 3分岐, それ以外: 2分岐, MAX/MIN 交互)"""
    rng = random.Random(seed if seed is not None else _GT_SEEDS.get(depth, depth * 31337))
    bf = 3 if depth == 3 else 2
    LETTERS = ["A", "B", "C"]

    def make_path_id(path):
        if not path:
            return "root"
        return LETTERS[path[0]] + "".join(str(p) for p in path[1:])

    def make_node(path, cur_depth):
        id_str = make_path_id(path)
        if cur_depth == depth - 1:          # 葉レベル
            return _gt_node(id_str, "LEAF", leaf_val=rng.randint(1, 12))
        player = "MAX" if cur_depth % 2 == 0 else "MIN"
        children = [make_node(path + [i], cur_depth + 1) for i in range(bf)]
        node = _gt_node(id_str, player, children=children)
        node["value"] = None
        return node

    return make_node([], 0)


def minimax_game_tree(n, **kwargs):
    """ミニマックス法のアニメーション (Ch.12) ― 段数 3〜6 を init_data で指定"""
    init_data = kwargs.get("init_data", [])
    try:
        depth = int(init_data[0]) if init_data else 3
        depth = max(3, min(6, depth))
    except (ValueError, IndexError):
        depth = 3

    root = _build_game_tree_general(depth)
    label = f"ミニマックス法 ({depth}段)"

    def msg(text, color="lightgreen"):
        return [{"message": text, "color": color}]

    def frame(text, color="lightgreen", finished=False):
        return _gt_frame(root, label, msg(text, color), finished)

    # ── 再帰評価ジェネレータ ─────────────────────────────────────────────────
    def eval_node(node):
        if not node["children"]:               # 葉ノード
            node["hl"] = "active"
            yield frame(f"葉 {node['id']} = {node['value']}", "yellow")
            node["hl"] = "done"
            return

        node["hl"] = "active"
        yield frame(f"{node['player']} ノード {node['id']} を評価...", "yellow")

        for child in node["children"]:
            yield from eval_node(child)

        vals = [c["value"] for c in node["children"]]
        node["value"] = max(vals) if node["player"] == "MAX" else min(vals)
        node["hl"] = "done"
        yield frame(f"{node['player']}({node['id']}) = {node['value']}", "cyan")

    # ── ベストパスを再帰的にハイライト ──────────────────────────────────────
    def mark_best(node):
        node["hl"] = "best"
        if node["children"]:
            if node["player"] == "MAX":
                best = max(node["children"], key=lambda c: c["value"] or -999)
            else:
                best = min(node["children"], key=lambda c: c["value"] or  999)
            mark_best(best)

    yield frame(f"ゲーム木 ({depth}段): MAX が最大化, MIN が最小化", "white")
    yield from eval_node(root)
    mark_best(root)
    yield frame(f"ミニマックス値 = {root['value']}", "lightgreen", finished=True)


def alpha_beta_pruning(n, **kwargs):
    """α-β 枝刈りのアニメーション (Ch.12) ― 段数 3〜6 を init_data で指定"""
    init_data = kwargs.get("init_data", [])
    try:
        depth = int(init_data[0]) if init_data else 3
        depth = max(3, min(6, depth))
    except (ValueError, IndexError):
        depth = 3

    root = _build_game_tree_general(depth)
    label = f"α-β 枝刈り ({depth}段)"
    INF = 999

    def astr(v):
        return "-∞" if v == -INF else ("+∞" if v == INF else str(v))

    def msg(text, color="lightgreen"):
        return [{"message": text, "color": color}]

    def frame(text, color="lightgreen", finished=False):
        return _gt_frame(root, label, msg(text, color), finished)

    def mark_pruned(node):
        node["hl"] = "pruned"
        node["pruned_here"] = True
        for c in node["children"]:
            mark_pruned(c)

    def mark_best(node):
        node["hl"] = "best"
        if node["children"]:
            active = [c for c in node["children"]
                      if not c.get("pruned_here") and c["value"] is not None]
            if active:
                if node["player"] == "MAX":
                    best = max(active, key=lambda c: c["value"])
                else:
                    best = min(active, key=lambda c: c["value"])
                mark_best(best)

    # ── 再帰 α-β ジェネレータ ──────────────────────────────────────────────
    # alpha, beta は整数（値渡し）。
    # 各レベルが独自の alpha/beta を持ち、子に渡すときは更新済みの値を渡す。
    def alphabeta(node, alpha, beta):
        if not node["children"]:               # 葉ノード
            node["hl"] = "active"
            yield frame(f"葉 {node['id']} = {node['value']}", "yellow")
            node["hl"] = "done"
            return

        node["hl"] = "active"
        is_max = node["player"] == "MAX"
        v = -INF if is_max else INF
        node["alpha"] = alpha
        node["beta"]  = beta
        yield frame(f"{node['player']} ノード {node['id']}: α={astr(alpha)}, β={astr(beta)}", "yellow")

        for i, child in enumerate(node["children"]):
            yield from alphabeta(child, alpha, beta)
            cv = child["value"] if child["value"] is not None else (-INF if is_max else INF)

            if is_max:
                v = max(v, cv)
                if v > alpha:
                    alpha = v
                    node["alpha"] = alpha
            else:
                v = min(v, cv)
                if v < beta:
                    beta = v
                    node["beta"] = beta

            node["value"] = v

            if alpha >= beta:                  # カット発生
                for j in range(i + 1, len(node["children"])):
                    mark_pruned(node["children"][j])
                cut_msg = (
                    f"β カット: α={astr(alpha)} ≥ β={astr(beta)} → 枝刈り!" if is_max else
                    f"α カット: β={astr(beta)} ≤ α={astr(alpha)} → 枝刈り!"
                )
                yield frame(cut_msg, "#ff8844" if is_max else "#ff6644")
                node["hl"] = "done"
                return

            yield frame(f"{node['player']}({node['id']}) 暫定値 = {v}", "cyan")

        node["value"] = v
        node["hl"] = "done"
        yield frame(f"{node['player']}({node['id']}) = {v}  確定", "lightgreen")

    yield frame(f"α-β 枝刈り ({depth}段): α=-∞, β=+∞ で開始", "white")
    yield from alphabeta(root, -INF, INF)
    mark_best(root)
    yield frame(f"α-β 枝刈り完了: 最終値 = {root['value']}", "lightgreen", finished=True)


# ---------------------------------------------------------------------------
# Ch.6: クイックソート (QuickSort / Stack / Queue / OptimalQSS / OptimalQSQ)
# ---------------------------------------------------------------------------
# 参考: C++/QuickSort1.cpp, QuickSortStack.cpp, QuickSortQueue.cpp,
#       OptimalQSS.cpp, OptimalQSQ.cpp
# ---------------------------------------------------------------------------

_QS_PIV  = "#ff4444"   # ピボット (赤)
_QS_DONE = "#44aa44"   # 確定済み (緑)
_QS_I    = "#ffee44"   # i ポインタ (黄)
_QS_J    = "#dd66dd"   # j ポインタ (マゼンタ)


def _qs_bar(values, colors, first=None, last=None, weight=2):
    """縦棒グラフオブジェクトを生成する"""
    hl = {str(i): c for i, c in enumerate(colors) if c is not None}
    fills = ([{"from": first, "to": last, "color": "rgba(100,150,220,0.12)"}]
             if first is not None and last is not None and first <= last else [])
    return {"id": "arr", "type": "array1d", "values": list(values),
            "highlights": hl, "fills": fills, "weight": weight, "label": ""}


def _qs_stk_cell(pairs):
    """スタック表示 (bottom→top, 先頭=右が top)"""
    cells = [f"({f},{l})" for f, l in pairs]
    hl = {len(cells) - 1: _QS_I} if cells else {}
    return _c("stk", cells or [" "], f"スタック ({len(pairs)} 組)", hl=hl, weight=0.8)


def _qs_que_cell(pairs):
    """キュー表示 (front→back, 先頭=左が front)"""
    cells = [f"({f},{l})" for f, l in pairs]
    hl = {0: _QS_I} if cells else {}
    return _c("que", cells or [" "], f"キュー ({len(pairs)} 組)", hl=hl, weight=0.8)


def _qs_partition(data, colors, first, last, ds_obj=None):
    """
    Hoare-like パーティション処理ジェネレータ。
    フレームを yield し、StopIteration.value でピボット最終位置を返す。
    ds_obj: スタック/キュー表示オブジェクト（None = 棒グラフのみ）
    """
    def frm(msg, color="yellow"):
        bar = _qs_bar(data, colors, first, last)
        objs = [bar, ds_obj] if ds_obj is not None else [bar]
        return _f(objs, [{"message": msg, "color": color}])

    pivot = data[last]
    colors[last] = _QS_PIV
    yield frm(f"pivot={pivot}  [{first}..{last}]")

    i = first; j = last - 1
    colors[i] = _QS_I
    if j >= first:
        colors[j] = _QS_J

    while True:
        while i < last and data[i] < pivot:
            colors[i] = None; i += 1
            if i < last: colors[i] = _QS_I
            yield frm(f"→ i={i}  data[{i}]={data[i]}", "#ffee44")
        while j >= first and data[j] > pivot:
            colors[j] = None; j -= 1
            if j > first: colors[j] = _QS_J
            yield frm(f"← j={j}  data[{j}]={data[j]}", "#dd66dd")
        if i >= j:
            break
        data[i], data[j] = data[j], data[i]
        yield frm(f"swap data[{i}]↔data[{j}]", "cyan")
        colors[i] = colors[j] = None
        i += 1; j -= 1

    data[i], data[last] = data[last], data[i]
    colors[last] = None
    colors[i] = _QS_DONE
    for k in range(first, last + 1):
        if colors[k] in (_QS_I, _QS_J):
            colors[k] = None
    yield frm(f"pivot={pivot} → [{i}] 確定 ✓", "lightgreen")

    return i   # StopIteration.value — `yield from` で受け取る


def _qs_init(n, kwargs):
    rng = random.Random(kwargs.get("seed", n))
    return rng.sample(range(1, n + 1), n), [None] * n


# ── 1. 通常クイックソート ────────────────────────────────────────────────────
def quick_sort(n, **kwargs):
    """通常クイックソート (再帰相当・データ構造表示なし)"""
    data, colors = _qs_init(n, kwargs)

    def frm(msg, color="white", finished=False):
        return _f([_qs_bar(data, colors)], [{"message": msg, "color": color}], finished=finished)

    stk = [(0, n - 1)]
    yield frm(f"クイックソート  n={n}  開始")

    while stk:
        first, last = stk.pop()
        if first >= last:
            if first == last:
                colors[first] = _QS_DONE
            continue
        pivot_pos = yield from _qs_partition(data, colors, first, last)
        stk.append((pivot_pos + 1, last))
        stk.append((first, pivot_pos - 1))

    yield frm("ソート完了!", "lightgreen", finished=True)


# ── 2. QuickSortStack ────────────────────────────────────────────────────────
def quick_sort_stack(n, **kwargs):
    """QuickSortStack: スタックを明示的に使うクイックソート"""
    data, colors = _qs_init(n, kwargs)
    stk = [(0, n - 1)]

    def frm(msg, color="white", finished=False):
        return _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                  [{"message": msg, "color": color}], finished=finished)

    yield frm(f"Push (0,{n-1}) → スタック初期化  n={n}")

    while stk:
        first, last = stk.pop()
        yield _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                 [{"message": f"Pop ({first},{last}) → [{first}..{last}] を処理", "color": "yellow"}])

        if first >= last:
            if first == last:
                colors[first] = _QS_DONE
                yield _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                         [{"message": f"data[{first}] 単要素確定", "color": "lightgreen"}])
            continue

        pivot_pos = yield from _qs_partition(data, colors, first, last, _qs_stk_cell(stk))

        # 右範囲を先に Push → 左範囲が top になり次に処理される
        stk.append((pivot_pos + 1, last))
        stk.append((first, pivot_pos - 1))
        yield _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                 [{"message": f"Push ({pivot_pos+1},{last}), ({first},{pivot_pos-1})", "color": "cyan"}])

    yield frm("ソート完了!  スタック空", "lightgreen", finished=True)


# ── 3. QuickSortQueue ────────────────────────────────────────────────────────
def quick_sort_queue(n, **kwargs):
    """QuickSortQueue: キューを明示的に使うクイックソート"""
    from collections import deque
    data, colors = _qs_init(n, kwargs)
    que = deque([(0, n - 1)])

    def que_list():
        return list(que)

    def frm(msg, color="white", finished=False):
        return _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                  [{"message": msg, "color": color}], finished=finished)

    yield frm(f"Enqueue (0,{n-1}) → キュー初期化  n={n}")

    while que:
        first, last = que.popleft()
        yield _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                 [{"message": f"Dequeue ({first},{last}) → [{first}..{last}] を処理", "color": "yellow"}])

        if first >= last:
            if first == last:
                colors[first] = _QS_DONE
                yield _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                         [{"message": f"data[{first}] 単要素確定", "color": "lightgreen"}])
            continue

        pivot_pos = yield from _qs_partition(data, colors, first, last, _qs_que_cell(que_list()))

        # 左範囲 → 右範囲の順に Enqueue (FIFO で左から処理)
        que.append((first, pivot_pos - 1))
        que.append((pivot_pos + 1, last))
        yield _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                 [{"message": f"Enqueue ({first},{pivot_pos-1}), ({pivot_pos+1},{last})", "color": "cyan"}])

    yield frm("ソート完了!  キュー空", "lightgreen", finished=True)


# ── 4. OptimalQSS ────────────────────────────────────────────────────────────
def optimal_qss(n, **kwargs):
    """OptimalQSS: サイズ 1 の部分範囲をスキップするスタック版最適化クイックソート"""
    data, colors = _qs_init(n, kwargs)
    stk = [(0, n - 1)]

    def frm(msg, color="white", finished=False):
        return _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                  [{"message": msg, "color": color}], finished=finished)

    yield frm(f"Push (0,{n-1}) → スタック初期化  [サイズ 1 はスキップ]  n={n}")

    while stk:
        first, last = stk.pop()
        yield _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                 [{"message": f"Pop ({first},{last}) → [{first}..{last}] を処理", "color": "yellow"}])

        if first >= last:   # サイズ 0 or 1 は確定済みのはず
            continue

        pivot_pos = yield from _qs_partition(data, colors, first, last, _qs_stk_cell(stk))

        # サイズ 1 の部分範囲はそのまま確定 (Push しない)
        pushed = []
        if pivot_pos + 1 < last:          # 右部分がサイズ > 1
            stk.append((pivot_pos + 1, last))
            pushed.append(f"({pivot_pos+1},{last})")
        elif pivot_pos + 1 == last:
            colors[last] = _QS_DONE       # 右が 1 要素 → 即確定
        if first < pivot_pos - 1:         # 左部分がサイズ > 1 → top に積む
            stk.append((first, pivot_pos - 1))
            pushed.append(f"({first},{pivot_pos-1})")
        elif first == pivot_pos - 1:
            colors[first] = _QS_DONE      # 左が 1 要素 → 即確定

        msg = (f"Push {', '.join(pushed)}  [1要素はスキップ]" if pushed
               else "サブ範囲なし (すべて確定)")
        yield _f([_qs_bar(data, colors), _qs_stk_cell(stk)],
                 [{"message": msg, "color": "cyan"}])

    yield frm("ソート完了!  スタック空", "lightgreen", finished=True)


# ── 5. OptimalQSQ ────────────────────────────────────────────────────────────
def optimal_qsq(n, **kwargs):
    """OptimalQSQ: サイズ 1 の部分範囲をスキップするキュー版最適化クイックソート"""
    from collections import deque
    data, colors = _qs_init(n, kwargs)
    que = deque([(0, n - 1)])

    def que_list():
        return list(que)

    def frm(msg, color="white", finished=False):
        return _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                  [{"message": msg, "color": color}], finished=finished)

    yield frm(f"Enqueue (0,{n-1}) → キュー初期化  [サイズ 1 はスキップ]  n={n}")

    while que:
        first, last = que.popleft()
        yield _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                 [{"message": f"Dequeue ({first},{last}) → [{first}..{last}] を処理", "color": "yellow"}])

        if first >= last:
            continue

        pivot_pos = yield from _qs_partition(data, colors, first, last, _qs_que_cell(que_list()))

        enqueued = []
        if first < pivot_pos - 1:         # 左部分がサイズ > 1
            que.append((first, pivot_pos - 1))
            enqueued.append(f"({first},{pivot_pos-1})")
        elif first == pivot_pos - 1:
            colors[first] = _QS_DONE
        if pivot_pos + 1 < last:          # 右部分がサイズ > 1
            que.append((pivot_pos + 1, last))
            enqueued.append(f"({pivot_pos+1},{last})")
        elif pivot_pos + 1 == last:
            colors[last] = _QS_DONE

        msg = (f"Enqueue {', '.join(enqueued)}  [1要素はスキップ]" if enqueued
               else "サブ範囲なし (すべて確定)")
        yield _f([_qs_bar(data, colors), _qs_que_cell(que_list())],
                 [{"message": msg, "color": "cyan"}])

    yield frm("ソート完了!  キュー空", "lightgreen", finished=True)




AlgorithmList = [
    # ── Ch.3: vector / イテレータ ──
    ("vector capacity – 2倍拡張  (Ch.3)",    vector_capacity_double,  {"type": "misc"}),
    ("vector capacity – 固定+16拡張  (Ch.3)", vector_capacity_fixed16, {"type": "misc"}),
    ("vector 操作  (Ch.3)",        vector_ops,         {"type": "misc", "init_data": True, "ops": True,
                                                        "ops_hint": "push_back(5)\nerase(2)\ninsert(1, 9)\nfind_erase(5)\nreverse()"}),
    ("イテレータ・3要素合計  (Ch.3)", iterator_sum3,      {"type": "misc", "init_data": True}),
    # ── Ch.4: 連結リスト ──
    ("片方向連結リスト  (Ch.4)",              singly_linked_list,      {"type": "misc", "init_data": True, "ops": True,
                                                                         "ops_hint": "add(5)\naddFirst(9)\ndeleteFirst()\ndeleteNode(5)\nfind(9)"}),
    ("イテレータ・4要素平均  (Ch.4)",         singly_linked_list_avg4, {"type": "misc", "init_data": True}),
    ("双方向連結リスト  (Ch.4)",              doubly_linked_list,      {"type": "misc", "init_data": True, "ops": True,
                                                                         "ops_hint": "add(5)\naddFirst(9)\ndeleteNode(5)\ndisplay()\ndisplayReverse()\nreverse()"}),
    # ── Ch.5: スタック / キュー / RPN ──
    ("連結リストスタック  (Ch.5)",  stack_linked_list,  {"type": "misc", "init_data": True}),
    ("連結リストキュー  (Ch.5)",    queue_linked_list,  {"type": "misc", "init_data": True}),
    ("配列スタック  (Ch.5)",        stack_array,        {"type": "misc", "init_data": True}),
    ("循環キュー  (Ch.5)",          queue_circular,     {"type": "misc", "init_data": True}),
    ("RPN 評価・配列スタック  (Ch.5)",  rpn_eval_array,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: 2 3 + 8 1 - *"}),
    ("RPN 評価・連結リストスタック  (Ch.5)", rpn_eval_list,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: 2 3 + 8 1 - *"}),
    ("B式->RPN 変換・評価  (Ch.5)", rpn_eval,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: (2+3)*(8-1)"}),
    ("B型式 直接計算  (Ch.5)",      rpn_direct_b,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: (2+3)*(8-1)"}),
    # ── Ch.6: ソート+二分探索 / 逐次探索 ──
    ("ソート+二分探索  (Ch.6)", sample6_1_binary,
     {"type": "misc", "sort_method": True,
      "init_data": True, "init_data_type": "expr",
      "init_data_hint": "（例: 100）  省略時=100",
      "init_data_label": "探索回数"}),
    ("逐次探索  (Ch.6)", sample6_1_sequential,
     {"type": "misc",
      "init_data": True, "init_data_type": "expr",
      "init_data_hint": "（例: 100）  省略時=100",
      "init_data_label": "探索回数"}),
    # ── Ch.6: クイックソート (スタック/キュー応用) ──
    ("クイックソート  (Ch.6)",                           quick_sort,       {"type": "misc"}),
    ("クイックソート・スタック版  (Ch.6)",                quick_sort_stack, {"type": "misc"}),
    ("クイックソート・キュー版  (Ch.6)",                  quick_sort_queue, {"type": "misc"}),
    ("最適クイックソート・スタック版 OptimalQSS  (Ch.6)", optimal_qss,      {"type": "misc"}),
    ("最適クイックソート・キュー版 OptimalQSQ  (Ch.6)",   optimal_qsq,      {"type": "misc"}),
    # ── Ch.7: 二分探索木 / 二分木走査 / 演算木 ──
    ("BST 挿入・探索・削除  (Ch.7)", bst_operations,    {"type": "misc", "tree_regen": True}),
    ("二分木の走査 BFS/DFS  (Ch.7)", btree_traversals,  {"type": "misc", "traversal_select": True, "tree_regen": True}),
    ("演算木の構築  (Ch.7)",         expression_tree,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: 2 3 + 8 1 - *"}),
    # ── Ch.8: 赤黒木・B木 ──
    ("赤黒木 挿入  (Ch.8)",         rb_tree_insert,     {"type": "misc"}),
    ("AVL木 挿入・探索・削除  (Ch.8)", avl_tree_operations, {"type": "misc", "tree_regen": True}),
    ("B木 挿入  (Ch.8)",            bt_operations,      {"type": "misc"}),
    # ── Ch.11: グラフ ──
    ("深さ優先探索 DFS  (Ch.11)",    graph_dfs,          {"type": "misc"}),
    ("幅優先探索 BFS  (Ch.11)",      graph_bfs,          {"type": "misc"}),
    # ── Ch.12: ゲーム木 ──
    ("ミニマックス法  (Ch.12)", minimax_game_tree, {"type": "misc", "depth_select": True}),
    ("α-β 枝刈り  (Ch.12)",    alpha_beta_pruning, {"type": "misc", "depth_select": True}),
    # ── Ch.10: ハッシュ表 ──
    ("ハッシュ表 オープンアドレス法  (Ch.10)", hash_open_addressing,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: 13  (空欄=自動)  ハッシュ表サイズ m",
      "hash_func": True}),
    ("ハッシュ表 チェイン法  (Ch.10)", hash_chaining,
     {"type": "misc", "init_data": True, "init_data_type": "expr",
      "init_data_hint": "例: 7  (空欄=自動)  バケツ数 m",
      "hash_func": True}),
]

DataSizeList = [8, 12, 16, 20, 24, 32, 48, 64, 96, 128, 192, 256]
