/**
 * app.js  –  パネル管理・メインアプリケーション (ArrayAnimation)
 *
 * アルゴリズム種別 (meta.type) に応じて UI を切り替える:
 *   "search" → target 入力あり・データ条件なし
 *   "sort"   → target 入力なし・データ条件 (ランダム/昇順/降順/…) あり
 *   "misc"   → target 入力なし・データ条件なし (固定 N)
 */

"use strict";

// ===== グローバル状態 ==============================================
let algorithms = [];   // [{ id, name, meta }, ...]
let dataSizes  = [];   // [8, 16, ...]
let panelSeq   = 0;
let zoomLevel  = 1.0;

const DATA_CONDITIONS = [
  { id: 0, name: "ランダム" },
  { id: 1, name: "昇順" },
  { id: 2, name: "降順" },
  { id: 3, name: "ほぼ昇順" },
];

// ===== スナップ設定 ================================================
const SNAP_THRESHOLD = 15;
const SNAP_GAP       = 10;

function _getTopLeftPanel(excludeEl = null) {
  let best = null, bestDist = Infinity;
  document.querySelectorAll(".panel").forEach(p => {
    if (p === excludeEl) return;
    const d = Math.sqrt(p.offsetLeft ** 2 + p.offsetTop ** 2);
    if (d < bestDist) { bestDist = d; best = p; }
  });
  return best;
}

function _snapValue(val, snapPoints, threshold) {
  let closest = val, minDiff = threshold;
  for (const sp of snapPoints) {
    const diff = Math.abs(val - sp);
    if (diff < minDiff) { minDiff = diff; closest = sp; }
  }
  return closest;
}

/** アルゴリズム ID から meta.type を返す */
function _algoType(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return algo?.meta?.type || "search";
}

/** アルゴリズム ID が init_data をサポートするか */
function _algoSupportsInitData(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.init_data);
}

/** アルゴリズム ID が ops（操作列）をサポートするか */
function _algoSupportsOps(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.ops);
}

/** アルゴリズム ID がハッシュ関数選択をサポートするか */
function _algoSupportsHashFunc(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.hash_func);
}

/** アルゴリズム ID がソート手法選択をサポートするか */
function _algoSupportsSortMethod(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.sort_method);
}

/** アルゴリズム ID が段数セレクト (depth_select) をサポートするか */
function _algoSupportsDepthSel(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.depth_select);
}

/** アルゴリズム ID が木の再生成ボタン (tree_regen) をサポートするか */
function _algoSupportsTreeRegen(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.tree_regen);
}

/** アルゴリズム ID が走査種別セレクト (traversal_select) をサポートするか */
function _algoSupportsTraversalSel(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.traversal_select);
}

/** アルゴリズム ID が「回転で自動停止」チェックボックス (rotation_pause) をサポートするか */
function _algoSupportsRotationPause(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.rotation_pause);
}

/** アルゴリズム ID が目的ノード指定 (target_node) をサポートするか (グラフ探索用) */
function _algoSupportsTargetNode(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return !!(algo?.meta?.target_node);
}

/** キー型ごとのハッシュ関数オプション */
const _KEY_TYPE_FUNCS = {
  int:   [
    {v:"mod",    l:"除算法  h(k) = k mod m"},
    {v:"mult",   l:"乗算法  h(k) = ⌊m·(k·A mod 1)⌋"},
    {v:"square", l:"二乗法  h(k) = k² mod m"},
    {v:"custom", l:"カスタム… (変数: k=整数, m)"},
  ],
  str:   [
    {v:"sum",    l:"加算折り畳み法  h(k) = Σord(c) mod m"},
    {v:"poly",   l:"多項式ハッシュ  h(k) = Σ(ord(c)·31ⁱ) mod m"},
    {v:"mult",   l:"乗算折り畳み法  h(k) = ⌊m·(Σord(c)·A mod 1)⌋"},
    {v:"custom", l:"カスタム… (変数: k=文字列, m, ord, sum, len)"},
  ],
  float: [
    {v:"mult",   l:"乗算法  h(k) = ⌊m·(k·A mod 1)⌋"},
    {v:"trunc",  l:"切り捨て  h(k) = ⌊k⌋ mod m"},
    {v:"scale",  l:"スケール  h(k) = ⌊k×100⌋ mod m"},
    {v:"custom", l:"カスタム… (変数: k=実数, m, int, round, abs)"},
  ],
};

// ===== 起動 ========================================================
window.addEventListener("DOMContentLoaded", async () => {
  await loadMeta();
  _setupZoomControls();
  _setupThemeControls();
  document.getElementById("btn-add-panel").addEventListener("click", addPanel);
  document.getElementById("btn-start-all").addEventListener("click", startAll);
  document.getElementById("btn-pause-all").addEventListener("click", pauseAll);
  document.getElementById("btn-stop-all") .addEventListener("click", stopAll);
  document.getElementById("btn-reset-all").addEventListener("click", resetAll);
  document.getElementById("btn-sync-size").addEventListener("click", syncSize);
  document.getElementById("btn-apply-global").addEventListener("click", applyGlobalToAll);
  addPanel();
});

async function loadMeta() {
  const [alRes, dsRes] = await Promise.all([
    fetch("/api/algorithms"),
    fetch("/api/datasizes"),
  ]);
  algorithms = await alRes.json();
  dataSizes  = await dsRes.json();

  // global-size セレクトを dataSizes で初期化
  const gSel = document.getElementById("global-size");
  dataSizes.forEach(s => gSel.appendChild(new Option(String(s), s)));
  gSel.value = 16;
}


// ===== テーマ ======================================================

function _setupThemeControls() {
  document.querySelectorAll(".theme-btn").forEach(btn => {
    btn.addEventListener("click", () => _applyTheme(btn.dataset.th));
  });
}

function _applyTheme(key) {
  document.body.dataset.theme = key;
  setCanvasTheme(key);
  document.querySelectorAll(".theme-btn").forEach(b => {
    b.classList.toggle("theme-active", b.dataset.th === key);
  });
  document.querySelectorAll(".panel").forEach(el => {
    const panel = el._panel;
    if (!panel) return;
    if (panel.arrayCanvas && panel._lastFrame) {
      // 実行中・完了後にかかわらず、直近のフレーム（完了時の最終状態を含む）を
      // 保持したままテーマだけ切り替える。ここで preview に戻すと、
      // 完了後の最終状態がテーマ切替のたびに見えなくなってしまう。
      panel.arrayCanvas.canvas = panel.el.querySelector(".array-canvas");
      panel.arrayCanvas.ctx = panel.arrayCanvas.canvas.getContext("2d");
      panel.arrayCanvas.draw(panel._lastFrame);
    } else {
      panel._drawPreview();
    }
  });
}

// ===== ズーム ======================================================

function _applyZoom(level) {
  const ZOOM_MIN = 0.25, ZOOM_MAX = 2.0;
  zoomLevel = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(level * 10) / 10));
  document.getElementById("panels-container").style.transform = `scale(${zoomLevel})`;
  document.getElementById("zoom-label").textContent = Math.round(zoomLevel * 100) + "%";
}

function _setupZoomControls() {
  document.getElementById("btn-zoom-in")   .addEventListener("click", () => _applyZoom(zoomLevel + 0.1));
  document.getElementById("btn-zoom-out")  .addEventListener("click", () => _applyZoom(zoomLevel - 0.1));
  document.getElementById("btn-zoom-reset").addEventListener("click", () => _applyZoom(1.0));
  document.getElementById("panels-container").addEventListener("wheel", (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    _applyZoom(zoomLevel + (e.deltaY < 0 ? 0.1 : -0.1));
  }, { passive: false });
}

// ===== コンテナサイズ更新 ==========================================

function _updateContainerSize() {
  const container = document.getElementById("panels-container");
  let maxRight = 0, maxBottom = 0;
  container.querySelectorAll(".panel").forEach(p => {
    maxRight  = Math.max(maxRight,  p.offsetLeft + p.offsetWidth  + 20);
    maxBottom = Math.max(maxBottom, p.offsetTop  + p.offsetHeight + 20);
  });
  container.style.minWidth  = maxRight  + "px";
  container.style.minHeight = maxBottom + "px";
}

// ===== サイズ統一 ==================================================

function syncSize() {
  const panels = [...document.querySelectorAll(".panel")];
  if (panels.length < 2) return;
  // ユーザーが最後に手動クリック/ドラッグしたパネル (.front) を基準とする。
  // まだ一度もクリックされていなければ zIndex が最大のものを使う。
  const front =
    document.querySelector(".panel.front") ||
    panels.reduce((a, b) =>
      (parseInt(b.style.zIndex) || 1) > (parseInt(a.style.zIndex) || 1) ? b : a
    );
  const w = front.offsetWidth, h = front.offsetHeight;
  panels.forEach(el => {
    if (el !== front) { el.style.width = w + "px"; el.style.height = h + "px"; }
  });
}

// ===== パネル追加 ==================================================
function addPanel() {
  const panel = new ArrayPanel(++panelSeq);
  panel.mount(document.getElementById("panels-container"));
}

// ===== 全開始 / 全一時停止 / 全停止 / 全リセット ====================
function startAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p && !p.isRunning) p.start();
  });
}
function pauseAll() {
  const panels = [...document.querySelectorAll(".panel")]
    .map(el => el._panel).filter(p => p && p.isRunning);
  const anyRunning = panels.some(p => !p.isPaused);
  panels.forEach(p => {
    if (anyRunning && !p.isPaused) p.togglePause();
    else if (!anyRunning && p.isPaused) p.togglePause();
  });
  document.getElementById("btn-pause-all").textContent =
    anyRunning ? "▶ 全再開" : "⏸ 全一時停止";
}
function stopAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p && p.isRunning) p.stop();
  });
  document.getElementById("btn-pause-all").textContent = "⏸ 全一時停止";
}
function resetAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p) p.reset();
  });
  document.getElementById("btn-pause-all").textContent = "⏸ 全一時停止";
}

// ===== 全パネルへ適用 ===============================================
// 全非実行パネルのデータ数を揃え、misc 型は共通シードでプレビューを同期する
function applyGlobalToAll() {
  const n          = Number(document.getElementById("global-size").value);
  const sharedSeed = Math.floor(Math.random() * 1e9);

  document.querySelectorAll(".panel").forEach(el => {
    const panel = el._panel;
    if (!panel || panel.isRunning) return;

    // データ数を統一
    const selSize = el.querySelector(".sel-size");
    if (selSize) selSize.value = n;

    const algoId = Number(el.querySelector(".sel-algo").value);
    const type   = _algoType(algoId);

    if (type === "misc") {
      // misc: 共通シードでプレビューを同期
      const canvas = el.querySelector(".array-canvas");
      const ctx    = canvas.getContext("2d");
      ctx.fillStyle = "#1a1a2e";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      panel._fetchAndDrawPreview(sharedSeed);
    } else {
      panel._drawPreview();
    }
  });
}

// ===================================================================
// ArrayPanel クラス
// ===================================================================
class ArrayPanel {
  constructor(id) {
    this.id                = id;
    this.sessionId         = null;
    this.client            = null;
    this.arrayCanvas       = null;
    this.el                = null;
    this.isRunning         = false;
    this.isPaused          = false;
    this.numItems          = 0;
    this._lastFrame        = null;
    this._frameCount       = 0;
    this._speed            = 0.1;
    this._previewRequestId = 0;   // 非同期プレビューの競合防止カウンタ
    this._seed             = 0;   // グラフ等の乱数シード（プレビューと開始で共有）
    this._sortMethod       = "quick"; // ソート手法（sort_method 対応アルゴのみ）
    this._traversal        = "bfs";   // 走査種別（traversal_select 対応アルゴのみ）
    this._initData         = null; // ユーザー指定の初期配列（init_data 対応アルゴのみ）
    this._ops              = null; // ユーザー指定の操作列（ops 対応アルゴのみ）
    this._hashFunc         = null; // ユーザー指定のハッシュ関数（hash_func 対応アルゴのみ）
    this._keyType          = null; // ユーザー指定のキー型: null | "int" | "str" | "float"
  }

  // ── DOM 構築 ────────────────────────────────────────────────────
  mount(container) {
    const el = document.createElement("div");
    el.className = "panel";
    el._panel    = this;
    el.id        = `panel-${this.id}`;
    el.innerHTML = this._template();

    let initLeft = 0, initTop = 0;
    const existing = container.querySelectorAll(".panel");
    if (existing.length > 0) {
      let maxRight = 0, maxBottom = 0;
      existing.forEach(p => {
        maxRight  = Math.max(maxRight,  p.offsetLeft + p.offsetWidth  + 12);
        maxBottom = Math.max(maxBottom, p.offsetTop  + p.offsetHeight + 12);
      });
      const panelW = 520;
      if (maxRight + panelW <= window.innerWidth) {
        initLeft = maxRight; initTop = 0;
      } else {
        initLeft = 0; initTop = maxBottom;
      }
    }
    el.style.left = initLeft + "px";
    el.style.top  = initTop  + "px";
    container.appendChild(el);
    this.el = el;

    this._bind();
    this._populateSelects();
    this._updateParamVisibility();
    // 生成時は視覚的に最前面へ積むだけ (.front クラスはセットしない)
    // .front はユーザーがクリック/ドラッグしたときだけ付与 → サイズ統一の基準になる
    { let mz = 0;
      document.querySelectorAll(".panel").forEach(p =>
        { mz = Math.max(mz, parseInt(p.style.zIndex) || 1); });
      el.style.zIndex = mz + 1; }
    requestAnimationFrame(() => this._drawPreview());
    return el;
  }

  _template() {
    return `
      <div class="panel-header">
        <span class="drag-handle" title="ドラッグして移動">⠿</span>
        <span class="panel-title">パネル ${this.id}</span>
        <button class="panel-close" title="削除">✕</button>
      </div>

      <div class="params-row">
        <label>アルゴリズム
          <select class="sel-algo"></select>
        </label>
      </div>
      <div class="params-row">
        <label class="lbl-size">データ数
          <select class="sel-size"></select>
        </label>
        <label class="lbl-target">target
          <input type="number" class="inp-target" min="0" max="999" placeholder="自動"
                 style="width:60px" title="探索する値 (空欄=自動)">
        </label>
        <span class="target-info" style="font-size:0.82em;margin-left:-4px"></span>
        <label class="lbl-condition" style="display:none">データ条件
          <select class="sel-condition"></select>
        </label>
        <div class="speed-group">
          <label>速度</label>
          <input type="range" class="rng-speed" min="1" max="200" value="80"
                 title="大きいほど速い">
          <span class="speed-value">×1.0</span>
        </div>
        <div class="tree-ctrl-group"
             style="display:none;align-items:center;gap:8px;margin-left:8px;white-space:nowrap">
          <button class="btn btn-secondary btn-regen-tree"
                  style="display:none;white-space:nowrap">🌳 初期木生成</button>
          <label class="lbl-rotation-pause"
                 style="display:none;align-items:center;gap:4px"
                 title="回転 (LL/RR/LR/RL) が起きるフレームで自動的に一時停止します">
            <input type="checkbox" class="chk-rotation-pause">回転で自動停止
          </label>
        </div>
      </div>

      <div class="params-row init-data-row" style="display:none">
        <label class="lbl-init-data" style="white-space:nowrap;margin-right:6px">初期状態
          <input type="text" class="inp-init-data"
                 placeholder="例: 5 2 7 1  または  5,2,7,1"
                 style="width:100%;max-width:200px;box-sizing:border-box">
        </label>
        <button class="btn btn-secondary btn-set-init-data" style="white-space:nowrap">設定</button>
        <select class="sel-sort-method" style="display:none;flex:0 0 auto;max-width:160px;margin-left:8px">
          <option value="quick">クイックソート</option>
          <option value="shell">シェルソート</option>
          <option value="insert">挿入ソート</option>
        </select>
        <label class="lbl-depth-sel" style="display:none;white-space:nowrap;margin-right:6px">段数
          <select class="sel-depth" style="margin-left:4px">
            <option value="3">3段</option>
            <option value="4">4段</option>
            <option value="5">5段</option>
            <option value="6">6段</option>
          </select>
        </label>
        <label class="lbl-traversal-sel" style="display:none;white-space:nowrap;margin-right:6px">走査
          <select class="sel-traversal" style="margin-left:4px">
            <option value="bfs">BFS</option>
            <option value="preorder">Pre-Order</option>
            <option value="inorder">In-Order</option>
            <option value="postorder">Post-Order</option>
            <option value="all">全走査</option>
          </select>
        </label>
        <span class="init-data-info" style="color:#aaa;font-size:0.82em;min-width:0;flex:1;margin-left:6px"></span>
      </div>

      <div class="params-row ops-row" style="display:none">
        <label class="lbl-ops" style="flex:1;min-width:0;align-self:flex-start;margin-top:2px">操作列
          <textarea class="inp-ops" rows="4"
                    placeholder=""
                    style="width:100%;max-width:320px;box-sizing:border-box;resize:vertical;font-family:monospace;font-size:0.85em"></textarea>
        </label>
        <div style="display:flex;flex-direction:column;gap:4px;align-self:flex-start;margin-top:2px">
          <button class="btn btn-secondary btn-set-ops" style="white-space:nowrap">設定</button>
          <button class="btn btn-secondary btn-clear-ops" style="white-space:nowrap;font-size:0.82em">クリア</button>
        </div>
        <span class="ops-info" style="color:#aaa;font-size:0.82em;min-width:0;flex:1;align-self:flex-start;margin-top:4px"></span>
      </div>

      <div class="params-row key-type-row" style="display:none">
        <label class="row-label" style="white-space:nowrap;margin-right:6px">キー型</label>
        <select class="sel-key-type" style="flex:0 0 auto;max-width:200px">
          <option value="int">整数 (integer)</option>
          <option value="str">文字列 (string)</option>
          <option value="float">実数 (float)</option>
        </select>
        <span class="key-type-info" style="color:#aaa;font-size:0.82em;min-width:0;flex:1;margin-left:8px"></span>
      </div>

      <div class="params-row hash-func-row" style="display:none">
        <label class="row-label" style="white-space:nowrap;margin-right:6px">ハッシュ関数</label>
        <select class="sel-hash-func" style="flex:0 0 auto;max-width:220px">
          <option value="mod">除算法  h(k) = k mod m</option>
          <option value="mult">乗算法  h(k) = ⌊m·(k·A mod 1)⌋</option>
          <option value="square">二乗法  h(k) = k² mod m</option>
          <option value="custom">カスタム…</option>
        </select>
        <input type="text" class="inp-hash-custom"
               placeholder="例: (k*k+k)%m"
               style="display:none;width:120px;font-family:monospace;font-size:0.85em;margin-left:4px">
        <button class="btn btn-secondary btn-set-hash-func" style="white-space:nowrap;margin-left:6px">設定</button>
        <span class="hash-func-info" style="color:#aaa;font-size:0.82em;min-width:0;flex:1;margin-left:6px"></span>
      </div>

      <div class="controls-row">
        <button class="btn btn-primary   btn-start">▶ 開始</button>
        <button class="btn btn-warning   btn-pause" disabled>⏸ 一時停止</button>
        <button class="btn btn-danger    btn-stop"  disabled>⏹ 停止</button>
        <button class="btn btn-secondary btn-reset" disabled>↺ リセット</button>
      </div>

      <div class="canvas-wrapper">
        <canvas class="array-canvas"></canvas>
        <div class="text-overlay">（開始ボタンを押してください）</div>
      </div>

      <div class="status-bar">
        <span class="status-algo">-</span>
        <span class="status-state">待機中</span>
        <span class="status-frames">フレーム: 0</span>
        <span class="status-done-badge"></span>
      </div>
      <div class="resize-handle" title="リサイズ"></div>
    `;
  }

  // ── セレクトを動的に生成 ─────────────────────────────────────
  _populateSelects() {
    const selAlgo = this.el.querySelector(".sel-algo");
    algorithms.forEach(a => selAlgo.appendChild(new Option(a.name, a.id)));
    selAlgo.value = (this.id - 1) % algorithms.length;

    const selSize = this.el.querySelector(".sel-size");
    dataSizes.forEach(s => selSize.appendChild(new Option(String(s), s)));
    selSize.value = document.getElementById("global-size")?.value || 16;

    const selCond = this.el.querySelector(".sel-condition");
    DATA_CONDITIONS.forEach(c => selCond.appendChild(new Option(c.name, c.id)));

    const gSpeed = document.getElementById("global-speed")?.value;
    if (gSpeed) {
      this.el.querySelector(".rng-speed").value = gSpeed;
      this._applySpeed(Number(gSpeed));
    }
  }

  // ── アルゴリズム種別に応じて UI を表示/非表示 ─────────────────
  _updateParamVisibility() {
    const algoId        = Number(this.el.querySelector(".sel-algo").value);
    const type          = _algoType(algoId);
    const hasInitData   = _algoSupportsInitData(algoId);
    const hasDepthSel   = _algoSupportsDepthSel(algoId);
    const hasOps        = _algoSupportsOps(algoId);
    const hasHashFunc   = _algoSupportsHashFunc(algoId);
    const hasTargetNode = _algoSupportsTargetNode(algoId);

    const targetLbl = this.el.querySelector(".lbl-target");
    const targetInp = this.el.querySelector(".inp-target");
    targetLbl.style.display = (type === "search" || hasTargetNode) ? "" : "none";
    if (hasTargetNode) {
      // グラフ探索: target = 目的ノード番号 (空欄なら全ノードを走査する従来モード)
      targetLbl.childNodes[0].textContent = "目的ノード\n";
      targetInp.title = "経路探索する目的ノード番号 (空欄=全ノードを走査)";
      targetInp.placeholder = "空欄=全探索";
    } else {
      targetLbl.childNodes[0].textContent = "target\n";
      targetInp.title = "探索する値 (空欄=自動)";
      targetInp.placeholder = "自動";
    }
    this.el.querySelector(".lbl-condition").style.display = type === "sort"   ? "" : "none";
    // lbl-size は常に表示 (misc でも num_items は参照される)

    // 初期状態行（テキスト入力 or 段数セレクトのいずれかが必要なら表示）
    const algo = algorithms.find(a => a.id === algoId);
    const hasTraversalSel_ = _algoSupportsTraversalSel(algoId);
    const hasTreeRegen     = _algoSupportsTreeRegen(algoId);
    this.el.querySelector(".init-data-row").style.display =
      (hasInitData || hasDepthSel || hasTraversalSel_) ? "" : "none";

    // 段数セレクト表示制御
    const depthLbl = this.el.querySelector(".lbl-depth-sel");
    const depthSel = this.el.querySelector(".sel-depth");
    depthLbl.style.display = hasDepthSel ? "" : "none";
    if (hasDepthSel) {
      // テキスト入力・設定ボタンを隠し、段数セレクトの値を _initData にセット
      this.el.querySelector(".lbl-init-data").style.display = "none";
      this.el.querySelector(".btn-set-init-data").style.display = "none";
      this.el.querySelector(".init-data-info").textContent = "";
      this._initData = [depthSel.value];
    }

    if (!hasInitData && !hasDepthSel) {
      this._initData = null;
      this.el.querySelector(".inp-init-data").value = "";
      this.el.querySelector(".init-data-info").textContent = "";
      // tree_regen のみで行が表示される場合に備えてテキスト入力部分を隠す
      this.el.querySelector(".lbl-init-data").style.display = "none";
      this.el.querySelector(".btn-set-init-data").style.display = "none";
    }
    if (hasInitData) {
      // テキスト入力部分を表示・設定
      this.el.querySelector(".lbl-init-data").style.display = "";
      this.el.querySelector(".btn-set-init-data").style.display = "";
      // ラベルをアルゴリズム固有の名称に変更（なければ「初期状態」）
      const lbl = this.el.querySelector(".lbl-init-data");
      lbl.childNodes[0].textContent = (algo?.meta?.init_data_label || "初期状態") + "\n";
      const hint = algo?.meta?.init_data_hint || "";
      const isExpr = algo?.meta?.init_data_type === "expr";
      const inp = this.el.querySelector(".inp-init-data");
      const row = this.el.querySelector(".init-data-row");
      inp.placeholder = hint || (isExpr ? "式を入力" : "例: 5 2 7 1  または  5,2,7,1");
      // 式入力(RPN/B式)は入力欄を広げる — inline style を直接書いて確実に反映
      if (isExpr) {
        row.classList.add("expr-wide");
        lbl.style.cssText = "display:flex;align-items:center;gap:4px;flex:1 1 0;min-width:0;white-space:nowrap;";
        inp.style.cssText = "flex:1 1 0;min-width:0;max-width:none;box-sizing:border-box;";
      } else {
        row.classList.remove("expr-wide");
        lbl.style.cssText = "white-space:nowrap;margin-right:6px;";
        inp.style.cssText = "width:100%;max-width:200px;box-sizing:border-box;";
      }
    }

    // ソート手法セレクト（init-data-row 内）
    const hasSortMethod = _algoSupportsSortMethod(algoId);
    this.el.querySelector(".sel-sort-method").style.display = hasSortMethod ? "" : "none";
    if (!hasSortMethod) {
      this._sortMethod = "quick";
      this.el.querySelector(".sel-sort-method").value = "quick";
    }

    // 走査種別セレクト（init-data-row 内）+ 初期木生成ボタン（速度設定の隣）
    this.el.querySelector(".lbl-traversal-sel").style.display = hasTraversalSel_ ? "" : "none";
    this.el.querySelector(".btn-regen-tree").style.display    = hasTreeRegen ? "" : "none";

    // 「回転で自動停止」チェックボックス（初期木生成ボタンの右側）
    const hasRotationPause = _algoSupportsRotationPause(algoId);
    this.el.querySelector(".lbl-rotation-pause").style.display =
      hasRotationPause ? "flex" : "none";
    // ボタン or チェックボックスのいずれかが必要なら、まとめグループを表示
    this.el.querySelector(".tree-ctrl-group").style.display =
      (hasTreeRegen || hasRotationPause) ? "flex" : "none";
    if (!hasTraversalSel_) {
      this._traversal = "bfs";
      this.el.querySelector(".sel-traversal").value = "bfs";
    }

    // 操作列行
    this.el.querySelector(".ops-row").style.display = hasOps ? "" : "none";
    if (!hasOps) {
      this._ops = null;
      this.el.querySelector(".inp-ops").value = "";
      this.el.querySelector(".ops-info").textContent = "";
    } else {
      // アルゴリズム固有のプレースホルダーをセット
      const hint = algo?.meta?.ops_hint || "";
      const phLines = hint ? `例（1行1操作）:\n${hint}` : "例（1行1操作）:\nadd(5)\n...";
      this.el.querySelector(".inp-ops").placeholder = phLines;
    }

    // キー型行 & ハッシュ関数行
    this.el.querySelector(".key-type-row") .style.display = hasHashFunc ? "" : "none";
    this.el.querySelector(".hash-func-row").style.display = hasHashFunc ? "" : "none";
    if (!hasHashFunc) {
      this._keyType  = null;
      this._hashFunc = null;
      this.el.querySelector(".sel-key-type").value = "int";
      this.el.querySelector(".key-type-info").textContent = "";
      this.el.querySelector(".sel-hash-func").value = "mod";
      this.el.querySelector(".inp-hash-custom").style.display = "none";
      this.el.querySelector(".hash-func-info").textContent = "";
    } else {
      // キー型が変わっていればドロップダウンを再構築
      const currentKT = this.el.querySelector(".sel-key-type").value || "int";
      this._rebuildHashFuncOptions(currentKT);
    }

    this._validateTargetNode();
  }

  // ── 目的ノード / target 入力のバリデーション ─────────────────
  // 戻り値: 入力が妥当なら true（空欄も妥当＝自動/全探索）、不正なら false
  _validateTargetNode() {
    const algoId = Number(this.el.querySelector(".sel-algo").value);
    const info    = this.el.querySelector(".target-info");
    const inp     = this.el.querySelector(".inp-target");
    info.textContent = "";
    info.className   = "target-info";

    if (!_algoSupportsTargetNode(algoId)) return true;

    const raw = inp.value.trim();
    if (raw === "") return true;   // 空欄 = 全探索（従来モード）

    const n = Number(this.el.querySelector(".sel-size").value) || 0;
    const isIntStr = /^\d+$/.test(raw);
    const v = Number(raw);
    if (!isIntStr || v < 0 || v > n - 1) {
      info.textContent = `⚠ 0〜${Math.max(0, n - 1)} の整数を入力してください`;
      info.className   = "target-info error";
      return false;
    }
    return true;
  }

  // ── イベントバインド ─────────────────────────────────────────
  _bind() {
    const q = (sel) => this.el.querySelector(sel);

    q(".panel-close").addEventListener("click", () => this.destroy());
    q(".btn-start")  .addEventListener("click", () => this.start());
    q(".btn-pause")  .addEventListener("click", () => this.togglePause());
    q(".btn-stop")   .addEventListener("click", () => this.stop());
    q(".btn-reset")  .addEventListener("click", () => this.reset());

    q(".rng-speed").addEventListener("input", (ev) => {
      this._applySpeed(Number(ev.target.value));
    });

    q(".sel-algo").addEventListener("change", () => {
      if (!this.isRunning) { this._updateParamVisibility(); this._drawPreview(); }
    });
    q(".sel-size")     .addEventListener("change", () => {
      this._validateTargetNode();
      if (!this.isRunning) this._drawPreview();
    });
    q(".inp-target")   .addEventListener("input",  () => { this._validateTargetNode(); });
    q(".inp-target")   .addEventListener("change", () => {
      if (!this.isRunning && this._validateTargetNode()) this._drawPreview();
    });
    q(".sel-condition").addEventListener("change", () => { if (!this.isRunning) this._drawPreview(); });

    // 初期状態: 設定ボタン & Enter キー
    q(".btn-set-init-data").addEventListener("click", () => this._applyInitData());
    q(".inp-init-data").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); this._applyInitData(); }
    });

    // 操作列: 設定ボタン / クリアボタン
    q(".btn-set-ops").addEventListener("click", () => this._applyOps());
    q(".btn-clear-ops").addEventListener("click", () => {
      q(".inp-ops").value = "";
      this._ops = null;
      q(".ops-info").style.color = "#aaa";
      q(".ops-info").textContent = "（デフォルト操作列を使用）";
      if (!this.isRunning) this._drawPreview();
    });

    // ソート手法: 変更時にプレビュー更新
    q(".sel-sort-method").addEventListener("change", () => {
      this._sortMethod = q(".sel-sort-method").value;
      if (!this.isRunning) this._drawPreview();
    });

    // 走査種別: 変更時にプレビュー更新
    q(".sel-traversal").addEventListener("change", () => {
      this._traversal = q(".sel-traversal").value;
      if (!this.isRunning) this._drawPreview();
    });

    // 初期木生成: 新しいシードで木を再生成（リセットでは木は変わらない）
    q(".btn-regen-tree").addEventListener("click", () => {
      if (!this.isRunning) this._fetchAndDrawPreview(Math.floor(Math.random() * 1e9));
    });

    // 段数セレクト: 変更時に _initData を更新してプレビュー更新
    q(".sel-depth").addEventListener("change", () => {
      this._initData = [q(".sel-depth").value];
      if (!this.isRunning) this._drawPreview();
    });

    // キー型: 変更時にハッシュ関数ドロップダウンを再構築してプレビュー更新
    q(".sel-key-type").addEventListener("change", () => {
      const kt = q(".sel-key-type").value;
      this._keyType  = kt;
      this._hashFunc = null;  // キー型が変わったらハッシュ関数をリセット
      this._rebuildHashFuncOptions(kt);
      q(".hash-func-info").textContent = "";
      q(".inp-hash-custom").style.display = "none";
      if (!this.isRunning) this._drawPreview();
    });

    // ハッシュ関数: セレクト変更 → カスタム入力欄の表示切替
    q(".sel-hash-func").addEventListener("change", () => {
      const isCustom = q(".sel-hash-func").value === "custom";
      q(".inp-hash-custom").style.display = isCustom ? "" : "none";
    });
    // ハッシュ関数: 設定ボタン & Enter キー
    q(".btn-set-hash-func").addEventListener("click", () => this._applyHashFunc());
    q(".inp-hash-custom").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); this._applyHashFunc(); }
    });

    this.el.addEventListener("mousedown", () => this._bringToFront());

    const ro = new ResizeObserver(() => this._onResize());
    ro.observe(this.el);
    ro.observe(q(".canvas-wrapper"));

    // ── ドラッグ (Pointer Events) ────────────────────────────────
    const handle = q(".drag-handle");
    handle.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      handle.setPointerCapture(e.pointerId);
      this._bringToFront();
      handle.style.cursor = "grabbing";
      let prevX = e.clientX, prevY = e.clientY;

      const onMove = (mv) => {
        const dx = (mv.clientX - prevX) / zoomLevel;
        const dy = (mv.clientY - prevY) / zoomLevel;
        prevX = mv.clientX; prevY = mv.clientY;
        this.el.style.left = ((parseFloat(this.el.style.left) || 0) + dx) + "px";
        this.el.style.top  = ((parseFloat(this.el.style.top)  || 0) + dy) + "px";
        _updateContainerSize();
      };
      const onUp = () => {
        handle.style.cursor = "";
        handle.removeEventListener("pointermove",   onMove);
        handle.removeEventListener("pointerup",     onUp);
        handle.removeEventListener("pointercancel", onUp);
        // リリース時にスナップ適用（ドラッグ中は吸着させない）
        const ref = _getTopLeftPanel(this.el);
        if (ref) {
          const rL = ref.offsetLeft, rT = ref.offsetTop;
          const rR = rL + ref.offsetWidth, rB = rT + ref.offsetHeight;
          const cW = this.el.offsetWidth,   cH = this.el.offsetHeight;
          this.el.style.left = _snapValue(parseFloat(this.el.style.left) || 0,
            [rL, rR - cW, rR + SNAP_GAP, rL - cW - SNAP_GAP], SNAP_THRESHOLD) + "px";
          this.el.style.top  = _snapValue(parseFloat(this.el.style.top)  || 0,
            [rT, rB - cH, rB + SNAP_GAP, rT - cH - SNAP_GAP], SNAP_THRESHOLD) + "px";
          _updateContainerSize();
        }
      };
      handle.addEventListener("pointermove",   onMove);
      handle.addEventListener("pointerup",     onUp);
      handle.addEventListener("pointercancel", onUp);
    });

    // ── リサイズ (Pointer Events) ────────────────────────────────
    const resizeEl = q(".resize-handle");
    resizeEl.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      resizeEl.setPointerCapture(e.pointerId);
      let prevX = e.clientX, prevY = e.clientY;

      const onMove = (mv) => {
        const dx = (mv.clientX - prevX) / zoomLevel;
        const dy = (mv.clientY - prevY) / zoomLevel;
        prevX = mv.clientX; prevY = mv.clientY;
        this.el.style.width  = Math.max(280, this.el.offsetWidth  + dx) + "px";
        this.el.style.height = Math.max(340, this.el.offsetHeight + dy) + "px";
      };
      const onUp = () => {
        resizeEl.removeEventListener("pointermove",   onMove);
        resizeEl.removeEventListener("pointerup",     onUp);
        resizeEl.removeEventListener("pointercancel", onUp);
      };
      resizeEl.addEventListener("pointermove",   onMove);
      resizeEl.addEventListener("pointerup",     onUp);
      resizeEl.addEventListener("pointercancel", onUp);
    });
  }

  // ── 初期状態の解析・適用 ───────────────────────────────────────
  _applyInitData() {
    const raw  = this.el.querySelector(".inp-init-data").value.trim();
    const info = this.el.querySelector(".init-data-info");

    if (!raw) {
      // 空欄 → クリア（デフォルトに戻す）
      this._initData = null;
      info.style.color = "#aaa";
      info.textContent = "（デフォルトデータを使用）";
      if (!this.isRunning) this._drawPreview();
      return;
    }

    // 式入力モードか整数リストモードかを判定
    const algoId = parseInt(this.el.querySelector(".sel-algo").value, 10);
    const algo   = algorithms.find(a => a.id === algoId);
    const isExpr = algo?.meta?.init_data_type === "expr";

    if (isExpr) {
      // 式モード: 空白・コンマで分割してトークン配列として保持
      // （B型式: "(2 + 3)" → ["(2","+","3)"] → アルゴリズム側で join して "(2+3)"）
      // （A型式: "2 3 + 8 1 - *" → ["2","3","+","8","1","-","*"] → 7トークン）
      const tokens = raw.split(/[\s,]+/).filter(t => t.length > 0);
      if (tokens.length === 0) {
        this._initData = null;
        info.style.color = "#aaa";
        info.textContent = "（デフォルト式を使用）";
        if (!this.isRunning) this._drawPreview();
        return;
      }
      this._initData = tokens;
      info.style.color = "#44cc88";
      info.textContent = `✓ 式: ${tokens.join(" ")}`;
    } else {
      // 整数リストモード: コンマ・空白区切りで整数をパース
      const tokens = raw.split(/[\s,]+/).filter(s => s !== "");
      const nums   = tokens.map(s => parseInt(s, 10));
      if (nums.some(isNaN) || nums.length === 0) {
        info.style.color = "#ff6666";
        info.textContent = "⚠ 整数をコンマまたは空白で区切って入力してください";
        return;
      }
      this._initData = nums;
      info.style.color = "#44cc88";
      const preview = nums.slice(0, 8).join(", ") + (nums.length > 8 ? " …" : "");
      info.textContent = `✓ ${nums.length} 個: ${preview}`;
    }

    if (!this.isRunning) this._drawPreview();
  }

  // ── 操作列の解析・適用 ─────────────────────────────────────────
  _applyOps() {
    const raw  = this.el.querySelector(".inp-ops").value.trim();
    const info = this.el.querySelector(".ops-info");

    if (!raw) {
      this._ops = null;
      info.style.color = "#aaa";
      info.textContent = "（デフォルト操作列を使用）";
      if (!this.isRunning) this._drawPreview();
      return;
    }

    // 改行・セミコロン区切りで操作を分割し、空行・コメント行を除去
    const lines = raw.split(/[\n;]+/)
      .map(s => s.trim())
      .filter(s => s && !s.startsWith("#"));

    if (lines.length === 0) {
      info.style.color = "#ff6666";
      info.textContent = "⚠ 有効な操作が1つもありません";
      return;
    }

    this._ops = lines;
    info.style.color = "#44cc88";
    const preview = lines.slice(0, 3).join(", ") + (lines.length > 3 ? " …" : "");
    info.textContent = `✓ ${lines.length} 操作: ${preview}`;

    if (!this.isRunning) this._drawPreview();
  }

  // ── ハッシュ関数ドロップダウン再構築 ─────────────────────────
  _rebuildHashFuncOptions(keyType) {
    const sel   = this.el.querySelector(".sel-hash-func");
    const funcs = _KEY_TYPE_FUNCS[keyType] || _KEY_TYPE_FUNCS.int;
    const prev  = sel.value;
    sel.innerHTML = "";
    funcs.forEach(f => {
      const opt = new Option(f.l, f.v);
      sel.appendChild(opt);
    });
    // 前の選択肢が存在すれば維持、なければ先頭
    if (funcs.some(f => f.v === prev)) sel.value = prev;
    // カスタム入力欄の可視状態を同期
    this.el.querySelector(".inp-hash-custom").style.display =
      sel.value === "custom" ? "" : "none";
  }

  // ── ハッシュ関数の解析・適用 ───────────────────────────────────
  _applyHashFunc() {
    const q    = (sel) => this.el.querySelector(sel);
    const sel  = q(".sel-hash-func").value;
    const info = q(".hash-func-info");

    if (sel === "custom") {
      const formula = q(".inp-hash-custom").value.trim().replace(/\s+/g, "");
      if (!formula) {
        info.style.color = "#ff6666";
        info.textContent = "⚠ 式を入力してください  例: (k*k)%m";
        return;
      }
      this._hashFunc = formula;
      info.style.color = "#44cc88";
      info.textContent = `✓ カスタム: ${formula}`;
    } else {
      this._hashFunc = sel;
      const labels = { mod: "除算法 (mod)", mult: "乗算法 (mult)", square: "二乗法 (square)" };
      info.style.color = "#44cc88";
      info.textContent = `✓ ${labels[sel] || sel}`;
    }

    if (!this.isRunning) this._drawPreview();
  }

  // ── 最前面へ ──────────────────────────────────────────────────
  _bringToFront() {
    let maxZ = 0;
    document.querySelectorAll(".panel").forEach(p => {
      maxZ = Math.max(maxZ, parseInt(p.style.zIndex) || 1);
    });
    this.el.style.zIndex = maxZ + 1;
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("front"));
    this.el.classList.add("front");
  }

  // ── リサイズハンドラ ─────────────────────────────────────────
  _onResize() {
    const ref = _getTopLeftPanel(this.el);
    if (ref) {
      const snapW = _snapValue(this.el.offsetWidth,  [ref.offsetWidth],  SNAP_THRESHOLD);
      const snapH = _snapValue(this.el.offsetHeight, [ref.offsetHeight], SNAP_THRESHOLD);
      if (snapW !== this.el.offsetWidth)  this.el.style.width  = snapW + "px";
      if (snapH !== this.el.offsetHeight) this.el.style.height = snapH + "px";
    }

    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth, h = wrapper.clientHeight;
    if (w <= 0 || h <= 0) return;

    const sizeChanged = (canvas.width !== w || canvas.height !== h);
    if (!sizeChanged) return;
    canvas.width = w; canvas.height = h;

    if (this._lastFrame) {
      const ac = new ArrayCanvas(canvas);
      if (this.isRunning && this.arrayCanvas) {
        this.arrayCanvas.canvas = canvas;
        this.arrayCanvas.ctx    = canvas.getContext("2d");
      }
      ac.draw(this._lastFrame);
    } else {
      this._drawPreviewOnCanvas(canvas);
    }
  }

  // ── プレビュー描画 ──────────────────────────────────────────
  _drawPreview() {
    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight || Math.round(w * 0.55);
    if (w <= 0) return;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    this._drawPreviewOnCanvas(canvas);
  }

  /** 全パネル一括適用: 外部から共有データを渡して search プレビューを描画 */
  _applySharedPreview(sharedValues, targetRaw) {
    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight || Math.round(w * 0.55);
    if (w <= 0) return;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    const algoId = Number(this.el.querySelector(".sel-algo").value);
    const algo   = algorithms.find(a => a.id === algoId);
    const sorted = !!(algo?.meta?.sorted);
    const forced = targetRaw !== "" ? Number(targetRaw) : null;
    this._previewCache = new ArrayCanvas(canvas).drawPreview(
      sharedValues.length, sorted, forced, sharedValues, true, "cells"
    );
  }

  _drawPreviewOnCanvas(canvas) {
    const numItems = Number(this.el.querySelector(".sel-size").value) || 16;
    const algoId   = Number(this.el.querySelector(".sel-algo").value);
    const algo     = algorithms.find(a => a.id === algoId);
    const type     = algo?.meta?.type || "search";

    // misc 型: まず暗色で塗り、非同期でサーバーから初期フレームを取得して描画
    if (type === "misc") {
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#1a1a2e";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      this._fetchAndDrawPreview();
      return;
    }

    const sorted     = !!(algo?.meta?.sorted);
    const showTarget = (type === "search");
    const tRaw       = this.el.querySelector(".inp-target").value.trim();
    const forced     = (showTarget && tRaw !== "") ? Number(tRaw) : null;
    this._previewCache = new ArrayCanvas(canvas).drawPreview(
      numItems, sorted, forced, null, showTarget, "cells"
    );
  }

  /** misc アルゴリズムの初期フレームをサーバーから取得してキャンバスに描画する。
   *  forcedSeed が指定された場合はそのシードを使う（全パネル一括適用用）。 */
  async _fetchAndDrawPreview(forcedSeed = null) {
    const numItems  = Number(this.el.querySelector(".sel-size").value) || 16;
    const algoId    = Number(this.el.querySelector(".sel-algo").value);
    const requestId = ++this._previewRequestId;

    // tree_regen 対応アルゴ（二分木走査・BST・AVL木）/ target_node 対応アルゴ（DFS/BFS）は
    // シードを固定し、明示的な forcedSeed 指定時のみ再生成する。
    // これが無いと「目的ノードを入力→開始」のように .inp-target が blur した際の
    // change イベントで意図せず別のグラフに再抽選されてしまい、
    // プレビュー表示と実際に開始されるアニメーションが食い違うバグになる。
    const keepSeed = (_algoSupportsTreeRegen(algoId) || _algoSupportsTargetNode(algoId)) && this._seed;
    if (forcedSeed !== null) {
      this._seed = forcedSeed;
    } else if (!keepSeed) {
      this._seed = Math.floor(Math.random() * 1e9);
    }
    try {
      let previewUrl = `/api/preview?algorithm_id=${algoId}&n=${numItems}&seed=${this._seed}`;
      {
        // init_data: ハッシュ関数対応アルゴはキー型・ハッシュ関数トークンも追加
        const supportsHashFunc = _algoSupportsHashFunc(algoId);
        const initTokens = [...(this._initData || [])];
        if (supportsHashFunc) {
          if (this._keyType  && this._keyType  !== "int") initTokens.push(this._keyType);
          if (this._hashFunc) initTokens.push(this._hashFunc);
        }
        if (initTokens.length > 0) {
          previewUrl += `&init_data=${encodeURIComponent(initTokens.join(","))}`;
        }
      }
      if (this._ops && this._ops.length > 0) {
        previewUrl += `&ops=${encodeURIComponent(this._ops.join("\n"))}`;
      }
      if (_algoSupportsSortMethod(algoId)) {
        previewUrl += `&sort_method=${this._sortMethod}`;
      }
      if (_algoSupportsTraversalSel(algoId)) {
        previewUrl += `&traversal=${this._traversal}`;
      }
      if (_algoSupportsTargetNode(algoId)) {
        const tRaw = this.el.querySelector(".inp-target").value.trim();
        if (tRaw !== "" && this._validateTargetNode()) {
          previewUrl += `&target=${encodeURIComponent(tRaw)}`;
        }
      }
      const res = await fetch(previewUrl);
      if (!res.ok) return;
      const frame = await res.json();

      // 後から来た別のリクエストで上書き済み、または実行開始済みなら無視
      if (requestId !== this._previewRequestId || this.isRunning) return;

      const wrapper = this.el.querySelector(".canvas-wrapper");
      const canvas  = this.el.querySelector(".array-canvas");
      const w = wrapper.clientWidth;
      const h = wrapper.clientHeight || Math.round(w * 0.55);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w; canvas.height = h;
      }

      this._lastFrame = frame;
      new ArrayCanvas(canvas).draw(frame);

      // テキストオーバーレイ: フレームのテキストを表示（キャンバス描画と重複しないよう非表示）
      this.el.querySelector(".text-overlay").textContent = "";
    } catch (_) {
      // ネットワークエラーなどは無視
    }
  }

  // ── スピード変換 ─────────────────────────────────────────────
  _applySpeed(sliderVal) {
    const speed = Math.round(800 / sliderVal * 10) / 1000;
    const mult  = Math.round(sliderVal / 80 * 10) / 10;
    this.el.querySelector(".speed-value").textContent = `×${mult.toFixed(1)}`;
    if (this.client) this.client.setSpeed(speed);
    this._speed = speed;
  }

  _currentSpeed() {
    const v = Number(this.el.querySelector(".rng-speed").value);
    return Math.round(200 / v * 10) / 1000;
  }

  // ── 開始 ────────────────────────────────────────────────────────
  async start() {
    if (this.isRunning) return;

    if (!this._validateTargetNode()) {
      this._setStatus("エラー: 目的ノードの入力が不正です", "red");
      return;
    }

    const algoId   = Number(this.el.querySelector(".sel-algo").value);
    const numItems = Number(this.el.querySelector(".sel-size").value);
    const speed    = this._currentSpeed();
    const type     = _algoType(algoId);

    let info;
    try {
      const body = { algorithm_id: algoId, num_items: numItems, speed, seed: this._seed };

      if (type === "search") {
        const tRaw = this.el.querySelector(".inp-target").value.trim();
        if (tRaw !== "") {
          body.target = Number(tRaw);
        } else if (this._previewCache?.target !== undefined && this._previewCache.target !== null) {
          body.target = this._previewCache.target;
        }
        if (this._previewCache?.values) {
          body.data = this._previewCache.values;
        }
      } else if (type === "sort") {
        body.data_condition = Number(this.el.querySelector(".sel-condition").value);
        if (this._previewCache?.values) {
          body.data = this._previewCache.values;
        }
      }
      // misc: init_data / ops が設定されていれば一緒に送る
      if (type === "misc") {
        // ハッシュ関数対応アルゴはキー型・ハッシュ関数トークンも init_data に追加
        const supportsHashFunc = _algoSupportsHashFunc(algoId);
        const initTokens = [...(this._initData || [])];
        if (supportsHashFunc) {
          if (this._keyType  && this._keyType  !== "int") initTokens.push(this._keyType);
          if (this._hashFunc) initTokens.push(this._hashFunc);
        }
        if (initTokens.length > 0) body.init_data = initTokens;
        if (this._ops && this._ops.length > 0) body.ops = this._ops;
        if (_algoSupportsSortMethod(algoId))   body.sort_method = this._sortMethod;
        if (_algoSupportsTraversalSel(algoId)) body.traversal   = this._traversal;
        if (_algoSupportsRotationPause(algoId)) {
          body.rotation_pause = !!this.el.querySelector(".chk-rotation-pause")?.checked;
        }
        if (_algoSupportsTargetNode(algoId)) {
          const tRaw = this.el.querySelector(".inp-target").value.trim();
          if (tRaw !== "") body.target = Number(tRaw);
        }
      }

      const res = await fetch("/api/start", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      info = await res.json();
    } catch (e) {
      this._setStatus(`エラー: ${e.message}`, "red");
      return;
    }

    this.sessionId   = info.session_id;
    this.numItems    = info.num_items;
    this.isRunning   = true;
    this.isPaused    = false;
    this._lastFrame  = null;
    this._frameCount = 0;

    const canvas = this.el.querySelector(".array-canvas");
    this.arrayCanvas = new ArrayCanvas(canvas);

    this.el.querySelector(".panel-title").textContent = info.algo_name;
    this.el.classList.add("running");
    this.el.classList.remove("finished");
    this._setStatus("実行中", "#90caf9");
    this._setBtns({ start: false, pause: true, stop: true, reset: false });
    this.el.querySelector(".status-algo").textContent   = info.algo_name;
    this.el.querySelector(".text-overlay").textContent  = "";
    this._clearDoneBadge();

    this.client = new AnimationClient(
      this.sessionId,
      (frame) => this._onFrame(frame),
      ()      => this._onClose(),
      ()      => this._setStatus("接続エラー", "red"),
    );
    this.client.connect();
  }

  // ── フレーム受信 ─────────────────────────────────────────────
  _onFrame(frame) {
    this._lastFrame  = frame;
    this._frameCount = (this._frameCount ?? 0) + 1;

    this.arrayCanvas.draw(frame);
    this.el.querySelector(".status-frames").textContent = `フレーム: ${this._frameCount}`;

    // 「回転で自動停止」: 回転フレーム (objects に rotation を持つ) で一時停止
    const chk = this.el.querySelector(".chk-rotation-pause");
    const autoPause = chk && chk.offsetParent !== null && chk.checked;
    if (autoPause && !frame.finished && !this.isPaused &&
        Array.isArray(frame.objects) && frame.objects.some(o => o && o.rotation)) {
      this.togglePause();
      this._setStatus("回転で自動停止", "#FFD700");
    }

    if (frame.finished) {
      this.isRunning = false;
      this.el.classList.remove("running");
      this.el.classList.add("finished");
      this._setStatus("完了", "#44aa44");
      this._setBtns({ start: false, pause: false, stop: false, reset: true });
      // 探索結果(found)・計算結果(result)・単純完了のいずれも、
      // キャンバス上のデータ構造をdim/隠さず、ステータスバーのバッジにのみ表示する。
      // バッジは固定の背景色を持つため、カラーテーマが変わっても視認性が落ちない。
      this._showDoneBadge(frame);
    }
  }

  _showDoneBadge(frame) {
    const badge = this.el.querySelector(".status-done-badge");
    badge.classList.remove("badge-found", "badge-notfound", "badge-error", "badge-result", "flash");
    if (frame.result !== null && frame.result !== undefined) {
      const isError = typeof frame.result === "string" && frame.result.startsWith("エラー");
      badge.textContent = isError ? `❌ ${frame.result}` : `✅ 結果 = ${frame.result}`;
      badge.classList.add(isError ? "badge-error" : "badge-result");
    } else if (frame.found === true) {
      badge.textContent = "✅ Found !";
      badge.classList.add("badge-found");
    } else if (frame.found === false) {
      badge.textContent = "❌ Not Found";
      badge.classList.add("badge-notfound");
    } else {
      badge.textContent = "🎉 完了!";
    }
    badge.classList.add("visible");
    // 一時的に目立たせてから、常設のステータス表示に落ち着かせる
    void badge.offsetWidth; // reflow でアニメーションを再トリガー
    badge.classList.add("flash");
  }

  _clearDoneBadge() {
    const badge = this.el.querySelector(".status-done-badge");
    badge.textContent = "";
    badge.classList.remove("visible", "badge-found", "badge-notfound", "badge-error", "badge-result", "flash");
  }

  // ── WebSocket クローズ ────────────────────────────────────────
  _onClose() {
    if (this.isRunning) {
      this.isRunning = false;
      this.el.classList.remove("running");
      this._setStatus("切断", "#888");
      this._setBtns({ start: true, pause: false, stop: false, reset: false });
    }
  }

  // ── 一時停止 / 再開 ────────────────────────────────────────────
  togglePause() {
    if (!this.isRunning) return;
    this.isPaused = !this.isPaused;
    const btn = this.el.querySelector(".btn-pause");
    if (this.isPaused) {
      this.client.pause();
      btn.textContent = "▶ 再開";
      this._setStatus("一時停止", "#FFD700");
    } else {
      this.client.resume();
      btn.textContent = "⏸ 一時停止";
      this._setStatus("実行中", "#90caf9");
    }
  }

  // ── 停止 ─────────────────────────────────────────────────────
  stop() {
    if (!this.isRunning) return;
    this.client?.stop();
    this.client?.disconnect();
    this.client    = null;
    this.isRunning = false;
    this.el.classList.remove("running");
    this._setStatus("停止", "#888");
    this._setBtns({ start: true, pause: false, stop: false, reset: true });
  }

  // ── リセット ─────────────────────────────────────────────────
  reset() {
    if (this.isRunning) this.stop();
    this.el.querySelector(".text-overlay").textContent  = "（開始ボタンを押してください）";
    this.el.querySelector(".status-frames").textContent = "フレーム: 0";
    this._clearDoneBadge();
    this.el.classList.remove("finished");
    this._setStatus("待機中", "#888");
    this._setBtns({ start: true, pause: false, stop: false, reset: false });
    this.arrayCanvas = null;
    this._lastFrame  = null;
    this._frameCount = 0;
    this._drawPreview();
  }

  // ── パネル削除 ───────────────────────────────────────────────
  destroy() {
    this.stop();
    this.el?.remove();
  }

  // ── ヘルパー ─────────────────────────────────────────────────
  _setBtns({ start, pause, stop, reset }) {
    const q = (s) => this.el.querySelector(s);
    q(".btn-start").disabled = !start;
    q(".btn-pause").disabled = !pause;
    q(".btn-stop") .disabled = !stop;
    q(".btn-reset").disabled = !reset;
    if (!pause) q(".btn-pause").textContent = "⏸ 一時停止";
  }

  _setStatus(text, color = "#aaa") {
    const el = this.el.querySelector(".status-state");
    el.textContent = text;
    el.style.color = color;
  }
}
