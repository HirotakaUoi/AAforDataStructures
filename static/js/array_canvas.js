/**
 * array_canvas.js  –  多種オブジェクト描画ユーティリティ
 *
 * 対応オブジェクト type:
 *   array1d        – 縦棒グラフ (後方互換)
 *   array1d_cells  – 正方形セル配列
 *   heap_tree      – ヒープ二分木
 *   bucket_rows    – バケツ行 / 動的キュー
 *   tape           – 無端テープ
 *   fib_tree       – フィボナッチ再帰木
 *   staircase      – 階段状テキスト (階乗再帰)
 *   row            – 横並びコンテナ (children を weight 比で水平分割)
 *   col            – row の子として使用: 縦並びサブコンテナ
 */

"use strict";

// ---------------------------------------------------------------------------
// カラーテーマ (canvas 背景・ラベル色のみ; オブジェクト色はフレームデータ側)
// ---------------------------------------------------------------------------
const AC_THEMES = {
  dark: {
    canvasBg: "#0d1117",  valueLabelColor: "#ccc",  indexLabelColor: "#4a6080",
    foundCellBg: "#1a4a1a", foundCellText: "#44cc44",
    cellBg: "#1c2a3a",    cellEmptyBg: "#0a0e18",   nodeBg: "#0d1117",
    cellText: "#ffffff",  cellValueColor: "#dddddd",
    edgeColor: "#334455", dimEdge: "#1a2535",       ghostFill: "#0f1820",
    ghostStroke: "#1c2d3e", ghostText: "#253545",
    labelColor: "#6a8faf", badgeText: "#0d1117",
    emptyText: "#445566", textOverlay: "rgba(10,14,26,0.85)",
    connectorColor: "#2a4060",
  },
  bright: {
    canvasBg: "#f0f4ff",  valueLabelColor: "#334",  indexLabelColor: "#668",
    foundCellBg: "#b8f0b8", foundCellText: "#005500",
    cellBg: "#d8e8f8",    cellEmptyBg: "#e4eefa",   nodeBg: "#dce8f4",
    cellText: "#1a2a3a",  cellValueColor: "#223344",
    edgeColor: "#6688aa", dimEdge: "#99aabb",       ghostFill: "#dce8f4",
    ghostStroke: "#aabbcc", ghostText: "#8899aa",
    labelColor: "#6a8faf", badgeText: "#0d1117",
    emptyText: "#667788", textOverlay: "rgba(10,20,40,0.88)",
    connectorColor: "#6688aa",
  },
  hc: {
    canvasBg: "#000000",  valueLabelColor: "#fff",  indexLabelColor: "#888",
    foundCellBg: "#003300", foundCellText: "#00ff66",
    cellBg: "#182030",    cellEmptyBg: "#060810",   nodeBg: "#000000",
    cellText: "#ffffff",  cellValueColor: "#eeeeee",
    edgeColor: "#557799", dimEdge: "#223344",       ghostFill: "#080c14",
    ghostStroke: "#223344", ghostText: "#445566",
    labelColor: "#8899aa", badgeText: "#000000",
    emptyText: "#556677", textOverlay: "rgba(0,0,0,0.90)",
    connectorColor: "#446688",
  },
  hcbright: {
    canvasBg: "#ffffff",  valueLabelColor: "#111",  indexLabelColor: "#445",
    foundCellBg: "#a8eea8", foundCellText: "#003300",
    cellBg: "#d0e0f0",    cellEmptyBg: "#e4eefa",   nodeBg: "#dce8f4",
    cellText: "#1a2a3a",  cellValueColor: "#1a2a3a",
    edgeColor: "#5577aa", dimEdge: "#99aabb",       ghostFill: "#dce8f4",
    ghostStroke: "#aabbcc", ghostText: "#8899aa",
    labelColor: "#5577aa", badgeText: "#0d1117",
    emptyText: "#556677", textOverlay: "rgba(10,20,40,0.88)",
    connectorColor: "#5577aa",
  },
};
let _acThemeKey = "dark";
function _acTheme() { return AC_THEMES[_acThemeKey] ?? AC_THEMES.dark; }
/** app.js から呼ばれる */
function setCanvasTheme(k) { _acThemeKey = k; }

class ArrayCanvas {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx    = canvas.getContext("2d");
  }

  get cw() { return this.canvas.width;  }
  get ch() { return this.canvas.height; }

  // ── メイン描画 ────────────────────────────────────────────────────
  draw(frame) {
    const { objects = [], texts = [], finished = false, found = null,
            text_position = "top", result = null } = frame;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.cw, this.ch);

    // 背景
    ctx.fillStyle = _acTheme().canvasBg;
    ctx.fillRect(0, 0, this.cw, this.ch);

    const nObjs = objects.length;
    if (nObjs > 0) {
      // weight で高さを比例配分
      const totalW = objects.reduce((s, o) => s + (o.weight || 1), 0);
      let areaY = 0;
      for (let oi = 0; oi < nObjs; oi++) {
        const eachH = this.ch * (objects[oi].weight || 1) / totalW;
        const obj   = objects[oi];
        switch (obj.type) {
          case "array1d":       this._drawArray1d(obj, areaY, eachH);      break;
          case "array1d_cells": this._drawArray1dCells(obj, areaY, eachH); break;
          case "heap_tree":     this._drawHeapTree(obj, areaY, eachH);     break;
          case "bucket_rows":   this._drawBucketRows(obj, areaY, eachH);   break;
          case "tape":          this._drawTape(obj, areaY, eachH);         break;
          case "fib_tree":      this._drawFibTree(obj, areaY, eachH);      break;
          case "staircase":     this._drawStaircase(obj, areaY, eachH);    break;
          case "linked_list":   this._drawLinkedList(obj, areaY, eachH);   break;
          case "stack_v":          this._drawStackV(obj, areaY, eachH);          break;
          case "expr_stack_view":  this._drawExprStackView(obj, areaY, eachH);  break;
          case "queue_circ":       this._drawQueueCirc(obj, areaY, eachH);      break;
          case "bst_tree":      this._drawBstTree(obj, areaY, eachH);      break;
          case "row": {
            // 子オブジェクトを weight 比で水平分割して描画
            const children = obj.children || [];
            const totalCW  = children.reduce((s, c) => s + (c.weight || 1), 0);
            let childX = 0;
            for (const child of children) {
              const childW = this.cw * (child.weight || 1) / totalCW;
              switch (child.type) {
                case "stack_v":      this._drawStackV(child, areaY, eachH, childX, childW);      break;
                case "bst_tree":     this._drawBstTree(child, areaY, eachH, childX, childW);     break;
                case "linked_list":  this._drawLinkedList(child, areaY, eachH, childX, childW);  break;
                case "array1d_cells":this._drawArray1dCells(child, areaY, eachH, childX, childW);break;
                case "col": {
                  // row の中で縦に子を並べる
                  const colChildren = child.children || [];
                  const totalColW = colChildren.reduce((s, c) => s + (c.weight || 1), 0);
                  let colY = areaY;
                  for (const cc of colChildren) {
                    const ccH = eachH * (cc.weight || 1) / totalColW;
                    switch (cc.type) {
                      case "array1d_cells": this._drawArray1dCells(cc, colY, ccH, childX, childW); break;
                      case "linked_list":   this._drawLinkedList(cc, colY, ccH, childX, childW);   break;
                      case "stack_v":       this._drawStackV(cc, colY, ccH, childX, childW);       break;
                    }
                    colY += ccH;
                  }
                  break;
                }
                default: break;
              }
              childX += childW;
            }
            break;
          }
          case "graph_view":  this._drawGraphView(obj, areaY, eachH);  break;
          case "hash_table":  this._drawHashTable(obj, areaY, eachH);  break;
          case "btree_view":  this._drawBtreeView(obj, areaY, eachH);  break;
          case "op_list":     this._drawOpList(obj, areaY, eachH);     break;
        }
        areaY += eachH;
      }
    }

    // テキストオーバーレイ (top または bottom)
    if (texts.length > 0) {
      const TEXT_LINE_H = 18;
      const pad  = 6;
      const boxH = texts.length * TEXT_LINE_H + pad * 2;
      ctx.save();
      ctx.fillStyle = _acTheme().textOverlay;
      if (text_position === "bottom") {
        const boxY = this.ch - boxH;
        ctx.fillRect(0, boxY, this.cw, boxH);
        ctx.font = "13px monospace";
        for (let i = 0; i < texts.length; i++) {
          ctx.fillStyle = texts[i].color || "#ddd";
          ctx.textAlign = "left";
          ctx.fillText(texts[i].message, 8, boxY + pad + (i + 1) * TEXT_LINE_H - 3);
        }
      } else {
        ctx.fillRect(0, 0, this.cw, boxH);
        ctx.font = "13px monospace";
        for (let i = 0; i < texts.length; i++) {
          ctx.fillStyle = texts[i].color || "#ddd";
          ctx.textAlign = "left";
          ctx.fillText(texts[i].message, 8, pad + (i + 1) * TEXT_LINE_H - 3);
        }
      }
      ctx.restore();
    }

    // 完了オーバーレイ
    if (finished) {
      ctx.save();
      ctx.fillStyle = "rgba(0,0,0,.55)";
      ctx.fillRect(0, 0, this.cw, this.ch);
      const fs = Math.min(36, this.cw / 8);
      if (result !== null) {
        // result フィールドがある場合: 計算結果またはエラーを表示
        const isError = typeof result === "string" && result.startsWith("エラー");
        const bgColor  = isError ? "rgba(90,0,0,.80)"  : "rgba(0,70,0,.80)";
        const txtColor = isError ? "#ff9999"            : "#88ffbb";
        ctx.fillStyle = bgColor;
        const boxH = fs * 2.6;
        ctx.fillRect(0, this.ch / 2 - boxH / 2, this.cw, boxH);
        // テキストサイズをキャンバス幅に合わせて自動縮小
        let rfs = Math.min(fs * 1.1, this.cw / 10);
        ctx.font = `bold ${rfs}px monospace`;
        while (ctx.measureText(String(result)).width > this.cw - 16 && rfs > 10) {
          rfs -= 1;
          ctx.font = `bold ${rfs}px monospace`;
        }
        ctx.fillStyle = txtColor;
        ctx.textAlign = "center";
        ctx.fillText(String(result), this.cw / 2, this.ch / 2 + rfs * 0.38);
      } else if (found === true) {
        ctx.fillStyle = "rgba(0,80,0,.75)";
        ctx.fillRect(0, this.ch / 2 - fs * 1.2, this.cw, fs * 2.4);
        ctx.fillStyle = "#44ff88";
        ctx.font      = `bold ${fs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText("Found !", this.cw / 2, this.ch / 2 + fs * 0.38);
      } else if (found === false) {
        ctx.fillStyle = "rgba(80,0,0,.75)";
        ctx.fillRect(0, this.ch / 2 - fs * 1.2, this.cw, fs * 2.4);
        ctx.fillStyle = "#ff6666";
        ctx.font      = `bold ${fs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText("Not Found", this.cw / 2, this.ch / 2 + fs * 0.38);
      } else {
        ctx.fillStyle = "#FFD700";
        ctx.font      = `bold ${fs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText("完了!", this.cw / 2, this.ch / 2 + fs * 0.35);
      }
      ctx.restore();
    }
  }

  // ════════════════════════════════════════════════════════════════════
  // array1d – 縦棒グラフ (後方互換)
  // ════════════════════════════════════════════════════════════════════
  _drawArray1d(obj, areaY, areaH) {
    const {
      values = [], label = "",
      highlights = {}, fills = [],
      pointer = null, watchman_index = null,
      target    = null,
      log_scale = false,
    } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T = 22; const PAD_B = 16; const PAD_L = 8; const PAD_R = 8;

    const HAS_TARGET = target !== null;
    const REF_W   = HAS_TARGET ? 30 : 0;
    const REF_GAP = HAS_TARGET ? 10 : 0;

    const chartL = PAD_L + REF_W + REF_GAP;
    const chartR = cw - PAD_R;
    const chartT = areaY + PAD_T;
    const chartB = areaY + areaH - PAD_B;
    const chartH = chartB - chartT;
    const barW   = (chartR - chartL) / n;

    const dataMax = Math.max(...values, HAS_TARGET ? target : 0, 1);
    let valToY, valToH;
    if (log_scale) {
      const logMax = Math.log1p(dataMax) || 1;
      valToH = (v) => chartH * Math.log1p(Math.max(0, v)) / logMax;
      valToY = (v) => chartB - valToH(v);
    } else {
      valToY = (v) => chartT + chartH * (1 - v / dataMax);
      valToH = (v) => chartH * v / dataMax;
    }

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    if (HAS_TARGET) {
      const refX = PAD_L; const refY = valToY(target);
      const refH = valToH(target); const rw = REF_W - 2;
      ctx.fillStyle = _acTheme().foundCellBg;
      ctx.fillRect(refX + 0.5, refY, rw - 1, refH);
      ctx.strokeStyle = "#44cc44"; ctx.lineWidth = 1.5;
      ctx.strokeRect(refX + 0.5, refY + 0.5, rw - 1, refH - 1);
      ctx.save(); ctx.strokeStyle = "rgba(68,204,68,0.35)";
      ctx.lineWidth = 1; ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(PAD_L + REF_W, refY);
      ctx.lineTo(chartR, refY); ctx.stroke(); ctx.restore();
      const rFs = Math.max(7, Math.min(10, REF_W * 0.4));
      ctx.fillStyle = _acTheme().foundCellText; ctx.font = `${rFs}px monospace`;
      ctx.textAlign = "center";
      ctx.fillText(String(target), refX + REF_W / 2 - 1, refY - 3);
    }

    const showLabel = barW >= 14;
    for (let i = 0; i < n; i++) {
      const x = chartL + i * barW;
      const y = valToY(values[i]); const h = valToH(values[i]);
      const isWatchman = (watchman_index === i);
      const hlColor    = highlights[String(i)];
      ctx.fillStyle = isWatchman ? "#cc6600" : hlColor ? hlColor : "#4472C4";
      ctx.fillRect(x + 0.5, y, barW - 1, Math.max(h, 1));
      if (showLabel) {
        const fs = Math.min(11, barW * 0.65);
        ctx.fillStyle = _acTheme().valueLabelColor; ctx.font = `${fs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(String(values[i]), x + barW / 2, y - 2);
      }
    }

    for (const fill of fills) {
      const from = Math.max(0, fill.from), to = Math.min(n - 1, fill.to);
      ctx.globalAlpha = 0.78; ctx.fillStyle = fill.color;
      ctx.fillRect(chartL + from * barW, chartT, (to - from + 1) * barW, chartH);
      ctx.globalAlpha = 1.0;
    }

    if (barW >= 14) {
      const iFs = Math.min(9, barW * 0.5);
      ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = `${iFs}px sans-serif`;
      ctx.textAlign = "center";
      for (let i = 0; i < n; i++) {
        ctx.fillText(String(i), chartL + i * barW + barW / 2, chartB + 12);
      }
    }

    if (pointer) {
      const { index, label: pLabel, color: pColor = "#cc00cc" } = pointer;
      const px   = chartL + index * barW + barW / 2;
      const tipY = valToY(values[index]) - 2;
      const topY = chartT - 4;
      ctx.strokeStyle = pColor; ctx.lineWidth = 1.5;
      if (topY + (pLabel ? 12 : 0) < tipY - 7) {
        ctx.beginPath(); ctx.moveTo(px, topY + (pLabel ? 12 : 0));
        ctx.lineTo(px, tipY - 7); ctx.stroke();
      }
      ctx.fillStyle = pColor; ctx.beginPath();
      ctx.moveTo(px, tipY); ctx.lineTo(px - 5, tipY - 7);
      ctx.lineTo(px + 5, tipY - 7); ctx.closePath(); ctx.fill();
      if (pLabel) {
        const lFs = Math.max(7, Math.min(10, barW * 0.6));
        ctx.fillStyle = pColor; ctx.font = `${lFs}px monospace`;
        ctx.textAlign = "center"; ctx.fillText(pLabel, px, topY + 10);
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // array1d_cells – 正方形セル配列
  // ════════════════════════════════════════════════════════════════════
  _drawArray1dCells(obj, areaY, areaH, areaX = 0, areaW = null) {
    const {
      values = [], label = "",
      highlights = {}, fills = [],
      pointer = null, watchman_index = null,
      target = null,
      unused_from = null,   // この添字以降は「確保済み・未使用」スロット
    } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = (areaW !== null) ? areaW : this.cw;

    const hasSize = (unused_from !== null);
    const PAD_T = 22; const PAD_B = hasSize ? 64 : 16;
    const PAD_L = 8;  const PAD_R = 8;

    // target セルを左端に配置
    const HAS_TARGET = target !== null;
    const TGT_W   = HAS_TARGET ? 44 : 0;
    const TGT_GAP = HAS_TARGET ? 10 : 0;

    const chartL = PAD_L + TGT_W + TGT_GAP;
    const chartR = cw - PAD_R;
    const chartT = areaY + PAD_T;
    const chartB = areaY + areaH - PAD_B;
    const chartH = chartB - chartT;

    // セルサイズ: 全 n 要素が必ず幅に収まるよう cellW を決定（下限なし）
    const cellW  = Math.min(56, (chartR - chartL) / n);
    // cellH: 最低 14px を確保（縮小時も帯として視認できるよう）
    const cellH  = Math.min(Math.max(cellW, 14), chartH * 0.65);
    const totalW = cellW * n;
    const startX = chartL + Math.max(0, ((chartR - chartL) - totalW) / 2);
    const cellY  = chartT + (chartH - cellH) / 2;

    ctx.save();
    if (areaX) ctx.translate(areaX, 0);

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    // target セル
    if (HAS_TARGET) {
      const tx = PAD_L;
      ctx.fillStyle = _acTheme().foundCellBg;
      ctx.fillRect(tx, cellY, TGT_W - 2, cellH);
      ctx.strokeStyle = "#44cc44"; ctx.lineWidth = 1.5;
      ctx.strokeRect(tx + 0.5, cellY + 0.5, TGT_W - 3, cellH - 1);

      const fs = Math.max(8, Math.min(13, (TGT_W - 4) * 0.4));
      ctx.fillStyle = _acTheme().foundCellText; ctx.font = `bold ${fs}px monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(target), tx + (TGT_W - 2) / 2, cellY + cellH / 2);
      ctx.textBaseline = "alphabetic";

      // 破線ガイド
      ctx.save(); ctx.strokeStyle = "rgba(68,204,68,0.35)";
      ctx.lineWidth = 1; ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(tx + TGT_W, cellY + cellH / 2);
      ctx.lineTo(chartR, cellY + cellH / 2); ctx.stroke();
      ctx.restore();
    }

    // セル描画
    const compact = cellW < 4;   // 極小セル: ボーダー・テキストなし
    for (let i = 0; i < n; i++) {
      const cx       = startX + i * cellW;
      const isWatchman = (watchman_index === i);
      const hlColor    = highlights[String(i)];
      const isUnused   = (unused_from !== null && i >= unused_from);
      const fw         = Math.max(cellW, 1);  // fillRect 用の安全な幅

      if (compact) {
        // ── compact モード: 塗りのみ ──────────────────────────────────
        if (isUnused) {
          ctx.fillStyle = _acTheme().cellEmptyBg;
        } else if (hlColor) {
          ctx.fillStyle = hlColor;
        } else if (isWatchman) {
          ctx.fillStyle = "#5a3000";
        } else {
          ctx.fillStyle = _acTheme().cellBg;
        }
        ctx.fillRect(cx, cellY, fw, cellH);

      } else if (isUnused) {
        // ── 確保済み・未使用スロット ─────────────────────────────────
        ctx.fillStyle = _acTheme().cellEmptyBg;
        ctx.fillRect(cx, cellY, cellW - 1, cellH);

        // ハッチング (斜め縞) — セルが十分大きい場合のみ
        if (cellW >= 8) {
          ctx.save();
          ctx.beginPath();
          ctx.rect(cx, cellY, cellW - 1, cellH);
          ctx.clip();
          ctx.strokeStyle = "rgba(80,120,180,0.22)";
          ctx.lineWidth = 1;
          const step = Math.max(5, cellW * 0.28);
          for (let d = -cellH; d < cellW + cellH; d += step) {
            ctx.beginPath();
            ctx.moveTo(cx + d,          cellY);
            ctx.lineTo(cx + d + cellH,  cellY + cellH);
            ctx.stroke();
          }
          ctx.restore();
        }

        // 破線ボーダー
        ctx.save();
        ctx.strokeStyle = "rgba(80,130,200,0.55)";
        ctx.lineWidth = 1;
        ctx.setLineDash(cellW >= 6 ? [3, 3] : []);
        ctx.strokeRect(cx + 0.5, cellY + 0.5, cellW - 2, cellH - 1);
        ctx.restore();

        // テキスト: em ダッシュ — セルが十分大きい場合のみ
        if (cellW >= 10) {
          const fs = Math.max(8, Math.min(14, cellW * 0.48, cellH * 0.48));
          ctx.fillStyle    = "rgba(80,130,200,0.60)";
          ctx.font         = `${fs}px monospace`;
          ctx.textAlign    = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("–", cx + cellW / 2, cellY + cellH / 2);
          ctx.textBaseline = "alphabetic";
        }

      } else {
        // ── 通常セル ─────────────────────────────────────────────────
        if (isWatchman) {
          ctx.fillStyle = "#3d2000";
          ctx.fillRect(cx, cellY, cellW - 1, cellH);
        } else if (hlColor) {
          ctx.fillStyle = _acTheme().cellBg;
          ctx.fillRect(cx, cellY, cellW - 1, cellH);
          ctx.save(); ctx.globalAlpha = 0.65;
          ctx.fillStyle = hlColor;
          ctx.fillRect(cx, cellY, cellW - 1, cellH);
          ctx.restore();
        } else {
          ctx.fillStyle = _acTheme().cellBg;
          ctx.fillRect(cx, cellY, cellW - 1, cellH);
        }

        // ボーダー
        ctx.strokeStyle = isWatchman ? "#cc6600" : hlColor ? hlColor : "#336699";
        ctx.lineWidth   = isWatchman ? 2 : hlColor ? 1.5 : 1;
        ctx.strokeRect(cx + 0.5, cellY + 0.5, cellW - 2, cellH - 1);

        // 値ラベル — セルが十分大きい場合のみ
        if (cellW >= 10) {
          const fs = Math.max(8, Math.min(14, cellW * 0.48, cellH * 0.48));
          ctx.fillStyle    = _acTheme().cellText;
          ctx.font         = `${fs}px monospace`;
          ctx.textAlign    = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(values[i]), cx + cellW / 2, cellY + cellH / 2);
          ctx.textBaseline = "alphabetic";
        }
      }

      // インデックスラベル (下) — 使用済み・未使用問わず表示
      if (cellW >= 14) {
        const iFs = Math.max(7, Math.min(9, cellW * 0.38));
        ctx.fillStyle = isUnused
          ? "rgba(80,130,200,0.45)"
          : _acTheme().indexLabelColor;
        ctx.font = `${iFs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(String(i), cx + cellW / 2, cellY + cellH + 12);
      }
    }

    // size / capacity プログレスバー（vector capacity アニメーション用）
    if (hasSize && n > 0) {
      const size     = unused_from;
      const capacity = n;
      const usedW    = size * cellW;
      const capW     = capacity * cellW;
      const barH     = 7;
      const barY     = cellY + cellH + 20;   // インデックスラベル(+12)の下
      const textY    = barY + barH + 12;

      // capacity バー（背景・暗め）
      ctx.fillStyle = "rgba(60,100,170,0.22)";
      ctx.fillRect(startX, barY, capW - 1, barH);
      ctx.strokeStyle = "rgba(80,130,200,0.4)";
      ctx.lineWidth = 1; ctx.setLineDash([]);
      ctx.strokeRect(startX + 0.5, barY + 0.5, capW - 2, barH - 1);

      // size バー（使用済み・緑）
      if (usedW > 0) {
        ctx.fillStyle = "#3ecf88";
        ctx.fillRect(startX, barY, usedW - 1, barH);
      }

      // 境界の縦線
      if (size > 0 && size < capacity) {
        ctx.strokeStyle = "#3ecf88";
        ctx.lineWidth = 2; ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(startX + usedW, barY - 1);
        ctx.lineTo(startX + usedW, barY + barH + 1);
        ctx.stroke();
      }
      ctx.setLineDash([]);

      // ラベルを描画（バー幅に応じて配置を変える）
      const sizeStr = `size = ${size}`;
      const capStr  = `capacity = ${capacity}`;
      ctx.font = "bold 13px sans-serif";
      const sizeW = ctx.measureText(sizeStr).width;
      ctx.font = "12px sans-serif";
      const capW2 = ctx.measureText(capStr).width;

      if (capW >= sizeW + capW2 + 16) {
        // 幅が十分: 左右に分けて表示
        ctx.font = "bold 13px sans-serif";
        ctx.fillStyle = "#3ecf88";
        ctx.textAlign = "left";
        ctx.fillText(sizeStr, startX, textY);
        ctx.font = "12px sans-serif";
        ctx.fillStyle = "rgba(100,160,220,0.85)";
        ctx.textAlign = "right";
        ctx.fillText(capStr, startX + capW, textY);
      } else {
        // 幅が狭い: 中央に「size=N  /  cap=M」をまとめて表示
        ctx.font = "bold 12px sans-serif";
        ctx.fillStyle = "#3ecf88";
        ctx.textAlign = "left";
        ctx.fillText(`size=${size}`, startX, textY);
        ctx.font = "12px sans-serif";
        ctx.fillStyle = "rgba(100,160,220,0.85)";
        ctx.textAlign = "right";
        ctx.fillText(`cap=${capacity}`, startX + capW, textY);
      }
    }

    // フィル (除外領域)
    for (const fill of fills) {
      const from = Math.max(0, fill.from), to = Math.min(n - 1, fill.to);
      ctx.save(); ctx.globalAlpha = 0.55;
      ctx.fillStyle = fill.color;
      ctx.fillRect(startX + from * cellW, cellY,
                   (to - from + 1) * cellW, cellH);
      ctx.restore();
    }

    // ポインタ矢印
    if (pointer) {
      const { index, label: pLabel, color: pColor = "#cc00cc" } = pointer;
      const px   = startX + index * cellW + cellW / 2;
      const tipY = cellY - 2;
      const topY = chartT - 4;
      ctx.strokeStyle = pColor; ctx.lineWidth = 1.5;
      if (topY + (pLabel ? 12 : 0) < tipY - 7) {
        ctx.beginPath(); ctx.moveTo(px, topY + (pLabel ? 12 : 0));
        ctx.lineTo(px, tipY - 7); ctx.stroke();
      }
      ctx.fillStyle = pColor; ctx.beginPath();
      ctx.moveTo(px, tipY); ctx.lineTo(px - 5, tipY - 7);
      ctx.lineTo(px + 5, tipY - 7); ctx.closePath(); ctx.fill();
      if (pLabel) {
        const lFs = Math.max(7, Math.min(10, cellW * 0.5));
        ctx.fillStyle = pColor; ctx.font = `${lFs}px monospace`;
        ctx.textAlign = "center"; ctx.fillText(pLabel, px, topY + 10);
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // heap_tree – ヒープ二分木
  // ════════════════════════════════════════════════════════════════════
  _drawHeapTree(obj, areaY, areaH) {
    const { values = [], heap_size = 0, highlights = {}, label = "",
            confirmed_min = 0 } = obj;
    const N = values.length;
    if (N === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 16;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD + (label ? 14 : 4);
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // 木の深さ
    const levels = N > 0 ? Math.floor(Math.log2(N)) + 1 : 1;
    const levelH = chartH / levels;
    const nodeR  = Math.max(8, Math.min(20, levelH * 0.32,
                             chartW / Math.pow(2, Math.ceil(levels / 2)) * 0.45));

    // ノード座標
    function nodePos(i) {
      const level       = Math.floor(Math.log2(i + 1));
      const posInLevel  = i - (Math.pow(2, level) - 1);
      const nodesInLvl  = Math.pow(2, level);
      return {
        x: chartL + chartW * (posInLevel + 0.5) / nodesInLvl,
        y: chartT + levelH * (level + 0.5),
      };
    }

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD, areaY + 14);
    }

    // 辺 (heap_size 以内。ghost 辺は暗く描画)
    for (let i = 1; i < heap_size; i++) {
      const isGhostEdge = i < confirmed_min;
      ctx.strokeStyle = isGhostEdge ? _acTheme().dimEdge : _acTheme().edgeColor;
      ctx.lineWidth   = isGhostEdge ? 0.5 : 1;
      const parent = Math.floor((i - 1) / 2);
      const p1 = nodePos(parent), p2 = nodePos(i);
      ctx.beginPath(); ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y); ctx.stroke();
    }

    // ノード描画 (heap_size 以内)
    const fs = Math.max(6, Math.min(12, nodeR * 0.72));
    for (let i = 0; i < heap_size; i++) {
      const isGhost = i < confirmed_min;
      const pos     = nodePos(i);
      const hlColor = highlights[String(i)];

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeR, 0, Math.PI * 2);

      if (isGhost) {
        // 未処理ノード: 非常に暗い色で描画 (存在はほのめかす)
        ctx.fillStyle   = _acTheme().ghostFill;
        ctx.fill();
        ctx.strokeStyle = _acTheme().ghostStroke;
        ctx.lineWidth   = 0.8;
        ctx.stroke();
        ctx.fillStyle    = _acTheme().ghostText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";
      } else {
        // 確定済みノード: 通常描画
        if (hlColor) {
          ctx.fillStyle = _acTheme().nodeBg; ctx.fill();
          ctx.save(); ctx.globalAlpha = 0.4;
          ctx.fillStyle = hlColor; ctx.fill(); ctx.restore();
          ctx.strokeStyle = hlColor; ctx.lineWidth = 2;
        } else {
          ctx.fillStyle = _acTheme().cellBg; ctx.fill();
          ctx.strokeStyle = "#4472C4"; ctx.lineWidth = 1.5;
        }
        ctx.stroke();

        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";

        // インデックス (右下小)
        if (nodeR >= 12) {
          const iFs = Math.max(6, Math.min(8, nodeR * 0.42));
          ctx.fillStyle = _acTheme().indexLabelColor;
          ctx.font      = `${iFs}px sans-serif`;
          ctx.textAlign = "center";
          ctx.fillText(String(i), pos.x + nodeR * 0.7, pos.y + nodeR + iFs);
        }
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // bucket_rows – バケツ行 / 動的キュー
  // ════════════════════════════════════════════════════════════════════
  _drawBucketRows(obj, areaY, areaH) {
    const {
      num_buckets = 0, buckets = [], bucket_colors = [],
      bucket_labels = [], label = "", active_bucket = null,
      direction = "rows",   // "rows" | "columns"
    } = obj;
    if (num_buckets === 0) return;

    if (direction === "columns") {
      this._drawBucketColumns(obj, areaY, areaH);
      return;
    }

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T   = label ? 18 : 6;
    const PAD_B   = 4;
    const PAD_L   = 6;
    const LBL_W   = 24;
    const SEP_W   = 4;

    const totalH  = areaH - PAD_T - PAD_B;
    const rowH    = Math.max(14, Math.min(36, totalH / num_buckets));
    const cellW   = Math.min(rowH * 1.1, 42);
    const cellPad = 2;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_L, areaY + 14);
    }

    for (let b = 0; b < num_buckets; b++) {
      const rowY    = areaY + PAD_T + b * rowH;
      const cells   = buckets[b] || [];
      const color   = bucket_colors[b % bucket_colors.length] || "#4472C4";
      const isActive = active_bucket === b;
      const lblText = bucket_labels[b] !== undefined ? String(bucket_labels[b]) : String(b);

      ctx.fillStyle = isActive ? "#ffffff" : color;
      ctx.font      = `${Math.max(8, Math.min(11, rowH * 0.5))}px monospace`;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(lblText, PAD_L + LBL_W, rowY + rowH / 2);
      ctx.textBaseline = "alphabetic";

      ctx.strokeStyle = isActive ? "#ffffff" : color;
      ctx.lineWidth   = isActive ? 1.5 : 1;
      ctx.beginPath();
      ctx.moveTo(PAD_L + LBL_W + SEP_W, rowY + 3);
      ctx.lineTo(PAD_L + LBL_W + SEP_W, rowY + rowH - 3);
      ctx.stroke();

      for (let c = 0; c < cells.length; c++) {
        const cx     = PAD_L + LBL_W + SEP_W + cellPad + c * (cellW + cellPad);
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = _acTheme().nodeBg;
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.save(); ctx.globalAlpha = isLast ? 0.5 : 0.22;
        ctx.fillStyle = color;
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.restore();

        ctx.strokeStyle = isLast ? _acTheme().cellText : color;
        ctx.lineWidth   = isLast ? 1.5 : 1;
        ctx.strokeRect(cx + 0.5, rowY + 2.5, cellW - 1, rowH - 5);

        const fs = Math.max(7, Math.min(12, cellW * 0.44, (rowH - 4) * 0.55));
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[c]), cx + cellW / 2, rowY + rowH / 2);
        ctx.textBaseline = "alphabetic";
      }

      if (cells.length === 0) {
        ctx.strokeStyle = color; ctx.globalAlpha = 0.2; ctx.lineWidth = 0.5;
        const cx = PAD_L + LBL_W + SEP_W + cellPad;
        ctx.strokeRect(cx + 0.5, rowY + 2.5, cellW - 1, rowH - 5);
        ctx.globalAlpha = 1;
      }
    }

    ctx.restore();
  }

  // ── bucket_rows カラムレイアウト (1バケツ = 1列, ラベルが上・セルは下へ伸びる) ──
  _drawBucketColumns(obj, areaY, areaH) {
    const {
      num_buckets = 0, buckets = [], bucket_colors = [],
      bucket_labels = [], label = "", active_bucket = null,
    } = obj;

    const ctx    = this.ctx;
    const cw     = this.cw;
    // テキストオーバーレイ（最大3行 × 18 + 12 ≈ 66px）の下からコンテンツを開始する
    const TEXT_OVERLAY_H = 66;
    const PAD_T  = TEXT_OVERLAY_H;   // オーバーレイ分を避けるパディング
    const LBL_H  = 16;               // 各列ラベル行の高さ
    const PAD_B  = 4;
    const PAD_LR = 4;

    const usableW  = cw - PAD_LR * 2;
    const colW     = usableW / num_buckets;
    const cellPad  = 2;
    const cellW    = Math.max(8, colW - cellPad * 2);
    const usableH  = areaH - PAD_T - LBL_H - PAD_B;
    const maxItems = Math.max(1, ...buckets.map(b => b.length));
    const cellH    = Math.max(10, Math.min(colW * 0.9, usableH / Math.max(4, maxItems)));
    const fs       = Math.max(7, Math.min(11, cellH * 0.55, cellW * 0.5));

    // セル開始 Y（ラベル行のすぐ下）
    const cellStartY = areaY + PAD_T + LBL_H;

    ctx.save();

    // セクションラベル（オーバーレイ直下に配置）
    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_LR, areaY + PAD_T - 4);
    }

    for (let b = 0; b < num_buckets; b++) {
      const colX     = PAD_LR + b * colW + cellPad;
      const cells    = buckets[b] || [];
      const color    = bucket_colors[b % bucket_colors.length] || "#4472C4";
      const isActive = active_bucket === b;
      const lblText  = bucket_labels[b] !== undefined ? String(bucket_labels[b]) : String(b);

      // 列ラベル（上端）
      const lblY = areaY + PAD_T + LBL_H - 4;
      ctx.fillStyle    = isActive ? "#ffffff" : color;
      ctx.font         = `${Math.max(8, Math.min(11, colW * 0.38))}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(lblText, colX + cellW / 2, lblY);

      // 区切り線（ラベルの下）
      ctx.strokeStyle = isActive ? "#ffffff" : color;
      ctx.lineWidth   = isActive ? 1.2 : 0.8;
      ctx.globalAlpha = isActive ? 1.0 : 0.6;
      ctx.beginPath();
      ctx.moveTo(colX,          cellStartY);
      ctx.lineTo(colX + cellW,  cellStartY);
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // セル（上から下へ積む: index 0 が一番上）
      for (let c = 0; c < cells.length; c++) {
        const cellY  = cellStartY + c * cellH + cellPad;
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = _acTheme().nodeBg;
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.save();
        ctx.globalAlpha = isLast ? 0.55 : 0.25;
        ctx.fillStyle   = color;
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.restore();

        ctx.strokeStyle = isLast ? _acTheme().cellText : color;
        ctx.lineWidth   = isLast ? 1.2 : 0.6;
        ctx.strokeRect(colX + 0.5, cellY + 0.5, cellW - 1, cellH - cellPad - 1);

        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[c]), colX + cellW / 2, cellY + (cellH - cellPad) / 2);
        ctx.textBaseline = "alphabetic";
      }

      // 空列（細い輪郭のみ）
      if (cells.length === 0) {
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.15;
        ctx.lineWidth   = 0.5;
        ctx.strokeRect(colX + 0.5, cellStartY + cellPad + 0.5, cellW - 1, cellH - cellPad - 1);
        ctx.globalAlpha = 1.0;
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // tape – 無端テープ
  // ════════════════════════════════════════════════════════════════════
  _drawTape(obj, areaY, areaH) {
    const { cells = [], head = 0, label = "", color = "#4472C4" } = obj;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 6;
    const LBL_W  = 64;
    // セルサイズを array1d_cells と揃える (小さめに抑える)
    const cellH  = Math.max(18, Math.min(28, areaH - PAD * 2 - 16));
    const cellW  = cellH;
    const tapeY  = areaY + (areaH - cellH - 14) / 2;    // -14 = 矢印スペース
    const availW = cw - PAD * 2 - LBL_W;
    const nVis   = Math.max(3, Math.floor(availW / cellW));
    const half   = Math.floor(nVis / 2);
    const startX = PAD + LBL_W + half * cellW;

    ctx.save();

    // ラベル
    ctx.fillStyle    = color;
    ctx.font         = "11px monospace";
    ctx.textAlign    = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(label, PAD, tapeY + cellH / 2);
    ctx.textBaseline = "alphabetic";

    // 端のハッシュ記号は bright テーマで目立つため廃止（範囲外セルが不可視なので不要）

    // セル
    for (let vi = 0; vi < nVis; vi++) {
      const idx    = head - half + vi;
      const cx     = PAD + LBL_W + vi * cellW;
      const inData = idx >= 0 && idx < cells.length;
      const isHead = (idx === head);

      if (!inData) {
        // データ範囲外セル → 背景色で完全に塗りつぶして不可視にする
        ctx.fillStyle = _acTheme().canvasBg;
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
      } else {
        // データセル
        ctx.fillStyle = _acTheme().cellBg;
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
        if (isHead) {
          ctx.save(); ctx.globalAlpha = 0.45;
          ctx.fillStyle = color;
          ctx.fillRect(cx, tapeY, cellW - 1, cellH);
          ctx.restore();
        }
        ctx.strokeStyle = isHead ? color : _acTheme().edgeColor;
        ctx.lineWidth   = isHead ? 2 : 0.8;
        ctx.strokeRect(cx + 0.5, tapeY + 0.5, cellW - 2, cellH - 1);

        const fs = Math.max(8, Math.min(13, cellW * 0.42, cellH * 0.46));
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[idx]), cx + cellW / 2, tapeY + cellH / 2);
        ctx.textBaseline = "alphabetic";
      }
    }

    // ヘッド矢印
    const hx = PAD + LBL_W + half * cellW + cellW / 2;
    ctx.fillStyle = color; ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("▲", hx, tapeY + cellH + 13);

    ctx.restore();
  }

  _drawTapeHashmark(ctx, x, tapeY, w, cellH) {
    ctx.save();
    ctx.fillStyle = _acTheme().cellEmptyBg;
    ctx.fillRect(x, tapeY, w - 1, cellH);
    ctx.strokeStyle = _acTheme().dimEdge; ctx.lineWidth = 0.5;
    ctx.strokeRect(x + 0.5, tapeY + 0.5, w - 2, cellH - 1);
    ctx.setLineDash([3, 4]);
    for (let hx = x + 3; hx < x + w - 2; hx += 5) {
      ctx.beginPath(); ctx.moveTo(hx, tapeY + 2);
      ctx.lineTo(hx - (cellH - 4) * 0.5, tapeY + cellH - 2); ctx.stroke();
    }
    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // fib_tree – フィボナッチ再帰木
  // ════════════════════════════════════════════════════════════════════
  _drawFibTree(obj, areaY, areaH) {
    const { root } = obj;
    if (!root) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 20;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD;
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // 深さ・最大幅を計算
    function depth(node) {
      if (!node) return 0;
      return 1 + Math.max(depth(node.left), depth(node.right));
    }
    function leafCount(node) {
      if (!node) return 0;
      if (!node.left && !node.right) return 1;
      return (node.left ? leafCount(node.left) : 0) +
             (node.right ? leafCount(node.right) : 0);
    }

    const d   = depth(root);
    const lc  = Math.max(1, leafCount(root));
    if (d === 0) return;

    const levelH = chartH / d;
    const nodeR  = Math.max(8, Math.min(18, levelH * 0.3,
                             chartW / (lc * 2.2)));

    // ノード位置を計算 (葉の位置から再帰的に決定)
    let leafIdx = 0;
    function assignPos(node, depth_) {
      if (!node) return;
      const y = chartT + levelH * (depth_ + 0.5);
      if (!node.left && !node.right) {
        // 葉ノード: 左から順に等間隔
        node._x = chartL + chartW * (leafIdx + 0.5) / lc;
        node._y = y;
        leafIdx++;
      } else {
        assignPos(node.left,  depth_ + 1);
        assignPos(node.right, depth_ + 1);
        const lx = node.left  ? node.left._x  : null;
        const rx = node.right ? node.right._x : null;
        node._x = lx !== null && rx !== null ? (lx + rx) / 2
                : lx !== null ? lx : rx;
        node._y = y;
      }
    }
    leafIdx = 0;
    assignPos(root, 0);

    ctx.save();

    // 辺
    function drawEdges(node) {
      if (!node) return;
      if (node.left) {
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.left._x, node.left._y);
        ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(node.left);
      }
      if (node.right) {
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.right._x, node.right._y);
        ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(node.right);
      }
    }
    drawEdges(root);

    // ノード
    function drawNodes(node) {
      if (!node) return;
      const color = node.color || "#4472C4";

      ctx.beginPath();
      ctx.arc(node._x, node._y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = _acTheme().nodeBg; ctx.fill();
      ctx.save(); ctx.globalAlpha = 0.4;
      ctx.fillStyle = color; ctx.fill(); ctx.restore();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.stroke();

      // ラベル: f(n) / =v
      const fs = Math.max(6, Math.min(11, nodeR * 0.68));
      ctx.fillStyle    = "#ccddee";
      ctx.font         = `${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";

      const hasVal = node.value !== null && node.value !== undefined;
      if (hasVal) {
        ctx.fillText(`f(${node.n})`, node._x, node._y - fs * 0.55);
        ctx.fillStyle = color;
        ctx.fillText(`=${node.value}`, node._x, node._y + fs * 0.55);
      } else {
        ctx.fillText(`f(${node.n})`, node._x, node._y);
      }
      ctx.textBaseline = "alphabetic";

      // メモ化ノード: 右上にバッジ
      if (node.memo) {
        const bR = Math.max(4, nodeR * 0.35);
        ctx.beginPath();
        ctx.arc(node._x + nodeR * 0.72, node._y - nodeR * 0.72, bR, 0, Math.PI * 2);
        ctx.fillStyle = "#44aacc"; ctx.fill();
        ctx.strokeStyle = "#fff"; ctx.lineWidth = 0.8; ctx.stroke();
        ctx.fillStyle = "#fff"; ctx.font = `bold ${Math.max(5, bR * 0.9)}px sans-serif`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText("M", node._x + nodeR * 0.72, node._y - nodeR * 0.72);
        ctx.textBaseline = "alphabetic";
      }

      drawNodes(node.left);
      drawNodes(node.right);
    }
    drawNodes(root);

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // staircase – 階段状テキスト (階乗再帰)
  // ════════════════════════════════════════════════════════════════════
  _drawStaircase(obj, areaY, areaH) {
    const { rows = [], label = "" } = obj;
    if (rows.length === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T   = label ? 20 : 6;
    const PAD_L   = 10;
    const PAD_R   = 8;
    const maxDepth = rows.reduce((m, r) => Math.max(m, r.depth || 0), 0);
    const INDENT   = Math.min(18, maxDepth > 0 ? (cw * 0.3) / maxDepth : 18);
    const rowH     = Math.max(12, Math.min(22, (areaH - PAD_T - 4) / Math.max(rows.length, 1)));
    const fs       = Math.max(9, Math.min(13, rowH * 0.68));

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_L, areaY + 14);
    }

    for (let i = 0; i < rows.length; i++) {
      const { text, depth = 0, color = "#aaa" } = rows[i];
      const rowY = areaY + PAD_T + i * rowH;
      const rowX = PAD_L + depth * INDENT;
      const isActive = (color === "yellow" || color === "#ffff00");

      // アクティブ行の背景ハイライト
      if (isActive) {
        ctx.save(); ctx.globalAlpha = 0.12;
        ctx.fillStyle = "#ffff00";
        ctx.fillRect(rowX - 3, rowY, cw - rowX - PAD_R, rowH);
        ctx.restore();
      }

      // 接続線 (前の行から indent が増えた場合)
      if (i > 0 && rows[i].depth > rows[i - 1].depth) {
        const prevX = PAD_L + rows[i - 1].depth * INDENT + 3;
        const prevY = areaY + PAD_T + (i - 1) * rowH + rowH * 0.75;
        ctx.strokeStyle = _acTheme().connectorColor; ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(prevX, prevY);
        ctx.lineTo(prevX, rowY + rowH * 0.5);
        ctx.lineTo(rowX - 1, rowY + rowH * 0.5);
        ctx.stroke();
        // 矢印
        ctx.fillStyle = _acTheme().connectorColor;
        ctx.beginPath();
        ctx.moveTo(rowX - 1, rowY + rowH * 0.5);
        ctx.lineTo(rowX - 5, rowY + rowH * 0.5 - 3);
        ctx.lineTo(rowX - 5, rowY + rowH * 0.5 + 3);
        ctx.closePath(); ctx.fill();
      }

      // テキスト
      ctx.fillStyle = color;
      ctx.font      = `${fs}px monospace`;
      ctx.textAlign = "left";
      ctx.fillText(text, rowX + 4, rowY + rowH * 0.78);
    }

    ctx.restore();
  }

  // ── プレビュー描画 ────────────────────────────────────────────────
  /**
   * @param {number}   numItems
   * @param {boolean}  sorted
   * @param {number|null} forcedTarget
   * @param {Array|null}  sharedValues
   * @param {boolean}  showTarget
   * @param {string}   mode  "bars" | "cells"
   */
  drawPreview(numItems, sorted = false, forcedTarget = null,
              sharedValues = null, showTarget = true, mode = "bars") {
    const maxVal = numItems >= 200 ? 999 : 99;
    let values = sharedValues
      ? [...sharedValues]
      : Array.from({ length: numItems }, () => Math.floor(Math.random() * maxVal) + 1);
    if (sorted) values.sort((a, b) => a - b);

    const target = showTarget
      ? (forcedTarget !== null ? forcedTarget : values[Math.floor(Math.random() * numItems)])
      : null;

    const type = (mode === "cells") ? "array1d_cells" : "array1d";
    this.draw({
      objects: [{
        id:             "preview",
        type,
        values,
        label:          "Data",
        highlights:     {},
        fills:          [],
        pointer:        null,
        watchman_index: null,
        target,
        log_scale:      false,
        weight:         1,
      }],
      texts:    [],
      finished: false,
    });
    return { values, target };
  }

  // ════════════════════════════════════════════════════════════════════
  // linked_list – 連結リスト（ノード＋矢印）
  // ════════════════════════════════════════════════════════════════════
  _drawLinkedList(obj, areaY, areaH, areaX = 0, areaW = null) {
    if (obj.is_vertical) { this._drawLinkedListV(obj, areaY, areaH, areaX, areaW); return; }
    const {
      nodes      = [],
      label      = "",
      highlights = {},
      is_doubly  = false,
      ptr_labels = ["first", "last"],
      ptr_colors = ["#44cc66", "#4499dd"],
    } = obj;
    const n   = nodes.length;
    const ctx = this.ctx;
    const cw  = this.cw;

    // ── レイアウト定数 ──────────────────────────────────────────────
    const PAD_L   = 14;
    const PAD_R   = 14;
    const PAD_T   = 44;   // ラベル(12px) + バッジ(13px) + 余白
    const PAD_B   = 52;   // 底部テキストオーバーレイ(≈48px) を避ける

    const availW  = cw - PAD_L - PAD_R;
    const availH  = areaH - PAD_T - PAD_B;

    // ノードと矢印のサイズを利用可能幅から算出
    // 片方向: n ノード + n 矢印 (最後は→NULL)
    // 双方向: n ノード + (n-1) 矢印
    const arrowSlots = is_doubly ? Math.max(n - 1, 0) : n;
    const ARROW_W = Math.max(18, Math.min(32, availW * 0.12));
    const NULL_W  = is_doubly ? 0 : Math.max(24, ARROW_W);
    const NODE_W  = n === 0 ? 60
                            : Math.max(32, Math.min(64,
                                (availW - arrowSlots * ARROW_W - NULL_W) / n));
    const NODE_H  = Math.max(28, Math.min(46, availH * 0.62));
    const CORNER  = 5;

    const totalW  = n === 0 ? 0
                            : n * NODE_W + arrowSlots * ARROW_W + NULL_W;
    const startX  = PAD_L + Math.max(0, (availW - totalW) / 2);
    const nodeY   = areaY + PAD_T + (availH - NODE_H) / 2;
    const midY    = nodeY + NODE_H / 2;

    ctx.save();

    // ラベル
    if (label) {
      ctx.fillStyle = "#6a8faf";
      ctx.font      = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    // 空リスト表示
    if (n === 0) {
      ctx.fillStyle = _acTheme().emptyText;
      ctx.font      = "12px monospace";
      ctx.textAlign = "center";
      ctx.fillText("(空)", cw / 2, areaY + areaH / 2);
      ctx.restore();
      return;
    }

    // ── 各ノードを描画 ──────────────────────────────────────────────
    const nodeXs = [];
    for (let i = 0; i < n; i++) {
      const slotsBefore = is_doubly ? i : i;
      const x = startX + i * NODE_W + slotsBefore * ARROW_W;
      nodeXs.push(x);

      const hlColor = highlights[String(i)];

      // ノード背景
      ctx.fillStyle = _acTheme().cellBg;
      this._rrect(ctx, x, nodeY, NODE_W, NODE_H, CORNER);
      ctx.fill();

      // ノード枠
      ctx.strokeStyle = hlColor || "#4472C4";
      ctx.lineWidth   = hlColor ? 2.5 : 1.5;
      this._rrect(ctx, x, nodeY, NODE_W, NODE_H, CORNER);
      ctx.stroke();

      // ハイライト背景色
      if (hlColor) {
        ctx.save();
        ctx.globalAlpha = 0.22;
        ctx.fillStyle   = hlColor;
        this._rrect(ctx, x, nodeY, NODE_W, NODE_H, CORNER);
        ctx.fill();
        ctx.restore();
      }

      // 値テキスト
      const fs = Math.max(10, Math.min(15, NODE_W * 0.32));
      ctx.fillStyle    = hlColor || _acTheme().cellValueColor;
      ctx.font         = `bold ${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(nodes[i]), x + NODE_W / 2, midY);
      ctx.textBaseline = "alphabetic";

      // ── 矢印描画 ──────────────────────────────────────────────────
      if (i < n - 1) {
        const ax1 = x + NODE_W;
        const ax2 = ax1 + ARROW_W;
        ctx.strokeStyle = "#5577aa";
        ctx.lineWidth   = 1.5;
        if (is_doubly) {
          this._arrow(ctx, ax1, midY - 4, ax2, midY - 4);   // →
          this._arrow(ctx, ax2, midY + 4, ax1, midY + 4);   // ←
        } else {
          this._arrow(ctx, ax1, midY, ax2, midY);            // →
        }
      }
    }

    // 片方向: 末尾 → NULL
    if (!is_doubly) {
      const lastX = nodeXs[n - 1];
      const ax1   = lastX + NODE_W;
      const ax2   = ax1 + ARROW_W;
      ctx.strokeStyle = _acTheme().connectorColor;
      ctx.lineWidth   = 1.5;
      ctx.beginPath(); ctx.moveTo(ax1, midY); ctx.lineTo(ax2 - 8, midY); ctx.stroke();
      ctx.fillStyle    = _acTheme().connectorColor;
      ctx.font         = "bold 10px monospace";
      ctx.textAlign    = "left";
      ctx.textBaseline = "middle";
      ctx.fillText("null", ax2 - 8, midY);
      ctx.textBaseline = "alphabetic";
    }

    // ── first / last ポインタ（ノード上端に密着バッジ） ──────────────
    const BADGE_H  = 13;   // バッジの高さ
    const GAP      = 10;   // バッジ下端～ノード上端の隙間
    const TRI_H    = 5;    // ノード側への小三角の高さ
    // バッジ下端 = ノード上端 - GAP
    const badgeBot = nodeY - GAP;
    const badgeTop = badgeBot - BADGE_H;

    // offsetX: 同一ノードに2ポインタが重なるとき左右にずらすピクセル
    const drawPtr = (nodeIdx, color, lbl, offsetX = 0) => {
      const px = nodeXs[nodeIdx] + NODE_W / 2 + offsetX;
      ctx.font = "bold 10px monospace";
      const tw = ctx.measureText(lbl).width;
      const bw = tw + 8, br = 3;
      // バッジ背景
      ctx.save(); ctx.globalAlpha = 0.92; ctx.fillStyle = color;
      this._rrect(ctx, px - bw/2, badgeTop, bw, BADGE_H, br); ctx.fill();
      ctx.restore();
      // バッジテキスト
      ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(lbl, px, badgeTop + BADGE_H / 2);
      ctx.textBaseline = "alphabetic";
      // 縦線（バッジ下端→ノード上端）
      ctx.strokeStyle = color; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(px, badgeBot); ctx.lineTo(px, nodeY); ctx.stroke();
      // ノードへの小三角（下向き）
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(px - 4, nodeY);
      ctx.lineTo(px + 4, nodeY);
      ctx.lineTo(px,     nodeY + TRI_H);
      ctx.closePath(); ctx.fill();
    };

    // front と back が同一ノードを指す場合（n=1）は左右にずらして両方表示
    const sameNode = (n === 1);
    const shift = sameNode ? Math.min(NODE_W * 0.22, 12) : 0;
    drawPtr(0,     ptr_colors[0], ptr_labels[0], sameNode ? -shift : 0);
    drawPtr(n - 1, ptr_colors[1], ptr_labels[1], sameNode ? +shift : 0);

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // linked_list (vertical) – 縦方向連結リスト（BOTTOM 固定・上積み）
  // nodes[0] = top（上）、nodes[n-1] = bottom（下・固定）
  // ════════════════════════════════════════════════════════════════════
  _drawLinkedListV(obj, areaY, areaH, areaX = 0, areaW = null) {
    const {
      nodes      = [],
      label      = "",
      highlights = {},
      is_doubly  = false,
      ptr_labels = ["top", "bottom"],
      ptr_colors = ["#44cc66", "#4499dd"],
    } = obj;
    const n   = nodes.length;
    const ctx = this.ctx;
    const cw  = (areaW !== null) ? areaW : this.cw;
    const CORNER  = 5;

    // ── レイアウト定数 ──────────────────────────────────────────────
    const PTR_W   = 58;    // 左側ポインタ幅
    const PAD_R   = 14;
    const PAD_BOT = 24;    // BOTTOM バッジ用
    const PAD_TOP = label ? 20 : 10;
    const NODE_W  = Math.max(50, Math.min(88, cw - PTR_W - PAD_R - 8));
    const nodeX   = PTR_W + (cw - PTR_W - PAD_R - NODE_W) / 2;
    const midX    = nodeX + NODE_W / 2;

    // BOTTOM ラインは常に固定 Y
    const bottomLineY = areaY + areaH - PAD_BOT;

    // ノード数に応じて NODE_H / ARROW_H を動的に算出
    const availForNodes = bottomLineY - (areaY + PAD_TOP);
    const maxNodes = Math.max(n, 1);
    const NULL_H  = 14;
    // n ノード + (n-1 or n) 矢印 + null の高さの合計が availForNodes に収まるように
    const arrowSlots = is_doubly ? Math.max(n - 1, 0) : n;
    const rawNodeH  = (availForNodes - NULL_H - arrowSlots * 14) / maxNodes;
    const NODE_H  = Math.max(18, Math.min(36, rawNodeH));
    const ARROW_H = Math.max(10, Math.min(18, (availForNodes - maxNodes * NODE_H - NULL_H) / Math.max(arrowSlots, 1)));

    ctx.save();
    if (areaX) ctx.translate(areaX, 0);

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, 6, areaY + 12);
    }

    // ── BOTTOM ライン（常に固定）────────────────────────────────────
    ctx.strokeStyle = ptr_colors[1] || "#4499dd"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(nodeX - 4, bottomLineY); ctx.lineTo(nodeX + NODE_W + 4, bottomLineY); ctx.stroke();
    // BOTTOM バッジ
    const botLbl  = ptr_labels[1] || "bottom";
    ctx.font      = "bold 10px monospace";
    const botTw   = ctx.measureText(botLbl).width;
    const botBw   = botTw + 10, botBh = 14;
    ctx.save(); ctx.globalAlpha = 0.85;
    ctx.fillStyle = ptr_colors[1] || "#4499dd";
    this._rrect(ctx, midX - botBw/2, bottomLineY + 4, botBw, botBh, 3); ctx.fill();
    ctx.restore();
    ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(botLbl, midX, bottomLineY + 4 + botBh/2);
    ctx.textBaseline = "alphabetic";

    if (n === 0) {
      ctx.fillStyle = _acTheme().emptyText; ctx.font = "12px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("(空)", midX, (areaY + PAD_TOP + bottomLineY) / 2);
      ctx.textBaseline = "alphabetic";
      ctx.restore(); return;
    }

    // ── ノード Y 座標（BOTTOM から上向きに積み上げ）──────────────────
    // nodes[n-1] = 最下段（BOTTOM ライン直上）
    // nodes[0]   = 最上段（top）
    // 片方向: nodes[n-1] の下に null → bottomLineY
    const nullY = bottomLineY - NULL_H;   // null ラベルの top Y
    const nodeYs = new Array(n);
    for (let i = n - 1; i >= 0; i--) {
      const fromBottom = n - 1 - i;       // 0 = 最下段
      nodeYs[i] = nullY - (fromBottom + 1) * NODE_H - fromBottom * ARROW_H;
    }

    // ── null ターミネータ ─────────────────────────────────────────
    if (!is_doubly) {
      const lastBottom = nodeYs[n - 1] + NODE_H;
      ctx.strokeStyle = _acTheme().connectorColor; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(midX, lastBottom); ctx.lineTo(midX, nullY); ctx.stroke();
      ctx.fillStyle = _acTheme().connectorColor; ctx.font = "bold 10px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("null", midX, nullY + NULL_H / 2);
      ctx.textBaseline = "alphabetic";
    }

    // ── 各ノード描画 ─────────────────────────────────────────────
    for (let i = 0; i < n; i++) {
      const ny      = nodeYs[i];
      const hlColor = highlights[String(i)];

      ctx.fillStyle = _acTheme().cellBg;
      this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.fill();
      if (hlColor) {
        ctx.save(); ctx.globalAlpha = 0.25; ctx.fillStyle = hlColor;
        this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.fill(); ctx.restore();
      }
      ctx.strokeStyle = hlColor || "#4472C4";
      ctx.lineWidth   = hlColor ? 2.5 : 1.5;
      this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.stroke();

      ctx.fillStyle = hlColor || _acTheme().cellValueColor;
      ctx.font = "bold 13px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(nodes[i]), midX, ny + NODE_H / 2);
      ctx.textBaseline = "alphabetic";

      // 下向き矢印（next ポインタ）
      if (i < n - 1) {
        const ay1 = ny + NODE_H, ay2 = nodeYs[i + 1];
        ctx.strokeStyle = "#5577aa"; ctx.lineWidth = 1.5;
        if (is_doubly) {
          this._arrow(ctx, midX - 5, ay1, midX - 5, ay2);
          this._arrow(ctx, midX + 5, ay2, midX + 5, ay1);
        } else {
          this._arrow(ctx, midX, ay1, midX, ay2);
        }
      }
    }

    // ── TOP バッジ（左サイドポインタ）────────────────────────────
    if (n > 0) {
      const topMidY = nodeYs[0] + NODE_H / 2;
      const ptrX2   = nodeX - 6;
      const ptrX1   = ptrX2 - 20;
      const topLbl  = ptr_labels[0] || "top";
      const topCol  = ptr_colors[0] || "#44cc66";

      // ポインタ矢印（← ノードを指す）
      ctx.strokeStyle = topCol; ctx.fillStyle = topCol; ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.moveTo(ptrX1, topMidY); ctx.lineTo(ptrX2, topMidY); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(ptrX2, topMidY);
      ctx.lineTo(ptrX2 - 8, topMidY - 4);
      ctx.lineTo(ptrX2 - 8, topMidY + 4);
      ctx.closePath(); ctx.fill();

      // TOP バッジ
      ctx.font = "bold 10px monospace";
      const tw = ctx.measureText(topLbl).width;
      const bw = tw + 10, bh = 14;
      ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = topCol;
      this._rrect(ctx, ptrX1 - bw - 2, topMidY - bh/2, bw, bh, 3); ctx.fill(); ctx.restore();
      ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(topLbl, ptrX1 - bw/2 - 2, topMidY);
      ctx.textBaseline = "alphabetic";
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // stack_v – 縦方向配列スタック（Bottom 固定・上に積む）
  // ════════════════════════════════════════════════════════════════════
  _drawStackV(obj, areaY, areaH, areaX = 0, areaW = null) {
    const { values = [], top = -1, label = "", highlights = {}, max_size, pad_bottom = 0 } = obj;
    const n   = (max_size !== undefined) ? max_size : values.length;
    const ctx = this.ctx;
    const cw  = (areaW !== null) ? areaW : this.cw;
    const ox  = areaX;   // x オフセット

    const PAD_IDX = 22;   // インデックス表示幅（左）
    const PAD_PTR = 46;   // top ポインタ幅（右）
    const PAD_T   = label ? 22 : 8;
    const PAD_B   = 20 + pad_bottom;   // BOTTOM ラベル + 追加余白

    const availH  = areaH - PAD_T - PAD_B;
    const cellH   = Math.max(14, Math.min(38, availH / Math.max(n, 1)));
    const cellW   = Math.max(36, Math.min(90, cw - PAD_IDX - PAD_PTR - 8));
    const cellX   = ox + PAD_IDX + (cw - PAD_IDX - PAD_PTR - cellW) / 2;
    const bottomY = areaY + areaH - PAD_B;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, ox + 4, areaY + 14);
    }

    // BOTTOM ライン＋バッジ
    ctx.strokeStyle = "#4499dd"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cellX - 4, bottomY); ctx.lineTo(cellX + cellW + 4, bottomY); ctx.stroke();
    ctx.font = "bold 10px monospace";
    const botTw = ctx.measureText("BOTTOM").width;
    const botBw = botTw + 10, botBh = 14;
    ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = "#4499dd";
    this._rrect(ctx, cellX + cellW/2 - botBw/2, bottomY + 4, botBw, botBh, 3); ctx.fill(); ctx.restore();
    ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("BOTTOM", cellX + cellW / 2, bottomY + 4 + botBh/2);
    ctx.textBaseline = "alphabetic";

    for (let i = 0; i < n; i++) {
      const cellY   = bottomY - (i + 1) * cellH;
      const hasVal  = i <= top;
      const hlColor = highlights[String(i)];

      // 背景
      ctx.fillStyle = hasVal ? _acTheme().cellBg : _acTheme().cellEmptyBg;
      ctx.fillRect(cellX, cellY, cellW, cellH - 1);

      // ハイライト
      if (hlColor) {
        ctx.save(); ctx.globalAlpha = 0.28; ctx.fillStyle = hlColor;
        ctx.fillRect(cellX, cellY, cellW, cellH - 1); ctx.restore();
      }

      // 枠線
      ctx.strokeStyle = hlColor || (hasVal ? "#4472C4" : _acTheme().dimEdge);
      ctx.lineWidth   = hlColor ? 2 : 1;
      ctx.strokeRect(cellX + 0.5, cellY + 0.5, cellW - 1, cellH - 2);

      // 値
      if (hasVal) {
        const fs = Math.max(9, Math.min(14, cellH * 0.50));
        ctx.fillStyle = hlColor || _acTheme().cellValueColor;
        ctx.font = `bold ${fs}px monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), cellX + cellW / 2, cellY + cellH / 2);
        ctx.textBaseline = "alphabetic";
      }

      // インデックス（左）
      ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = "9px monospace";
      ctx.textAlign = "right";
      ctx.fillText(String(i), cellX - 4, cellY + cellH / 2 + 3);
    }

    // TOP ポインタ＋バッジ（右側）
    if (top >= 0 && top < n) {
      const topY  = bottomY - (top + 1) * cellH;
      const midY  = topY + cellH / 2;
      const ax1   = cellX + cellW + 4;
      const ax2   = ax1 + 20;

      ctx.strokeStyle = "#44cc66"; ctx.fillStyle = "#44cc66"; ctx.lineWidth = 1.8;
      // 矢印（← ノードを指す）
      ctx.beginPath(); ctx.moveTo(ax2, midY); ctx.lineTo(ax1 + 8, midY); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(ax1 + 8, midY);
      ctx.lineTo(ax1 + 14, midY - 4);
      ctx.lineTo(ax1 + 14, midY + 4);
      ctx.closePath(); ctx.fill();
      // TOP バッジ
      ctx.font = "bold 10px monospace";
      const tw = ctx.measureText("TOP").width;
      const bw = tw + 10, bh = 14;
      ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = "#44cc66";
      this._rrect(ctx, ax2, midY - bh/2, bw, bh, 3); ctx.fill(); ctx.restore();
      ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("TOP", ax2 + bw/2, midY);
      ctx.textBaseline = "alphabetic";
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // expr_stack_view – 演算木スタック（空セル左＋部分木右＋矢印）
  // stack: [{tree:{...}, color:"#rrggbb"}, ...] (index 0 = bottom)
  // ════════════════════════════════════════════════════════════════════
  _drawExprStackView(obj, areaY, areaH) {
    const { stack = [], max_size = 3, label = "" } = obj;
    const n = max_size;
    const ctx = this.ctx, cw = this.cw;

    // ── レイアウト定数 ──
    const IDX_W  = 20;                      // インデックスラベル幅
    const CELL_W = 46;                      // セル幅
    const CELL_X = IDX_W;                   // セル左端X
    const ARR_GAP = 8;                      // セル右端 → 木エリア左端 間隔
    const TREE_X = CELL_X + CELL_W + ARR_GAP; // 木エリア左端X
    const TREE_W = cw - TREE_X;            // 木エリア幅
    const PAD_T  = label ? 22 : 8;
    const PAD_B  = 68;                      // 下部テキストオーバーレイ回避
    const availH = areaH - PAD_T - PAD_B;
    const rowH   = Math.max(30, availH / Math.max(n, 1));
    const botY   = areaY + PAD_T + availH;  // BOTTOM ライン Y

    ctx.save();

    // ラベル
    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, 2, areaY + 14);
    }

    // BOTTOM ライン + バッジ
    ctx.strokeStyle = "#4499dd"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(CELL_X - 2, botY); ctx.lineTo(CELL_X + CELL_W + 2, botY); ctx.stroke();
    ctx.font = "bold 9px monospace";
    const btw = ctx.measureText("BOTTOM").width + 8, bth = 12;
    ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = "#4499dd";
    this._rrect(ctx, CELL_X + CELL_W / 2 - btw / 2, botY + 3, btw, bth, 3); ctx.fill(); ctx.restore();
    ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("BOTTOM", CELL_X + CELL_W / 2, botY + 3 + bth / 2);
    ctx.textBaseline = "alphabetic";

    // ── 部分木レンダラー（ミニ版） ──
    // 引数: ルートノード, 描画エリア (chartL,chartT,chartW,chartH)
    // 戻り値: {x, y, r} = ルートノードの中心座標と半径
    const drawMiniTree = (root, cL, cT, cW, cH) => {
      if (!root) return null;
      const cnt  = nd => nd ? 1 + cnt(nd.left) + cnt(nd.right) : 0;
      const dep  = nd => nd ? 1 + Math.max(dep(nd.left), dep(nd.right)) : 0;
      const N = cnt(root), d = dep(root);
      if (!N || !d) return null;
      const lH = cH / d;
      const nR = Math.max(5, Math.min(18, lH * 0.40, cW / (N + 1) * 0.80));
      const fs = Math.max(6, Math.min(12, nR * 0.80));
      // 座標割り付け（中順)
      let ii = 0;
      const assign = (nd, dep_) => {
        if (!nd) return;
        assign(nd.left, dep_ + 1);
        nd._x = cL + cW * (ii + 0.5) / N;
        nd._y = cT + lH * (dep_ + 0.5);
        ii++;
        assign(nd.right, dep_ + 1);
      };
      ii = 0; assign(root, 0);
      // エッジ
      const drawE = nd => {
        if (!nd) return;
        for (const ch of [nd.left, nd.right]) {
          if (!ch) continue;
          ctx.beginPath(); ctx.moveTo(nd._x, nd._y); ctx.lineTo(ch._x, ch._y);
          ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
          drawE(ch);
        }
      };
      drawE(root);
      // ノード
      const drawN = nd => {
        if (!nd) return;
        const { _x: x, _y: y, color = "#4472C4", highlight = null } = nd;
        ctx.beginPath(); ctx.arc(x, y, nR, 0, Math.PI * 2);
        ctx.fillStyle = color; ctx.fill();
        if (highlight) {
          ctx.save(); ctx.globalAlpha = 0.35; ctx.fillStyle = highlight;
          ctx.beginPath(); ctx.arc(x, y, nR, 0, Math.PI * 2); ctx.fill(); ctx.restore();
          ctx.strokeStyle = highlight; ctx.lineWidth = 2; ctx.stroke();
        } else {
          ctx.strokeStyle = _acTheme().dimEdge; ctx.lineWidth = 0.8; ctx.stroke();
        }
        ctx.fillStyle = _acTheme().cellText; ctx.font = `bold ${fs}px monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(nd.key), x, y);
        ctx.textBaseline = "alphabetic";
        drawN(nd.left); drawN(nd.right);
      };
      drawN(root);
      // ルート座標を返す
      const leftCnt = cnt(root.left);
      return { x: cL + cW * (leftCnt + 0.5) / N, y: cT + lH * 0.5, r: nR };
    };

    // ── 各スロット描画 ──
    for (let i = 0; i < n; i++) {
      const item     = i < stack.length ? stack[i] : null;
      const hl       = item ? item.color : null;
      const slotTopY = botY - (i + 1) * rowH;
      const slotMidY = slotTopY + rowH / 2;
      const cellH    = Math.min(28, rowH * 0.72);
      const cellTopY = slotTopY + (rowH - cellH) / 2;

      // セル背景
      ctx.fillStyle = item ? _acTheme().cellBg : _acTheme().cellEmptyBg;
      this._rrect(ctx, CELL_X, cellTopY, CELL_W, cellH, 3); ctx.fill();
      if (hl) {
        ctx.save(); ctx.globalAlpha = 0.20; ctx.fillStyle = hl;
        this._rrect(ctx, CELL_X, cellTopY, CELL_W, cellH, 3); ctx.fill(); ctx.restore();
      }
      // セル枠
      ctx.strokeStyle = hl || (item ? "#4472C4" : _acTheme().dimEdge);
      ctx.lineWidth   = hl ? 2 : 1;
      this._rrect(ctx, CELL_X + 0.5, cellTopY + 0.5, CELL_W - 1, cellH - 1, 3); ctx.stroke();

      // インデックスラベル（左）
      ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = "9px monospace";
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(String(i), CELL_X - 3, slotMidY);

      // TOP バッジ（最上位スロット）
      if (item && i === stack.length - 1) {
        ctx.fillStyle = hl || "#44cc66"; ctx.font = "bold 8px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("TOP", CELL_X + CELL_W / 2, slotMidY);
      }
      ctx.textBaseline = "alphabetic";

      // 部分木＋矢印
      if (item && item.tree) {
        const tPad = 4;
        const rootInfo = drawMiniTree(
          item.tree,
          TREE_X + tPad, slotTopY + tPad,
          TREE_W - tPad * 2, rowH - tPad * 2
        );
        if (rootInfo) {
          // ベジェ曲線矢印: セル右端 → ルートノード左端
          const ax1 = CELL_X + CELL_W + 2, ay1 = slotMidY;
          const ax2 = rootInfo.x - rootInfo.r - 2, ay2 = rootInfo.y;
          const arrowColor = hl || "#4488cc";
          ctx.strokeStyle = arrowColor; ctx.fillStyle = arrowColor; ctx.lineWidth = 1.4;
          ctx.beginPath();
          ctx.moveTo(ax1, ay1);
          ctx.bezierCurveTo(
            ax1 + (ax2 - ax1) * 0.45, ay1,
            ax2 - 14, ay2,
            ax2, ay2
          );
          ctx.stroke();
          // 矢じり
          const ang = Math.atan2(ay2 - ay1, ax2 - ax1);
          ctx.beginPath();
          ctx.moveTo(ax2, ay2);
          ctx.lineTo(ax2 - 8 * Math.cos(ang - 0.42), ay2 - 8 * Math.sin(ang - 0.42));
          ctx.lineTo(ax2 - 8 * Math.cos(ang + 0.42), ay2 - 8 * Math.sin(ang + 0.42));
          ctx.closePath(); ctx.fill();
        }
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // queue_circ – 円形循環キュー
  // ════════════════════════════════════════════════════════════════════
  // queue_circ – ドーナツリング型循環キュー
  // ════════════════════════════════════════════════════════════════════
  _drawQueueCirc(obj, areaY, areaH) {
    const { values = [], front = 0, back = 0, count = 0,
            label = "", highlights = {} } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    // ── レイアウト計算 ──────────────────────────────────────────────
    const topPad   = label ? 18 : 6;
    const botPad   = 52;   // 底部テキストオーバーレイ分を除外
    // ポインタバッジまで含めた総占有半径 = outerR + IDX_PAD + PTR_LEN + BADGE_R
    const IDX_PAD  = 14;   // outerR 外縁～インデックスラベル中心
    const PTR_LEN  = 22;   // インデックスラベル外縁～矢印先端
    const BADGE_R  = 10;   // バッジ半高さ程度
    const totalExt = IDX_PAD + PTR_LEN + BADGE_R;
    const innerH   = areaH - topPad - botPad;  // 利用可能な縦スペース
    const outerR   = Math.max(28, Math.min(
      cw / 2 - totalExt - 4,
      innerH / 2 - totalExt - 4
    ));
    const innerR   = outerR * 0.46;
    const midR     = (outerR + innerR) / 2;
    const idxR     = outerR + IDX_PAD;

    const cx = cw / 2;
    // 中心をテキスト領域を除いたエリアの中央に配置
    const cy = areaY + topPad + innerH / 2;

    const sliceA   = (2 * Math.PI) / n;
    const startAng = -Math.PI / 2;   // 12時から開始

    ctx.save();

    // ラベル
    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, 6, areaY + 12);
    }

    // アクティブインデックス集合
    const activeSet = new Set();
    for (let j = 0; j < count; j++) activeSet.add((front + j) % n);

    // ── パイセグメント描画 ──────────────────────────────────────────
    for (let i = 0; i < n; i++) {
      const a1   = startAng + i * sliceA;
      const a2   = startAng + (i + 1) * sliceA;
      const midA = (a1 + a2) / 2;
      const isAct   = activeSet.has(i);
      const hlColor = highlights[String(i)];

      // セグメントパス（ドーナツの一切れ）
      const seg = () => {
        ctx.beginPath();
        ctx.arc(cx, cy, outerR, a1, a2);
        ctx.arc(cx, cy, innerR, a2, a1, true);
        ctx.closePath();
      };

      // 背景
      seg();
      ctx.fillStyle = isAct ? _acTheme().cellBg : _acTheme().cellEmptyBg;
      ctx.fill();

      // ハイライト
      if (hlColor) {
        seg();
        ctx.save(); ctx.globalAlpha = 0.30; ctx.fillStyle = hlColor;
        ctx.fill(); ctx.restore();
      }

      // 枠線
      seg();
      ctx.strokeStyle = hlColor || (isAct ? "#4472C4" : _acTheme().dimEdge);
      ctx.lineWidth   = hlColor ? 2 : 1;
      ctx.stroke();

      // 値テキスト（アクティブ or ハイライトのみ）
      if (isAct || hlColor) {
        const tx = cx + midR * Math.cos(midA);
        const ty = cy + midR * Math.sin(midA);
        const arcLen = midR * sliceA;
        const fs = Math.max(8, Math.min(13, arcLen * 0.40));
        ctx.fillStyle = hlColor || _acTheme().cellValueColor;
        ctx.font = `bold ${fs}px monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), tx, ty);
        ctx.textBaseline = "alphabetic";
      }

      // インデックスラベル（外側・緑）
      ctx.fillStyle = "#44aa44"; ctx.font = "bold 9px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(i),
        cx + idxR * Math.cos(midA),
        cy + idxR * Math.sin(midA));
      ctx.textBaseline = "alphabetic";
    }

    // 外縁・内縁の境界円（強調）
    ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(cx, cy, outerR, 0, 2 * Math.PI); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, innerR, 0, 2 * Math.PI); ctx.stroke();

    // 空キュー表示
    if (count === 0) {
      ctx.fillStyle = _acTheme().emptyText; ctx.font = "11px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("(空)", cx, cy);
      ctx.textBaseline = "alphabetic";
    }

    // ── 外側ポインタ矢印 + バッジ ────────────────────────────────
    // front と back が重なる場合は back を隣スライスの中央にずらす
    const BADGE_H  = 13;
    const BADGE_PD = 8;
    const arrowGap = IDX_PAD + 4;   // outerR からの矢印先端距離
    const arrowLen = PTR_LEN;        // 矢印の長さ

    const drawExtPtr = (idxF, color, lbl, angleOffset = 0) => {
      const midA = startAng + (idxF + 0.5) * sliceA + angleOffset;
      const tipR  = outerR + arrowGap;          // 矢印先端（リング外縁すぐ外）
      const tailR = tipR + arrowLen;             // 矢印尾端

      const tx1 = cx + tailR * Math.cos(midA);
      const ty1 = cy + tailR * Math.sin(midA);
      const tx2 = cx + tipR  * Math.cos(midA);
      const ty2 = cy + tipR  * Math.sin(midA);

      // 矢印
      ctx.strokeStyle = color; ctx.lineWidth = 2;
      this._arrow(ctx, tx1, ty1, tx2, ty2);

      // バッジ（矢印尾端のさらに外側）
      const badgeCR = tailR + BADGE_H / 2 + 2;
      const bcx = cx + badgeCR * Math.cos(midA);
      const bcy = cy + badgeCR * Math.sin(midA);
      ctx.font = "bold 10px monospace";
      const tw = ctx.measureText(lbl).width;
      const bw = tw + BADGE_PD;

      ctx.save(); ctx.globalAlpha = 0.92; ctx.fillStyle = color;
      this._rrect(ctx, bcx - bw/2, bcy - BADGE_H/2, bw, BADGE_H, 3);
      ctx.fill(); ctx.restore();

      ctx.fillStyle = _acTheme().badgeText; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(lbl, bcx, bcy);
      ctx.textBaseline = "alphabetic";
    };

    // front ポインタ（緑）
    drawExtPtr(front % n, "#44cc66", "front");

    // back ポインタ（オレンジ）: front と重なる場合は半スライスずらす
    const backIdx = back % n;
    const frontIdx = front % n;
    if (backIdx === frontIdx && count > 0) {
      drawExtPtr(backIdx, "#ff8844", "back", sliceA * 0.45);
    } else {
      drawExtPtr(backIdx, "#ff8844", "back");
    }

    ctx.restore();
  }

  /** 矢印を描画 (ctx のstrokeStyle/lineWidth を使用) */
  _arrow(ctx, x1, y1, x2, y2) {
    const HEAD = 6;
    const ang  = Math.atan2(y2 - y1, x2 - x1);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - HEAD * Math.cos(ang - Math.PI / 6),
               y2 - HEAD * Math.sin(ang - Math.PI / 6));
    ctx.lineTo(x2 - HEAD * Math.cos(ang + Math.PI / 6),
               y2 - HEAD * Math.sin(ang + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
  }

  /** 角丸矩形パスを生成 */
  _rrect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.arcTo(x + w, y,     x + w, y + r,     r);
    ctx.lineTo(x + w, y + h - r);
    ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
    ctx.lineTo(x + r, y + h);
    ctx.arcTo(x,     y + h, x,     y + h - r, r);
    ctx.lineTo(x,     y + r);
    ctx.arcTo(x,     y,     x + r, y,         r);
    ctx.closePath();
  }

  // ════════════════════════════════════════════════════════════════════
  // bst_tree – 二分探索木 / 赤黒木
  // ════════════════════════════════════════════════════════════════════
  _drawBstTree(obj, areaY, areaH, areaX = 0, areaW = null) {
    const { root = null, label = "" } = obj;
    if (!root) return;

    const ctx = this.ctx;
    const cw  = (areaW !== null) ? areaW : this.cw;
    const ox  = areaX;

    const PAD    = 12;
    const chartL = ox + PAD;
    const chartR = ox + cw - PAD;
    const chartT = areaY + PAD + (label ? 14 : 4);
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // Count nodes + depth
    function countNodes(node) {
      if (!node) return 0;
      return 1 + countNodes(node.left) + countNodes(node.right);
    }
    function treeDepth(node) {
      if (!node) return 0;
      return 1 + Math.max(treeDepth(node.left), treeDepth(node.right));
    }

    const N = countNodes(root);
    const d = treeDepth(root);
    if (d === 0 || N === 0) return;

    const levelH = chartH / d;
    const nodeR  = Math.max(8, Math.min(22, levelH * 0.38, chartW / (N + 1) * 0.8));

    // In-order traversal to assign x positions
    let inorderIdx = 0;
    function assignPos(node, depth_) {
      if (!node) return;
      assignPos(node.left, depth_ + 1);
      node._x = chartL + chartW * (inorderIdx + 0.5) / N;
      node._y = chartT + levelH * (depth_ + 0.5);
      inorderIdx++;
      assignPos(node.right, depth_ + 1);
    }
    inorderIdx = 0;
    assignPos(root, 0);

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, ox + PAD, areaY + 14);
    }

    // Draw edges
    function drawEdges(node) {
      if (!node) return;
      if (node.left) {
        const dimEdge = node.dim || node.left.dim;
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.left._x, node.left._y);
        ctx.strokeStyle = dimEdge ? _acTheme().dimEdge : _acTheme().edgeColor;
        ctx.lineWidth   = dimEdge ? 0.5 : 1; ctx.stroke();
        drawEdges(node.left);
      }
      if (node.right) {
        const dimEdge = node.dim || node.right.dim;
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.right._x, node.right._y);
        ctx.strokeStyle = dimEdge ? _acTheme().dimEdge : _acTheme().edgeColor;
        ctx.lineWidth   = dimEdge ? 0.5 : 1; ctx.stroke();
        drawEdges(node.right);
      }
    }
    drawEdges(root);

    // Draw nodes
    const fs = Math.max(7, Math.min(13, nodeR * 0.75));
    function drawNodes(node) {
      if (!node) return;
      const { _x: x, _y: y, color = "#4472C4", highlight = null, dim = false } = node;

      if (dim) {
        // Ghost / unbuilt node
        ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2);
        ctx.fillStyle = _acTheme().ghostFill; ctx.fill();
        ctx.strokeStyle = _acTheme().ghostStroke; ctx.lineWidth = 0.8; ctx.stroke();
        ctx.fillStyle = _acTheme().ghostText; ctx.font = `${fs}px monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(node.key), x, y); ctx.textBaseline = "alphabetic";
      } else {
        // Node circle
        ctx.beginPath();
        ctx.arc(x, y, nodeR, 0, Math.PI * 2);
        ctx.fillStyle = _acTheme().nodeBg;
        ctx.fill();

        // Tinted fill
        ctx.save();
        ctx.globalAlpha = highlight ? 0.5 : 0.35;
        ctx.fillStyle   = highlight || color;
        ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2); ctx.fill();
        ctx.restore();

        // Stroke
        ctx.strokeStyle = highlight || color;
        ctx.lineWidth   = highlight ? 2.5 : 1.5;
        ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2); ctx.stroke();

        // Key label
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `bold ${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(node.key), x, y);
        ctx.textBaseline = "alphabetic";
      }

      drawNodes(node.left);
      drawNodes(node.right);
    }
    drawNodes(root);

    // ── Rotation arc overlay (AVL / tree rotation) ───────────────────
    if (obj.rotation) {
      const rotType  = obj.rotation.type;
      const rotPivot = obj.rotation.pivot;
      const rotChild = obj.rotation.child ?? null;  // LR/RL のみ非null

      // キーでノードを探す（assignPos で _x, _y 付与済み）
      const findNode = (n, key) => {
        if (!n) return null;
        if (n.key === key) return n;
        return findNode(n.left, key) || findNode(n.right, key);
      };

      const pn = findNode(root, rotPivot);
      const cn = rotChild !== null ? findNode(root, rotChild) : null;

      // cx,cy の位置に半円弧＋矢印を描く
      // ccw=false → 右半円(CW,時計回り) / ccw=true → 左半円(CCW,反時計回り)
      const drawArcAt = (cx, cy, ccw, dashed) => {
        const R = nodeR * 2.8;
        ctx.save();
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = "#ff8800";
        ctx.fillStyle   = "#ff8800";
        ctx.lineWidth   = 3.5;
        ctx.setLineDash(dashed ? [7, 4] : []);
        ctx.beginPath();
        ctx.arc(cx, cy, R, -Math.PI / 2, Math.PI / 2, ccw);
        ctx.stroke();
        ctx.setLineDash([]);
        // 矢印ヘッド: 弧の下端 (cx, cy+R)
        // CCW弧(左): 進行方向=右 → ang=0  /  CW弧(右): 進行方向=左 → ang=π
        const ax = cx, ay = cy + R;
        const ang = ccw ? 0 : Math.PI;
        const H = 10;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - H * Math.cos(ang - 0.6), ay - H * Math.sin(ang - 0.6));
        ctx.lineTo(ax - H * Math.cos(ang + 0.6), ay - H * Math.sin(ang + 0.6));
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      };

      if (pn && pn._x !== undefined) {
        const px = pn._x, py = pn._y;
        if (rotType === 'LL') {
          // pivot で右回転(CW) → 右半円
          drawArcAt(px, py, false, false);
        } else if (rotType === 'RR') {
          // pivot で左回転(CCW) → 左半円
          drawArcAt(px, py, true, false);
        } else if (rotType === 'LR') {
          // ① 子ノードで左回転(CCW) → 左半円
          if (cn && cn._x !== undefined) drawArcAt(cn._x, cn._y, true, true);
          // ② pivot で右回転(CW) → 右半円
          drawArcAt(px, py, false, true);
        } else if (rotType === 'RL') {
          // ① 子ノードで右回転(CW) → 右半円
          if (cn && cn._x !== undefined) drawArcAt(cn._x, cn._y, false, true);
          // ② pivot で左回転(CCW) → 左半円
          drawArcAt(px, py, true, true);
        }

        // ラベル（pivot 弧の上に）
        const rotLabels = { LL: '右回転', RR: '左回転', LR: '左右二重回転', RL: '右左二重回転' };
        const R = nodeR * 2.8;
        ctx.save();
        ctx.globalAlpha  = 1.0;
        ctx.font         = `bold ${Math.max(10, Math.min(13, nodeR * 0.75))}px sans-serif`;
        ctx.fillStyle    = "#ff8800";
        ctx.textAlign    = "center";
        ctx.textBaseline = "bottom";
        ctx.fillText(rotLabels[rotType] || rotType, px, py - R + 2);
        ctx.textBaseline = "alphabetic";
        ctx.restore();
      }
    }
    // ─────────────────────────────────────────────────────────────────

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // graph_view – 有向 / 無向グラフ
  // ════════════════════════════════════════════════════════════════════
  _drawGraphView(obj, areaY, areaH) {
    const { nodes = [], edges = [], label = "", directed = false } = obj;
    if (nodes.length === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 24;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD + (label ? 14 : 4);
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    const px = (xr) => chartL + xr * chartW;
    const py = (yr) => chartT + yr * chartH;

    const nodeR = Math.max(14, Math.min(24, Math.min(chartW, chartH) / (nodes.length * 0.9 + 2)));
    const fs    = Math.max(8, Math.min(13, nodeR * 0.65));

    // Build position map
    const pos = {};
    for (const n of nodes) pos[n.id] = { x: px(n.x), y: py(n.y) };

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD, areaY + 14);
    }

    // Draw edges first
    for (const e of edges) {
      const p1 = pos[e.from], p2 = pos[e.to];
      if (!p1 || !p2) continue;
      const col = e.highlight ? "#ffcc44" : _acTheme().edgeColor;
      ctx.strokeStyle = col;
      ctx.lineWidth   = e.highlight ? 2.5 : 1.2;
      if (e.directed || directed) {
        // Shorten line to node boundary
        const dx = p2.x - p1.x, dy = p2.y - p1.y;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        const ux = dx / len, uy = dy / len;
        const sx = p1.x + ux * nodeR, sy = p1.y + uy * nodeR;
        const ex = p2.x - ux * nodeR, ey = p2.y - uy * nodeR;
        ctx.fillStyle = col;
        this._arrow(ctx, sx, sy, ex, ey);
      } else {
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
      }
      // Edge weight label
      if (e.weight !== undefined) {
        const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
        ctx.fillStyle = "#8899aa"; ctx.font = "9px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(e.weight), mx + 6, my - 6);
        ctx.textBaseline = "alphabetic";
      }
    }

    // Draw nodes
    for (const n of nodes) {
      const { x, y } = pos[n.id];
      const color = n.color || "#4472C4";
      const hl    = n.highlight;

      ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = _acTheme().nodeBg; ctx.fill();

      ctx.save(); ctx.globalAlpha = hl ? 0.55 : 0.28;
      ctx.fillStyle = hl || color;
      ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2); ctx.fill();
      ctx.restore();

      ctx.strokeStyle = hl || color;
      ctx.lineWidth   = hl ? 2.5 : 1.5;
      ctx.beginPath(); ctx.arc(x, y, nodeR, 0, Math.PI * 2); ctx.stroke();

      ctx.fillStyle    = _acTheme().cellText;
      ctx.font         = `bold ${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(n.label !== undefined ? n.label : n.id), x, y);
      ctx.textBaseline = "alphabetic";
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // hash_table – ハッシュ表 (線形探索法 / チェイン法)
  // ════════════════════════════════════════════════════════════════════
  _drawHashTable(obj, areaY, areaH) {
    const { slots = [], m = 0, label = "", active = -1 } = obj;
    if (m === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T  = label ? 20 : 8;
    const PAD_B  = 6;
    const PAD_L  = 48;   // index labels
    const PAD_R  = 8;

    const availH    = areaH - PAD_T - PAD_B;
    const cellH     = Math.max(14, Math.min(38, availH / m));
    const cellW     = 60;                          // ハッシュキーは短い整数 — 固定幅
    const CHAIN_ROOM = 160;
    const startX    = PAD_L + Math.max(0, Math.floor((cw - PAD_L - PAD_R - cellW - CHAIN_ROOM) / 2));
    const chainStart = startX + cellW + 8;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, 6, areaY + 14);
    }

    for (let i = 0; i < m; i++) {
      const cellY  = areaY + PAD_T + i * cellH;
      const slot   = slots[i] || { key: null, highlight: null, chain: [] };
      const isAct  = (i === active);
      const hl     = slot.highlight;

      // Index label
      ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = "9px monospace";
      ctx.textAlign = "right";
      ctx.fillText(`[${i}]`, startX - 6, cellY + cellH * 0.65);

      // Main cell
      ctx.fillStyle = (slot.key !== null || (slot.chain && slot.chain.length > 0))
                      ? _acTheme().cellBg : _acTheme().cellEmptyBg;
      ctx.fillRect(startX, cellY, cellW, cellH - 1);

      if (hl || isAct) {
        ctx.save(); ctx.globalAlpha = 0.38;
        ctx.fillStyle = hl || "#ffcc44";
        ctx.fillRect(startX, cellY, cellW, cellH - 1);
        ctx.restore();
      }

      ctx.strokeStyle = hl ? hl : (isAct ? "#ffcc44" : (slot.key !== null ? "#4472C4" : _acTheme().dimEdge));
      ctx.lineWidth   = (hl || isAct) ? 2 : 1;
      ctx.strokeRect(startX + 0.5, cellY + 0.5, cellW - 1, cellH - 2);

      if (slot.key !== null) {
        const fs = Math.max(8, Math.min(13, cellH * 0.50));
        ctx.fillStyle    = hl ? hl : _acTheme().cellValueColor;
        ctx.font         = `bold ${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(slot.key), startX + cellW / 2, cellY + cellH / 2);
        ctx.textBaseline = "alphabetic";
      } else if (!slot.chain || slot.chain.length === 0) {
        // Empty marker
        ctx.fillStyle = _acTheme().emptyText; ctx.font = "9px monospace";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText("—", startX + cellW / 2, cellY + cellH / 2);
        ctx.textBaseline = "alphabetic";
      }

      // Chain nodes (for chaining)
      if (slot.chain && slot.chain.length > 0) {
        const chainCellW = Math.max(cellH * 0.9, 24);
        let cx = chainStart;
        for (let j = 0; j < slot.chain.length; j++) {
          // Arrow connector
          ctx.strokeStyle = "#5577aa"; ctx.lineWidth = 1;
          const ax1 = j === 0 ? startX + cellW : cx - 8;
          ctx.beginPath(); ctx.moveTo(ax1, cellY + cellH / 2);
          ctx.lineTo(cx - 1, cellY + cellH / 2); ctx.stroke();
          ctx.fillStyle = "#5577aa";
          ctx.beginPath();
          ctx.moveTo(cx - 1, cellY + cellH / 2);
          ctx.lineTo(cx - 7, cellY + cellH / 2 - 3);
          ctx.lineTo(cx - 7, cellY + cellH / 2 + 3);
          ctx.closePath(); ctx.fill();

          // Chain node box
          ctx.fillStyle = _acTheme().cellBg;
          ctx.fillRect(cx, cellY + 1, chainCellW, cellH - 3);
          ctx.strokeStyle = (slot.chainHL && slot.chainHL[j]) ? slot.chainHL[j] : "#4472C4";
          ctx.lineWidth = (slot.chainHL && slot.chainHL[j]) ? 2 : 1;
          ctx.strokeRect(cx + 0.5, cellY + 1.5, chainCellW - 1, cellH - 4);

          const fs2 = Math.max(7, Math.min(11, chainCellW * 0.42));
          ctx.fillStyle    = _acTheme().cellValueColor;
          ctx.font         = `${fs2}px monospace`;
          ctx.textAlign    = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(String(slot.chain[j]), cx + chainCellW / 2, cellY + cellH / 2);
          ctx.textBaseline = "alphabetic";

          cx += chainCellW + 10;
        }
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // btree_view – B木 (2-3-4木など最小次数 t=2)
  // ════════════════════════════════════════════════════════════════════
  _drawBtreeView(obj, areaY, areaH) {
    const { root = null, label = "", t = 2 } = obj;
    if (!root) return;

    const ctx = this.ctx;
    const cw  = this.cw;
    const MAX_KEYS = 2 * t - 1;

    const PAD    = 12;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD + (label ? 14 : 4);
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // ── レイアウト計算 ──────────────────────────────────────────────
    function treeDepth(node) {
      if (!node || !node.children || node.children.length === 0) return 1;
      return 1 + Math.max(...node.children.map(treeDepth));
    }
    // 各ノードの「葉数」を数える (レイアウト幅の基準)
    function leafCount(node) {
      if (!node || !node.children || node.children.length === 0)
        return Math.max(1, node ? node.keys.length : 1);
      return node.children.reduce((s, c) => s + leafCount(c), 0);
    }

    const depth  = treeDepth(root);
    const totalL = leafCount(root);
    const levelH = chartH / depth;
    // セル幅: 利用可能幅を葉数×最大キー数で割る
    const CELL_W = Math.max(16, Math.min(32, chartW / (totalL * MAX_KEYS)));
    const NODE_H = Math.max(16, Math.min(30, levelH * 0.48));

    // ── 座標割り当て (再帰) ─────────────────────────────────────────
    let leafIdx = 0;
    function assignPos(node, d) {
      const y = chartT + levelH * (d + 0.5);
      if (!node.children || node.children.length === 0) {
        // 葉ノード: 左から順に配置
        const w   = Math.max(1, node.keys.length);
        node._x   = chartL + chartW * (leafIdx + w / 2) / totalL;
        node._y   = y;
        leafIdx  += w;
      } else {
        // 内部ノード: 子を先に配置し、子の中心に自分を置く
        const startIdx = leafIdx;
        for (const child of node.children) assignPos(child, d + 1);
        const endIdx = leafIdx;
        node._x = chartL + chartW * (startIdx + (endIdx - startIdx) / 2) / totalL;
        node._y = y;
      }
    }
    leafIdx = 0;
    assignPos(root, 0);

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD, areaY + 14);
    }

    // ── 辺の描画 ───────────────────────────────────────────────────
    function drawEdges(node) {
      if (!node.children || node.children.length === 0) return;
      const nk  = node.keys.length;
      const nw  = nk * CELL_W;
      for (let ci = 0; ci < node.children.length; ci++) {
        const child = node.children[ci];
        // 親の接続点: キーとキーの間（ci 番目の隙間）
        const frac = (ci + 0.5) / (nk + 1);
        const px   = node._x - nw / 2 + frac * nw;
        const py   = node._y + NODE_H / 2;
        const cy   = child._y - NODE_H / 2;
        ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(child._x, cy);
        ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(child);
      }
    }
    drawEdges(root);

    // ── ノードの描画 ───────────────────────────────────────────────
    const fs = Math.max(7, Math.min(13, CELL_W * 0.5, NODE_H * 0.55));
    function drawNode(node) {
      const nk = node.keys.length;
      const nw = nk * CELL_W;
      const nx = node._x - nw / 2;
      const ny = node._y - NODE_H / 2;

      for (let ki = 0; ki < nk; ki++) {
        const cx = nx + ki * CELL_W;
        const hl = node.highlight && node.highlight[ki];

        // 背景
        ctx.fillStyle = _acTheme().cellBg;
        ctx.fillRect(cx, ny, CELL_W - 1, NODE_H);
        if (hl) {
          ctx.save(); ctx.globalAlpha = 0.45; ctx.fillStyle = hl;
          ctx.fillRect(cx, ny, CELL_W - 1, NODE_H); ctx.restore();
        }

        // 枠線
        ctx.strokeStyle = hl || "#4472C4";
        ctx.lineWidth   = hl ? 2 : 1;
        ctx.strokeRect(cx + 0.5, ny + 0.5, CELL_W - 2, NODE_H - 1);

        // キー値
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `bold ${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(node.keys[ki]), cx + CELL_W / 2, node._y);
        ctx.textBaseline = "alphabetic";
      }

      if (node.children) {
        for (const child of node.children) drawNode(child);
      }
    }
    drawNode(root);

    ctx.restore();
  }

  // ── op_list – 操作リスト表示 ──────────────────────────────────────────
  _drawOpList(obj, areaY, areaH) {
    const ctx  = this.ctx;
    const cw   = this.cw;
    const th   = _acTheme();
    const ops  = obj.ops || [];
    if (ops.length === 0) return;

    const curIdx = obj.current_idx ?? -1;   // 現在実行中の操作インデックス
    const padX   = 12;
    const padY   = 6;

    ctx.save();

    // ─── 背景 ───────────────────────────────────────────────────────────
    ctx.fillStyle = th.canvasBg;
    ctx.fillRect(0, areaY, cw, areaH);

    // ─── ラベル ──────────────────────────────────────────────────────────
    const labelH  = 18;
    const label   = obj.label || "操作列";
    ctx.font      = `bold 11px sans-serif`;
    ctx.fillStyle = th.labelColor;
    ctx.textBaseline = "middle";
    ctx.fillText(label, padX, areaY + padY + labelH / 2);

    // ─── 区切り線 ────────────────────────────────────────────────────────
    const lineY = areaY + padY + labelH + 2;
    ctx.strokeStyle = th.edgeColor;
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(padX, lineY);
    ctx.lineTo(cw - padX, lineY);
    ctx.stroke();

    // ─── アイテム描画 ────────────────────────────────────────────────────
    const listY  = lineY + 4;
    const listH  = areaH - (listY - areaY) - padY;
    const itemH  = Math.min(22, listH / ops.length);
    const fsize  = Math.max(9, Math.min(13, itemH * 0.72));

    // 表示ウィンドウ: 全部入りきらない場合は current 付近を中心に表示
    const maxVisible = Math.floor(listH / itemH);
    let startIdx = 0;
    if (ops.length > maxVisible && curIdx >= 0) {
      startIdx = Math.max(0, Math.min(curIdx - Math.floor(maxVisible / 2),
                                      ops.length - maxVisible));
    }

    ctx.font = `${fsize}px monospace`;

    for (let i = startIdx; i < ops.length; i++) {
      const iy = listY + (i - startIdx) * itemH;
      if (iy + itemH > areaY + areaH - padY) break;

      const isCurrent = (i === curIdx);
      const isDone    = (i < curIdx);

      // 現在行ハイライト背景
      if (isCurrent) {
        ctx.fillStyle = "rgba(255, 220, 0, 0.15)";
        ctx.fillRect(2, iy, cw - 4, itemH);
      }

      // テキスト色・マーカー
      if (isCurrent) {
        ctx.fillStyle = "#ffdd44";
      } else if (isDone) {
        ctx.fillStyle = "#44aa44";
      } else {
        ctx.fillStyle = th.labelColor;
      }

      ctx.textBaseline = "middle";
      const marker = isCurrent ? "▶" : (isDone ? "✓" : "·");
      const numStr = String(i + 1).padStart(2, " ");
      ctx.fillText(`${marker} ${numStr}. ${ops[i]}`, padX, iy + itemH / 2);
    }

    // スクロール省略インジケータ
    if (startIdx > 0) {
      ctx.fillStyle = th.labelColor;
      ctx.font      = `10px sans-serif`;
      ctx.textBaseline = "middle";
      ctx.fillText(`… (${startIdx} 件省略)`, padX, listY - 8);
    }

    ctx.restore();
  }
}
