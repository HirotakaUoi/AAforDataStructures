# AAforDataStructures

教科書サンプルコード（C#）のデータ構造アルゴリズムをブラウザ上でステップごとにアニメーション表示する可視化ツールです。

**デモ:** https://aafordatastructures.onrender.com

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 概要

FastAPI + WebSocket によるサーバーサイドのフレーム生成と、Canvas 2D API による描画を組み合わせ、データ構造の操作をリアルタイムにアニメーション表示します。

- 各操作を **1操作 = 1フレーム** で可視化（挿入・削除・探索などをステップ追跡）
- 複数パネルを同時に開いてアルゴリズムを並べて比較可能
- 4種類のカラーテーマ（ダーク / 明るめ / コントラスト強め 暗 / 明）
- 速度調整・一時停止・ステップ再生に対応

---

## 対応アルゴリズム（22種）

### Ch.3 — vector / イテレータ

| アルゴリズム | 説明 |
|---|---|
| vector capacity – 2倍拡張 | `push_back` による capacity の倍増を可視化 |
| vector capacity – 固定+16拡張 | `push_back` による capacity の +16 拡張を可視化 |
| vector 操作 | `push_back` / `erase` / `insert` / `find_erase` / `reverse` の操作列（カスタム可） |
| イテレータ・3要素合計 | テープ表示でイテレータが 3 要素ずつ走査し合計を計算（端数グループ対応） |

### Ch.4 — 連結リスト

| アルゴリズム | 説明 |
|---|---|
| 片方向連結リスト | `add` / `addFirst` / `deleteFirst` / `deleteNode` / `find`（操作列カスタム可） |
| イテレータ・4要素平均 | 連結リストを 4 要素ずつ走査して平均を計算（端数グループ対応） |
| 双方向連結リスト | `add` / `addFirst` / `deleteNode` / `display` / `displayReverse` / `reverse`（操作列カスタム可） |

### Ch.5 — スタック / キュー / RPN

| アルゴリズム | 説明 |
|---|---|
| 連結リストスタック | 片方向連結リストによる Push / Pop |
| 連結リストキュー | 片方向連結リストによる Enqueue / Dequeue |
| 配列スタック | 配列による Push / Pop（top ポインタ付き） |
| 循環キュー | 配列による循環キュー（front / back、ラップアラウンド可視化） |
| RPN 変換・評価 | 中置式 → 逆ポーランド記法変換 + スタック評価 |

### Ch.6 — 二分探索木（BST）

| アルゴリズム | 説明 |
|---|---|
| BST 挿入・探索・削除 | 挿入パスを黄色でたどり、削除は後継ノード交換まで可視化 |

### Ch.7 — 二分木の走査 / 演算木

| アルゴリズム | 説明 |
|---|---|
| 二分木の走査 BFS / DFS | 幅優先・前順・中順・後順の4種を比較表示 |
| 演算木の構築 | 算術式から演算木を構築し、再帰的に評価 |

### Ch.8 — 平衡木

| アルゴリズム | 説明 |
|---|---|
| 赤黒木 挿入 | 挿入後の色変換・回転を赤/黒ノードで可視化 |
| AVL木 挿入・探索・削除 | LL / RR / LR / RL 回転を半円弧アニメーションで可視化 |
| B木 挿入 | ノード分割を伴う挿入を可視化 |

### Ch.10 — ハッシュ表

| アルゴリズム | 説明 |
|---|---|
| ハッシュ表 開番地法 | 線形探索法によるオープンアドレッシング |
| ハッシュ表 チェイン法 | 各スロットに連鎖リストを持つチェイニング |

### Ch.11 — グラフ探索

| アルゴリズム | 説明 |
|---|---|
| 深さ優先探索 DFS | スタックを用いた DFS（訪問順・バックトラックを可視化） |
| 幅優先探索 BFS | キューを用いた BFS（訪問順・距離を可視化） |

---

## 動作環境

- Python 3.11 以上
- モダンブラウザ（Chrome / Firefox / Safari / Edge）

---

## セットアップ

```bash
git clone https://github.com/HirotakaUoi/AAforDataStructures.git
cd AAforDataStructures
pip install -r requirements.txt
python -m uvicorn main:app --port 8006
```

ブラウザで http://localhost:8006 を開いてください。

---

## 使い方

1. **＋ パネル追加** でアニメーションパネルを追加
2. パネルごとにアルゴリズム・データ数・速度を設定
3. 対応アルゴリズムでは **初期データ** や **操作列** をカスタム入力可能
4. **▶ 開始** でアニメーション再生
5. **⏸ 一時停止** / **■ 停止** / **↺ リセット** で制御
6. パネルはドラッグで移動、右下コーナーでリサイズ可能

---

## ファイル構成

```
AAforDataStructures/
├── main.py              # FastAPI サーバー・WebSocket エンドポイント
├── algorithms.py        # 全アルゴリズムのジェネレータ関数 + AlgorithmList
├── requirements.txt
└── static/
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        ├── array_canvas.js  # Canvas 描画エンジン
        ├── ws_client.js     # WebSocket クライアント
        └── app.js           # パネル管理・メインアプリ
```

---

## 技術構成

| 要素 | 技術 |
|---|---|
| バックエンド | Python / FastAPI / WebSocket |
| フロントエンド | Vanilla JS / Canvas 2D API |
| アニメーション生成 | Python ジェネレータ（`yield` でフレーム単位に送信） |
| 通信 | WebSocket（フレームごとに JSON をストリーミング） |

---

## ライセンス

MIT
