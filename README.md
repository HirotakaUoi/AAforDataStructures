# AAforDataStructures

教科書サンプルコード（C#）のデータ構造アルゴリズムをブラウザ上でステップごとにアニメーション表示する可視化ツールです。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## 概要

FastAPI + WebSocket によるサーバーサイドのフレーム生成と、Canvas 2D API による描画を組み合わせ、データ構造の操作をリアルタイムにアニメーション表示します。

- 各操作（Push / Pop / Enqueue / Dequeue / insert / erase など）をフレーム単位で可視化
- **連結リスト**は矢印付きノード列で表示（片方向 `→` / 双方向 `←→`、`first`・`last` ポインタ自動描画）
- **テープ**表示でイテレータの走査位置をスクロール表示
- 複数パネルを同時に開いてアルゴリズムを並べて比較可能

## 対応アルゴリズム

### Ch.3 — vector / イテレータ

| アルゴリズム | 対応サンプル | 説明 |
|---|---|---|
| vector capacity | Sample3_1 | `push_back` による capacity の倍増を可視化 |
| vector 操作 | Sample3_2 | `push_back` / `erase` / `insert` / `reverse` の操作列 |
| イテレータ・3要素合計 | Sample3_3 | テープ表示でイテレータが 3 要素ずつ走査して合計を計算 |

### Ch.4 — 連結リスト

| アルゴリズム | 対応サンプル | 説明 |
|---|---|---|
| 片方向連結リスト | Sample4_2 | `add` / `addFirst` / `deleteFirst` / `deleteNode` / `find` |
| 双方向連結リスト | Sample4_5 | `add` / `deleteNode` / `displayReverse` / `reverse` |

### Ch.5 — スタック / キュー / RPN

| アルゴリズム | 対応サンプル | 説明 |
|---|---|---|
| 連結リストスタック | Sample5_1 | 片方向連結リストによる Push / Pop（top = 先頭ノード） |
| 連結リストキュー | Sample5_8 | 片方向連結リストによる Enqueue / Dequeue（front→back） |
| 配列スタック | Sample5_4 | 配列による Push / Pop（top ポインタ付き） |
| 循環キュー | Sample5_9 | 配列による循環キュー（front / back、ラップアラウンド可視化） |
| RPN 変換・評価 | Sample5_7 | B型単純式 → 逆ポーランド記法変換 + スタック評価 |

## 動作環境

- Python 3.11 以上
- モダンブラウザ（Chrome / Firefox / Safari / Edge）

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/HirotakaUoi/AAforDataStructures.git
cd AAforDataStructures

# 依存パッケージをインストール
pip install -r requirements.txt

# サーバーを起動
python -m uvicorn main:app --port 8006
```

ブラウザで http://localhost:8006 を開いてください。

## 使い方

1. **＋パネル追加** でアニメーションパネルを追加
2. パネルごとにアルゴリズム・データ数・速度を設定
3. **▶ 開始** でアニメーション再生
4. **⏸ 一時停止** / **■ 停止** で制御
5. パネルはドラッグで移動、右下コーナーでリサイズ可能

## ファイル構成

```
AAforDataStructures/
├── main.py              # FastAPI サーバー・WebSocket エンドポイント
├── algorithms.py        # 各データ構造アルゴリズムのジェネレータ
├── requirements.txt
└── static/
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        ├── array_canvas.js  # Canvas 描画ユーティリティ
        │                    #   対応 type: array1d_cells / tape / linked_list
        │                    #             heap_tree / bucket_rows / fib_tree / staircase
        ├── ws_client.js     # WebSocket クライアント
        └── app.js           # パネル管理・メインアプリ
```

## 技術構成

| 要素 | 技術 |
|---|---|
| バックエンド | Python / FastAPI / WebSocket |
| フロントエンド | Vanilla JS / Canvas 2D API |
| アニメーション生成 | Python ジェネレータ（`yield` でフレーム単位に送信） |
| 通信 | WebSocket（フレームごとに JSON をストリーミング） |

## ライセンス

MIT
