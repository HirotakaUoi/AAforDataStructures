# AAforDataStructures – 開発ガイド

## アーキテクチャ概要

```
[Browser]  ←─ WebSocket ─→  [FastAPI / main.py]  ←─ import ─→  [algorithms.py]
  app.js                       /api/start                          generator関数群
  array_canvas.js              /ws/{session_id}
```

- `algorithms.py` の各関数は **Pythonジェネレータ**（`yield` でフレームを1つずつ出力）
- `main.py` がジェネレータを回しながら WebSocket でフレームをストリーミング
- ブラウザ側の `array_canvas.js` が Canvas にフレームを描画

---

## フレーム形式

```python
{
  "objects":       [...],          # 描画オブジェクトのリスト
  "texts":         [...],          # テキストオーバーレイ
  "finished":      bool,           # アニメーション完了フラグ
  "found":         int | null,     # 探索結果インデックス (search 用)
  "text_position": "top" | "bottom"  # テキスト描画位置（デフォルト "top"）
}
```

テキスト要素:
```python
{"message": "説明文", "color": "white" | "red" | "lightgreen" | "cyan" | ...}
```

---

## オブジェクト種別とヘルパー関数

### `array1d_cells` — 正方形セル配列
```python
_c(id, values, label="", hl=None, fills=None, ptr=None,
   watchman=None, target=None, weight=1, unused_from=None)
```
- `hl`: `{インデックス: "色"}` で個別ハイライト
- `ptr`: `_ptr(index, label, color)` で生成したポインタオブジェクト
- `unused_from`: このインデックス以降のセルをグレーアウト（配列スタックの未使用領域表示用）

### `tape` — 無端テープ（イテレータ走査用）
```python
_tape(id, cells, head, label="", color="#4472C4", weight=1)
```

### `linked_list` — 矢印接続ノード列
```python
_ll(id, nodes, label="", hl=None, is_doubly=False, is_vertical=False,
    ptr_labels=None, ptr_colors=None, weight=1)
```
- `is_doubly=True`: 双方向リスト（`←→` 矢印）
- `ptr_labels`: ノード列の先頭・末尾ポインタラベル（例: `["first", "last"]`）

### `stack_v` — 縦方向配列スタック
```python
_stack_v(id, values, top, max_size, label="", hl=None, weight=1, pad_bottom=0)
```
- `top`: 現在のスタックトップインデックス（-1 = 空）

### `queue_circ` — 循環キュー
```python
_queue_circ(id, values, front, back, count, label="", hl=None, weight=1)
```

### `bst_tree` — 二分探索木 / 赤黒木 / 二分木汎用
```python
_bst_obj(id, node_dict, hl_map=None, label="", weight=1)
```
- ノードdict: `{"key": k, "color": "#4472C4", "left": ..., "right": ...}`
- 赤黒木ノードは `"color"` が `"red"` / `"black"` / `"#2a1a1a"`（nil ノード）

### `btree_view` — B木
```python
_bt_obj(id, root, hl_map=None, t=2, label="", weight=1)
```
- `t`: B木の最小次数（デフォルト 2 = 2-3-4木）

### `graph_view` — グラフ（無向）
```python
# _graph_frame() 内で直接構築
{"id": "graph", "type": "graph_view",
 "nodes": [...], "edges": [...], "label": "Graph", "weight": 1}
```
- node: `{"id": i, "color": "#4472C4", "highlight": None | color, ...}`
- edge: `{"from": u, "to": v, "directed": False, "highlight": bool}`
- ノード座標は `_make_random_graph(N, seed=...)` が **Fruchterman-Reingold** で計算（円形配置ではない）
- `seed` は `/api/preview` と `/api/start` の両方からフロントエンドが渡す → プレビューと実行で同じグラフ、リセットごとに新しいグラフ

### `hash_table` — ハッシュ表
```python
_hash_obj(id, slots, m, label="", active=-1, weight=1)
# slot: _hash_slot(key=None, hl=None, chain=[])
```
- `active`: 現在操作中のスロットインデックス（強調表示）
- `chain`: チェイン法では各スロットの連鎖値リスト

---

## `weight` の使い方

複数オブジェクトを同一フレームに入れるとき、縦スペースを比率で分配する:
```python
[
  _c("data", ..., weight=1),
  _ll("list", ..., weight=2),
]
```

---

## アルゴリズム追加手順

1. `algorithms.py` にジェネレータ関数を実装
   - シグネチャ: `def my_algo(n, **kwargs)`
   - 全アルゴリズムが `"misc"` タイプ（target 入力・data_condition 非表示）
   - 最低 1 フレーム yield すること（`finished=True` のフレームで終了）

2. `AlgorithmList` に登録（ファイル末尾）:
   ```python
   ("表示名  (Ch.X)", my_algo, {"type": "misc"}),
   ```

3. **1操作 = 1 `yield`** を原則とする

---

## ハイライト配色の慣例

| 状況 | 色 |
|---|---|
| 注目中 / 操作対象 | `"yellow"` |
| 挿入・確定済み | `"#44aa44"` |
| 削除・ポップ | `"#ff4444"` / `"orange"` |
| 探索経路 / 比較中 | `"#ffcc44"` |
| キュー待機中 | `"#ff8844"` |

---

## 開発サーバー

```bash
cd AAforDataStructures && python -m uvicorn main:app --port 8006
```

- ポート: **8006**

---

## 実装済みアルゴリズム（21本）

| チャプター | アルゴリズム |
|---|---|
| Ch.3 | vector capacity (2倍拡張), vector capacity (固定+16拡張), vector 操作, イテレータ・3要素合計 |
| Ch.4 | 片方向連結リスト, イテレータ・4要素平均, 双方向連結リスト |
| Ch.5 | 連結リストスタック, 連結リストキュー, 配列スタック, 循環キュー, RPN 変換・評価 |
| Ch.6 | BST 挿入・探索・削除 |
| Ch.7 | 二分木の走査 BFS/DFS, 演算木の構築 |
| Ch.8 | 赤黒木 挿入, B木 挿入 |
| Ch.10 | ハッシュ表 開番地法, ハッシュ表 チェイン法 |
| Ch.11 | 深さ優先探索 DFS, 幅優先探索 BFS |

---

## ファイル構成

```
AAforDataStructures/
├── main.py              FastAPI + WebSocket サーバー
├── algorithms.py        全アルゴリズム（ジェネレータ）+ AlgorithmList
├── requirements.txt
└── static/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── app.js           パネル管理・メインアプリ
        ├── array_canvas.js  Canvas 描画エンジン
        └── ws_client.js     WebSocket クライアント
```
