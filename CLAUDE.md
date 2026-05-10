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
- AVL木回転弧: オブジェクトに `rotation` フィールドを付加することで Canvas 上に回転矢印を描画
  ```python
  _avl_obj_from_dict(id_, root_dict, label="", weight=1,
                     rotation={"type": "LR", "pivot": 10, "child": 5})
  ```
  - `type`: `"LL"` / `"RR"` / `"LR"` / `"RL"`
  - `pivot`: 不均衡ノードのキー（常に必須）
  - `child`: LR/RL のみ必須（先に回転する子ノードのキー）、LL/RR は `null`
  - LL→pivot に右半円弧（実線）/ RR→pivot に左半円弧（実線）
  - LR→child に左半円弧＋pivot に右半円弧（破線）/ RL→child に右半円弧＋pivot に左半円弧（破線）

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
   - **乱数は必ず** `rng = random.Random(kwargs.get("seed", N))` を使うこと（グローバル `random.sample/randint` は使わない）

2. `AlgorithmList` に登録（ファイル末尾）:
   ```python
   ("表示名  (Ch.X)", my_algo, {"type": "misc"}),
   ```
   - `init_data` 対応の場合: `"init_data": True` を meta に追加
   - `ops` 対応の場合: `"ops": True` + `"ops_hint": "op1()\nop2()"` を meta に追加

3. **1操作 = 1 `yield`** を原則とする

---

## init_data / ops の対応状況

### init_data（初期データをユーザーが指定可能）

| アルゴリズム | init_data の意味 | init_data_type |
|---|---|---|
| vector 操作 | 初期ベクター要素 | (整数リスト) |
| イテレータ・3要素合計 | テープの要素列 | (整数リスト) |
| 片方向連結リスト | リスト初期値 | (整数リスト) |
| イテレータ・4要素平均 | テープの要素列 | (整数リスト) |
| 双方向連結リスト | リスト初期値 | (整数リスト) |
| 連結リストスタック | Push する値列 | (整数リスト) |
| 連結リストキュー | Enqueue する値列 | (整数リスト) |
| 配列スタック | Push する値列（最大8件） | (整数リスト) |
| 循環キュー | 最初の Enqueue 値列（最大6件） | (整数リスト) |
| RPN 評価・配列スタック | A型式（例: `2 3 + 8 1 - *`） | `"expr"` |
| RPN 評価・連結リストスタック | A型式（例: `2 3 + 8 1 - *`） | `"expr"` |
| RPN 変換・評価 | B型式・中置（例: `(2+3)*(8-1)`） | `"expr"` |
| B型式 直接計算 | 完全括弧 B型式（例: `(((2)+(3))*((8)-(1)))`） | `"expr"` |

`init_data_type: "expr"` の場合:
- 空白・コンマをトークン区切りとして扱う（式内の余分な空白は自動除去）
- B型式: `(2 + 3) * (8 - 1)` → アルゴリズム側で join → `(2+3)*(8-1)`
- A型式: `2 3 + 8 1 - *` → 7トークンとして処理
- `init_data_hint` に入力例を設定してプレースホルダーとして表示

### ops（操作列をユーザーが指定可能）

| アルゴリズム | 使える操作 |
|---|---|
| vector 操作 | `push_back(x)` / `erase(idx)` / `insert(idx, x)` / `find_erase(x)` / `reverse()` |
| 片方向連結リスト | `add(x)` / `addFirst(x)` / `deleteFirst()` / `deleteNode(x)` / `find(x)` |
| 双方向連結リスト | `add(x)` / `addFirst(x)` / `deleteNode(x)` / `display()` / `displayReverse()` / `reverse()` |

書式: 1行1操作。セミコロン区切りも可。`#` 始まり行はコメント。

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

## 実装済みアルゴリズム（22本）

| チャプター | アルゴリズム |
|---|---|
| Ch.3 | vector capacity (2倍拡張), vector capacity (固定+16拡張), vector 操作, イテレータ・3要素合計 |
| Ch.4 | 片方向連結リスト, イテレータ・4要素平均, 双方向連結リスト |
| Ch.5 | 連結リストスタック, 連結リストキュー, 配列スタック, 循環キュー, RPN 変換・評価 |
| Ch.6 | BST 挿入・探索・削除 |
| Ch.7 | 二分木の走査 BFS/DFS, 演算木の構築 |
| Ch.8 | 赤黒木 挿入, AVL木 挿入・探索・削除, B木 挿入 |
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
