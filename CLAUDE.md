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
| ハッシュ表 開番地法 | `m`（例: `13`）キー型・ハッシュ関数は別行 UI で選択 | `"expr"` |
| ハッシュ表 チェイン法 | `m`（例: `7`）キー型・ハッシュ関数は別行 UI で選択 | `"expr"` |
| RPN 評価・配列スタック | A型式（例: `2 3 + 8 1 - *`） | `"expr"` |
| RPN 評価・連結リストスタック | A型式（例: `2 3 + 8 1 - *`） | `"expr"` |
| RPN 変換・評価 | B型式・中置（例: `(2+3)*(8-1)`） | `"expr"` |
| B型式 直接計算 | 完全括弧 B型式（例: `(((2)+(3))*((8)-(1)))`） | `"expr"` |

**ハッシュ表のキー型・ハッシュ関数 UI**（`hash_func: True` のアルゴリズムのみ）:
- `key-type-row`: 整数 / 文字列 / 実数 をドロップダウンで切替
- `hash-func-row`: キー型に応じたハッシュ関数ドロップダウン
  - 整数: 除算法 / 乗算法 / 二乗法 / カスタム
  - 文字列: 加算折り畳み法 / 多項式ハッシュ(Horner) / 乗算折り畳み / カスタム
  - 実数: 乗算法 / 切り捨て / スケール(×100) / カスタム
- カスタム式変数: 整数→ `k, m`　文字列→ `k, m, ord, sum, len`　実数→ `k, m, int, round, abs`
- init_data トークン: `[m] [key_type] [func]`（例: `13 str poly` / `7 float scale`）

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
| Ch.7 | BST 挿入・探索・削除, 二分木の走査 BFS/DFS, 演算木の構築 |
| Ch.8 | 赤黒木 挿入, AVL木 挿入・探索・削除, B木 挿入 |
| Ch.10 | ハッシュ表 開番地法, ハッシュ表 チェイン法 |
| Ch.11 | 深さ優先探索 DFS, 幅優先探索 BFS（目的ノード指定で経路探索も可） |

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

---

## 現在のファイルバージョン

| ファイル | バージョン |
|---|---|
| `static/js/app.js` | **v45** |
| `static/js/array_canvas.js` | **v54** |
| `static/js/ws_client.js` | **v2** |
| `static/css/style.css` | **v9** |

---

## 最近の変更履歴

| 日付 | 内容 |
|---|---|
| 2026-07-17 | WebSocket keep-alive を追加 — 接続中は45秒間隔で `{"action":"ping"}` を送信し、Render 無料枠の「インバウンド通信15分無しでスピンダウン」による切断を防止（一時停止中も有効）。明示的な停止・完了・切断が無くても最大1時間で送信を打ち切る。サーバー側は未知 action を無視する既存実装のまま変更なし (ws_client.js v1→v2) |
| 2026-07-03 (3) | 全アルゴリズム共通: 完了時の全画面dimが探索結果(Found!/Not Found)・計算結果(result)バナーにまだ残っていたのを修正（生データ構造が隠れて確認できない問題）。キャンバス上には一切描かず、ステータスバーの `status-done-badge` に「✅ Found !」「❌ Not Found」「✅ 結果 = …」「🎉 完了!」を固定背景色バッジ（テーマが変わっても視認性が落ちない）で表示するよう統一。表示時に短いフラッシュアニメーション(1.4秒)を付与し「一時的に目立たせてからステータス表示に落ち着く」動きに。副次的に、テーマ切替時に実行中でないパネル（完了後含む）が最終フレームでなくプレビューに巻き戻るバグも発見・修正（`_applyTheme` の再描画条件から `isRunning` 判定を除去） (array_canvas.js v53→v54, app.js v44→v45, style.css v8→v9) |
| 2026-07-03 (2) | DFS/BFS: 「目的ノードを入力→開始」のように `.inp-target` が blur した際の change イベントで意図せずグラフが再抽選され、プレビューと実際に開始されるアニメーションが食い違うバグを修正。`tree_regen` と同様のシード固定ロジックを `target_node` 対応アルゴリズムにも適用 (app.js v43→v44) |
| 2026-07-03 (1) | DFS/BFS: グラフのランダム生成を連結成分ごとにレイアウト計算しグリッド状に敷き詰める方式に変更 — 非連結グラフで成分間に反発力だけが働き不必要な空白ができていた問題を修正（`_fr_layout()` ヘルパーに切り出し） |
| 2026-07-02 (8) | DFS/BFS 目的ノード欄: `<input type=number>` の上下スピナーを非表示化（直接入力のみ）。`_validateTargetNode()` を追加し、範囲外・非整数入力時はリアルタイムで赤字エラー表示、「開始」もブロックするよう変更 (app.js v42→v43, style.css v7→v8) |
| 2026-07-02 (7) | DFS/BFS: 目的ノード番号を指定して経路探索するモードを追加（`target` パラメータ、`target_node` メタフラグ）。発見時は経路をノード/辺とも緑色でハイライトし停止（BFSは自動的に最短経路）。未指定時は従来通りの全探索モードを維持。既存の `.inp-target` UI を流用し「目的ノード」ラベルに切替 (app.js v41→v42, array_canvas.js v52→v53) |
| 2026-07-02 (6) | DFS/BFS: `_make_random_graph` が一定確率(35%)で非連結グラフも生成するよう変更。完了メッセージに未到達ノードを明示。ノード重なりをグラフ描画時の実座標ベースの半径計算で解消 (array_canvas.js v51→v52) |
| 2026-07-02 (5) | ハッシュ表 開番地法: テーブル満杯時に挿入をスキップして続行していたのをやめ、空きスロットが見つからない時点でメッセージ表示して `finished=True` で即停止するよう変更（以降の挿入も全て失敗するため） |
| 2026-07-02 (4) | ハッシュ表 2本: 描画レイアウトを中央寄せ→左詰めに変更 — パネルを広げると中央寄せ計算により左側の余白が際限なく広がっていたバグを修正 (array_canvas.js v50→v51) |
| 2026-07-02 (3) | ハッシュ表 2本: 挿入データ数の上限を24→40に引き上げ、データ数メニューに追従するよう修正。開番地法は m をユーザー指定した場合に強制的に拡張する安全策を撤廃し、テーブルが満杯になり得る状態を許容 — 満杯時に既存要素を無条件上書きしていた潜在バグも合わせて修正 |
| 2026-07-02 (2) | 全アルゴリズム共通: 完了時の全画面dim+「完了!」オーバーレイを廃止（データ構造が見えなくなる問題）。探索結果(Found!/Not Found)・計算結果は維持しつつ、汎用の完了通知はコントロールパネルのステータスバー右側に「🎉 完了!」バッジとして表示するよう変更 (array_canvas.js v49→v50, app.js v40→v41, style.css v6→v7) |
| 2026-07-02 (1) | ハッシュ表 2本: `_drawHashTable` の上部パディングがテキストオーバーレイ(3行, 約66px)より小さく、テーブル先頭行が隠れていたのを修正 (array_canvas.js v48→v49) |
| 2026-07-02 | AVL木: 「回転で自動停止」の停止タイミングずれバグ修正 — サーバー送信ループがフレーム送信**前**に一時停止をチェックする構造だったため、クライアントの pause 往復待ちの間に次フレームが先に送られるレースコンディションがあった。`rotation_pause` を `/api/start` パラメータとしてサーバーに渡し、回転フレーム送信**直後**にサーバー自身が一時停止するよう変更 (main.py, app.js v39→v40) |
| 2026-06-21 | AVL木: 「回転で自動停止」機能追加 — 回転フレーム (objects に `rotation` を持つ) で自動的に一時停止。ON/OFF チェックボックスを「🌳 初期木生成」ボタンの右側に配置。meta フラグ `rotation_pause: True` + `_algoSupportsRotationPause()` ヘルパー、`_onFrame` に検出ロジック追加 (app.js v38→v39)。BST/赤黒木/B木: 挿入回数をデータ数 n に追従 (algorithms.py) |
| 2026-06-12 | BST/AVL: 初期木（高さ3, N=4〜6）を最初から表示し、挿入値3個は別途ランダム生成して挿入アニメーション。「🌳 初期木生成」ボタン（旧 二分木生成）を速度設定の隣に移動、`tree_regen` メタフラグで BST/AVL/走査の3本に適用 — リセットでは同じ木を維持、ボタンでのみ再生成 (app.js v36→v38) |
| 2026-06-12 | 二分木の走査: ランダム形状の二分木生成 (`_make_random_btree`, 高さ4固定・N=8〜12) + 「🌳 二分木生成」ボタンを走査セレクト隣に追加 — リセット・走査種別変更では同じ木を維持し、ボタン押下時のみシード再生成 (app.js v35→v36) |
| 2026-05-26 | RPN 変換・評価: 変換後 A型式(RPN)を B型式の下に配置 / Opr→"Opr"・演算子スタック→"Oprs" ラベル付き 2×2 グリッド表示 (array_canvas.js v43→v44, col 型対応追加) |
| 2026-05-26 | RPN/B式パネルの初期状態入力欄を広げる: CSS class方式を廃止し、JS inline style直接設定方式に変更 (app.js v31→v32, style.css v5→v6) |
| 2026-05-26 | RPN 変換・評価: 演算子スタック→stack_v表示 / 評価フェーズをrow+stack_v+エラー処理+result表示に変更 |
| 2026-05-26 | RPN 評価・配列スタック: レイアウトを連結リスト版に合わせて左スタック・右式に変更 + 両RPN関数にエラー判定追加（空pop・最終要素数チェック） |
| 2026-05-26 | RPN 評価・連結リストスタック: スタック表示を横→縦(底が下)に変更、入力文字列の左に配置 (array_canvas.js v41→v42) |
| 2026-05-15 | クイックソート分割を Hoare ライク二方向走査に変更 / データ数上限64→撤廃 / 探索回数ラベル・UI整理 (app.js v29→v30) |
| 2026-05-15 | 全パネルへ適用ボタン追加 (app.js v28→v29) — ツールバーに global-size セレクト + ↕ 全パネルへ適用ボタン、misc 型は共通シードでプレビュー同期 |
| 2026-05-15 | Sample6_1: ソート+二分探索 / 逐次探索 アニメーション追加 (algorithms.py) — ソート手法選択 UI (app.js v27→v28) |
| 2026-05-13 | ハッシュ表: 文字列・実数キー対応 (app.js v26→v27) — キー型選択 UI + sum/poly/trunc/scale ハッシュ関数追加 |
| 2026-05-13 | ハッシュ表 2本: ハッシュ関数選択 UI 追加 (app.js v25→v26) — 除算法/乗算法/二乗法/カスタム式ドロップダウン |
| 2026-05-11 | drag/resize を Pointer Events API に統一 — `setPointerCapture` で軸ロック完全解消 (app.js v24→v25) |
| 2026-05-10 | タッチドラッグ軸ロックバグ修正 — `onMove` 内に `preventDefault()` 追加 / スナップをリリース時のみ適用 (app.js v22→v24) |
| 2026-05-10 | RPN 式入力バグ修正 — `.inp-algo`→`.sel-algo`、A型式トークン分割修正 (app.js v20→v22) |
| 2026-05-10 | RPN 4本に `init_data` 式入力対応 (`init_data_type: "expr"`) |
| 2026-05-10 | タッチデバイス対応 — `resize-handle` 追加、`touch-action: none`、touch イベントリスナー追加 |
| 2026-05-07 | ops プレースホルダー改善（アルゴリズム固有ヒント） |
| 2026-05-06 | Ch.5 スタック・キュー4本に `init_data` 対応 / シード不一致バグ修正 |
| 2026-05-05 | ops 操作列 UI 追加（vector_ops / singly / doubly） |
| 2026-05-05 | lineWidth 強化（アニメーション指針対応）/ iterator_sum3 count 可視化 / BST 関数名衝突バグ修正 |
| 2026-05-04 | AVL木 挿入・探索・削除 追加 (Ch.8) + 回転矢印アニメーション |
| 2026-05-03 | カラーテーマ全面対応 (dark/bright/hc/hcbright) |
