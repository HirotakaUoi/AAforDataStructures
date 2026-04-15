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
 */

"use strict";

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
            text_position = "top" } = frame;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.cw, this.ch);

    // 背景
    ctx.fillStyle = "#0d1117";
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
          case "stack_v":       this._drawStackV(obj, areaY, eachH);       break;
          case "queue_circ":    this._drawQueueCirc(obj, areaY, eachH);    break;
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
      ctx.fillStyle = "rgba(10, 14, 26, 0.85)";
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
      if (found === true) {
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
      ctx.fillStyle = "#1a4a1a";
      ctx.fillRect(refX + 0.5, refY, rw - 1, refH);
      ctx.strokeStyle = "#44cc44"; ctx.lineWidth = 1.5;
      ctx.strokeRect(refX + 0.5, refY + 0.5, rw - 1, refH - 1);
      ctx.save(); ctx.strokeStyle = "rgba(68,204,68,0.35)";
      ctx.lineWidth = 1; ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(PAD_L + REF_W, refY);
      ctx.lineTo(chartR, refY); ctx.stroke(); ctx.restore();
      const rFs = Math.max(7, Math.min(10, REF_W * 0.4));
      ctx.fillStyle = "#44cc44"; ctx.font = `${rFs}px monospace`;
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
        ctx.fillStyle = "#ccc"; ctx.font = `${fs}px sans-serif`;
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
      ctx.fillStyle = "#4a6080"; ctx.font = `${iFs}px sans-serif`;
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
  _drawArray1dCells(obj, areaY, areaH) {
    const {
      values = [], label = "",
      highlights = {}, fills = [],
      pointer = null, watchman_index = null,
      target = null,
    } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T = 22; const PAD_B = 16;
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

    // セルサイズ: 横幅を n 等分し正方形に近づける
    const cellW  = Math.max(18, Math.min(56, (chartR - chartL) / n));
    const cellH  = Math.min(cellW, Math.max(18, chartH * 0.65));
    const totalW = cellW * n;
    const startX = chartL + Math.max(0, ((chartR - chartL) - totalW) / 2);
    const cellY  = chartT + (chartH - cellH) / 2;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    // target セル
    if (HAS_TARGET) {
      const tx = PAD_L;
      ctx.fillStyle = "#1a4a1a";
      ctx.fillRect(tx, cellY, TGT_W - 2, cellH);
      ctx.strokeStyle = "#44cc44"; ctx.lineWidth = 1.5;
      ctx.strokeRect(tx + 0.5, cellY + 0.5, TGT_W - 3, cellH - 1);

      const fs = Math.max(8, Math.min(13, (TGT_W - 4) * 0.4));
      ctx.fillStyle = "#44cc44"; ctx.font = `bold ${fs}px monospace`;
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
    for (let i = 0; i < n; i++) {
      const cx          = startX + i * cellW;
      const isWatchman  = (watchman_index === i);
      const hlColor     = highlights[String(i)];

      // 背景
      if (isWatchman) {
        ctx.fillStyle = "#3d2000";
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
      } else if (hlColor) {
        ctx.fillStyle = "#1c2a3a";
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
        ctx.save(); ctx.globalAlpha = 0.35;
        ctx.fillStyle = hlColor;
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
        ctx.restore();
      } else {
        ctx.fillStyle = "#1c2a3a";
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
      }

      // ボーダー
      ctx.strokeStyle = isWatchman ? "#cc6600" : hlColor ? hlColor : "#336699";
      ctx.lineWidth   = isWatchman ? 2 : hlColor ? 1.5 : 1;
      ctx.strokeRect(cx + 0.5, cellY + 0.5, cellW - 2, cellH - 1);

      // 値ラベル
      const fs = Math.max(8, Math.min(14, cellW * 0.48, cellH * 0.48));
      ctx.fillStyle    = "#ffffff";
      ctx.font         = `${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(values[i]), cx + cellW / 2, cellY + cellH / 2);
      ctx.textBaseline = "alphabetic";

      // インデックスラベル (下)
      if (cellW >= 14) {
        const iFs = Math.max(7, Math.min(9, cellW * 0.38));
        ctx.fillStyle = "#4a6080"; ctx.font = `${iFs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(String(i), cx + cellW / 2, cellY + cellH + 12);
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
      ctx.strokeStyle = isGhostEdge ? "#1b2535" : "#334455";
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
        ctx.fillStyle   = "#0f1820";
        ctx.fill();
        ctx.strokeStyle = "#1c2d3e";
        ctx.lineWidth   = 0.8;
        ctx.stroke();
        ctx.fillStyle    = "#253545";
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";
      } else {
        // 確定済みノード: 通常描画
        if (hlColor) {
          ctx.fillStyle = "#0d1117"; ctx.fill();
          ctx.save(); ctx.globalAlpha = 0.4;
          ctx.fillStyle = hlColor; ctx.fill(); ctx.restore();
          ctx.strokeStyle = hlColor; ctx.lineWidth = 2;
        } else {
          ctx.fillStyle = "#1a2a3a"; ctx.fill();
          ctx.strokeStyle = "#4472C4"; ctx.lineWidth = 1.5;
        }
        ctx.stroke();

        ctx.fillStyle    = "#ffffff";
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";

        // インデックス (右下小)
        if (nodeR >= 12) {
          const iFs = Math.max(6, Math.min(8, nodeR * 0.42));
          ctx.fillStyle = "#3a5070";
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
      ctx.lineWidth   = isActive ? 1.5 : 0.8;
      ctx.beginPath();
      ctx.moveTo(PAD_L + LBL_W + SEP_W, rowY + 3);
      ctx.lineTo(PAD_L + LBL_W + SEP_W, rowY + rowH - 3);
      ctx.stroke();

      for (let c = 0; c < cells.length; c++) {
        const cx     = PAD_L + LBL_W + SEP_W + cellPad + c * (cellW + cellPad);
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = "#0d1117";
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.save(); ctx.globalAlpha = isLast ? 0.5 : 0.22;
        ctx.fillStyle = color;
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.restore();

        ctx.strokeStyle = isLast ? "#ffffff" : color;
        ctx.lineWidth   = isLast ? 1.5 : 0.8;
        ctx.strokeRect(cx + 0.5, rowY + 2.5, cellW - 1, rowH - 5);

        const fs = Math.max(7, Math.min(12, cellW * 0.44, (rowH - 4) * 0.55));
        ctx.fillStyle    = "#ffffff";
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
      ctx.lineWidth   = isActive ? 1.2 : 0.5;
      ctx.globalAlpha = isActive ? 1.0 : 0.4;
      ctx.beginPath();
      ctx.moveTo(colX,          cellStartY);
      ctx.lineTo(colX + cellW,  cellStartY);
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // セル（上から下へ積む: index 0 が一番上）
      for (let c = 0; c < cells.length; c++) {
        const cellY  = cellStartY + c * cellH + cellPad;
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = "#0d1117";
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.save();
        ctx.globalAlpha = isLast ? 0.55 : 0.25;
        ctx.fillStyle   = color;
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.restore();

        ctx.strokeStyle = isLast ? "#ffffff" : color;
        ctx.lineWidth   = isLast ? 1.2 : 0.6;
        ctx.strokeRect(colX + 0.5, cellY + 0.5, cellW - 1, cellH - cellPad - 1);

        ctx.fillStyle    = "#ffffff";
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

    // 左端ハッシュ記号
    this._drawTapeHashmark(ctx, PAD + LBL_W, tapeY, cellW * 0.6, cellH);
    // 右端ハッシュ記号
    this._drawTapeHashmark(ctx, PAD + LBL_W + nVis * cellW, tapeY, cellW * 0.6, cellH);

    // セル
    for (let vi = 0; vi < nVis; vi++) {
      const idx    = head - half + vi;
      const cx     = PAD + LBL_W + vi * cellW;
      const inData = idx >= 0 && idx < cells.length;
      const isHead = (idx === head);

      if (!inData) {
        // 空白セル (ハッチング)
        ctx.fillStyle = "#0a0e18";
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
        ctx.strokeStyle = "#1e2a3a"; ctx.lineWidth = 0.5;
        ctx.strokeRect(cx + 0.5, tapeY + 0.5, cellW - 2, cellH - 1);
        ctx.save(); ctx.strokeStyle = "#1e3040"; ctx.lineWidth = 0.5;
        ctx.setLineDash([3, 4]);
        for (let hx = cx + 4; hx < cx + cellW - 2; hx += 5) {
          ctx.beginPath(); ctx.moveTo(hx, tapeY + 2);
          ctx.lineTo(hx - (cellH - 4) * 0.5, tapeY + cellH - 2); ctx.stroke();
        }
        ctx.restore();
      } else {
        // データセル
        ctx.fillStyle = "#1c2a3a";
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
        if (isHead) {
          ctx.save(); ctx.globalAlpha = 0.45;
          ctx.fillStyle = color;
          ctx.fillRect(cx, tapeY, cellW - 1, cellH);
          ctx.restore();
        }
        ctx.strokeStyle = isHead ? color : "#2a4060";
        ctx.lineWidth   = isHead ? 2 : 0.8;
        ctx.strokeRect(cx + 0.5, tapeY + 0.5, cellW - 2, cellH - 1);

        const fs = Math.max(8, Math.min(13, cellW * 0.42, cellH * 0.46));
        ctx.fillStyle    = "#ffffff";
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
    ctx.fillStyle = "#0a0e18";
    ctx.fillRect(x, tapeY, w - 1, cellH);
    ctx.strokeStyle = "#1e3040"; ctx.lineWidth = 0.5;
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
        ctx.strokeStyle = "#334455"; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(node.left);
      }
      if (node.right) {
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.right._x, node.right._y);
        ctx.strokeStyle = "#334455"; ctx.lineWidth = 1; ctx.stroke();
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
      ctx.fillStyle = "#0d1117"; ctx.fill();
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
        ctx.strokeStyle = "#2a4060"; ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(prevX, prevY);
        ctx.lineTo(prevX, rowY + rowH * 0.5);
        ctx.lineTo(rowX - 1, rowY + rowH * 0.5);
        ctx.stroke();
        // 矢印
        ctx.fillStyle = "#2a4060";
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
  _drawLinkedList(obj, areaY, areaH) {
    if (obj.is_vertical) { this._drawLinkedListV(obj, areaY, areaH); return; }
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
      ctx.fillStyle = "#445566";
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
      ctx.fillStyle = "#1c2a3a";
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
      ctx.fillStyle    = hlColor || "#ddd";
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
      ctx.strokeStyle = "#3a5060";
      ctx.lineWidth   = 1.5;
      ctx.beginPath(); ctx.moveTo(ax1, midY); ctx.lineTo(ax2 - 8, midY); ctx.stroke();
      ctx.fillStyle    = "#3a5060";
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

    const drawPtr = (nodeIdx, color, lbl) => {
      const px = nodeXs[nodeIdx] + NODE_W / 2;
      ctx.font = "bold 10px monospace";
      const tw = ctx.measureText(lbl).width;
      const bw = tw + 8, br = 3;
      // バッジ背景
      ctx.save(); ctx.globalAlpha = 0.92; ctx.fillStyle = color;
      this._rrect(ctx, px - bw/2, badgeTop, bw, BADGE_H, br); ctx.fill();
      ctx.restore();
      // バッジテキスト
      ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
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

    drawPtr(0, ptr_colors[0], ptr_labels[0]);
    if (n > 1) drawPtr(n - 1, ptr_colors[1], ptr_labels[1]);

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // linked_list (vertical) – 縦方向連結リスト（BOTTOM 固定・上積み）
  // nodes[0] = top（上）、nodes[n-1] = bottom（下・固定）
  // ════════════════════════════════════════════════════════════════════
  _drawLinkedListV(obj, areaY, areaH) {
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
    const cw  = this.cw;
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
    ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(botLbl, midX, bottomLineY + 4 + botBh/2);
    ctx.textBaseline = "alphabetic";

    if (n === 0) {
      ctx.fillStyle = "#445566"; ctx.font = "12px monospace";
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
      ctx.strokeStyle = "#3a5060"; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(midX, lastBottom); ctx.lineTo(midX, nullY); ctx.stroke();
      ctx.fillStyle = "#3a5060"; ctx.font = "bold 10px monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("null", midX, nullY + NULL_H / 2);
      ctx.textBaseline = "alphabetic";
    }

    // ── 各ノード描画 ─────────────────────────────────────────────
    for (let i = 0; i < n; i++) {
      const ny      = nodeYs[i];
      const hlColor = highlights[String(i)];

      ctx.fillStyle = "#1c2a3a";
      this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.fill();
      if (hlColor) {
        ctx.save(); ctx.globalAlpha = 0.25; ctx.fillStyle = hlColor;
        this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.fill(); ctx.restore();
      }
      ctx.strokeStyle = hlColor || "#4472C4";
      ctx.lineWidth   = hlColor ? 2.5 : 1.5;
      this._rrect(ctx, nodeX, ny, NODE_W, NODE_H, CORNER); ctx.stroke();

      ctx.fillStyle = hlColor || "#ddd";
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
      ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(topLbl, ptrX1 - bw/2 - 2, topMidY);
      ctx.textBaseline = "alphabetic";
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // stack_v – 縦方向配列スタック（Bottom 固定・上に積む）
  // ════════════════════════════════════════════════════════════════════
  _drawStackV(obj, areaY, areaH) {
    const { values = [], top = -1, label = "", highlights = {}, max_size } = obj;
    const n   = (max_size !== undefined) ? max_size : values.length;
    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_IDX = 26;   // インデックス表示幅（左）
    const PAD_PTR = 52;   // top ポインタ幅（右）
    const PAD_T   = label ? 22 : 8;
    const PAD_B   = 20;   // BOTTOM ラベル

    const availH  = areaH - PAD_T - PAD_B;
    const cellH   = Math.max(14, Math.min(38, availH / Math.max(n, 1)));
    const cellW   = Math.max(44, Math.min(110, cw - PAD_IDX - PAD_PTR - 16));
    const cellX   = PAD_IDX + (cw - PAD_IDX - PAD_PTR - cellW) / 2;
    const bottomY = areaY + areaH - PAD_B;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, 6, areaY + 14);
    }

    // BOTTOM ライン＋バッジ
    ctx.strokeStyle = "#4499dd"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cellX - 4, bottomY); ctx.lineTo(cellX + cellW + 4, bottomY); ctx.stroke();
    ctx.font = "bold 10px monospace";
    const botTw = ctx.measureText("BOTTOM").width;
    const botBw = botTw + 10, botBh = 14;
    ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = "#4499dd";
    this._rrect(ctx, cellX + cellW/2 - botBw/2, bottomY + 4, botBw, botBh, 3); ctx.fill(); ctx.restore();
    ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("BOTTOM", cellX + cellW / 2, bottomY + 4 + botBh/2);
    ctx.textBaseline = "alphabetic";

    for (let i = 0; i < n; i++) {
      const cellY   = bottomY - (i + 1) * cellH;
      const hasVal  = i <= top;
      const hlColor = highlights[String(i)];

      // 背景
      ctx.fillStyle = hasVal ? "#1c2a3a" : "#0a0e18";
      ctx.fillRect(cellX, cellY, cellW, cellH - 1);

      // ハイライト
      if (hlColor) {
        ctx.save(); ctx.globalAlpha = 0.28; ctx.fillStyle = hlColor;
        ctx.fillRect(cellX, cellY, cellW, cellH - 1); ctx.restore();
      }

      // 枠線
      ctx.strokeStyle = hlColor || (hasVal ? "#4472C4" : "#1e2833");
      ctx.lineWidth   = hlColor ? 2 : 0.8;
      ctx.strokeRect(cellX + 0.5, cellY + 0.5, cellW - 1, cellH - 2);

      // 値
      if (hasVal) {
        const fs = Math.max(9, Math.min(14, cellH * 0.50));
        ctx.fillStyle = hlColor || "#ddd";
        ctx.font = `bold ${fs}px monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), cellX + cellW / 2, cellY + cellH / 2);
        ctx.textBaseline = "alphabetic";
      }

      // インデックス（左）
      ctx.fillStyle = "#3a5570"; ctx.font = "9px monospace";
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
      ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("TOP", ax2 + bw/2, midY);
      ctx.textBaseline = "alphabetic";
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
      ctx.fillStyle = isAct ? "#1a2a3a" : "#080c14";
      ctx.fill();

      // ハイライト
      if (hlColor) {
        seg();
        ctx.save(); ctx.globalAlpha = 0.30; ctx.fillStyle = hlColor;
        ctx.fill(); ctx.restore();
      }

      // 枠線
      seg();
      ctx.strokeStyle = hlColor || (isAct ? "#4472C4" : "#1a2030");
      ctx.lineWidth   = hlColor ? 2 : 0.8;
      ctx.stroke();

      // 値テキスト（アクティブ or ハイライトのみ）
      if (isAct || hlColor) {
        const tx = cx + midR * Math.cos(midA);
        const ty = cy + midR * Math.sin(midA);
        const arcLen = midR * sliceA;
        const fs = Math.max(8, Math.min(13, arcLen * 0.40));
        ctx.fillStyle = hlColor || "#ddd";
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
    ctx.strokeStyle = "#2a3a50"; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(cx, cy, outerR, 0, 2 * Math.PI); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, innerR, 0, 2 * Math.PI); ctx.stroke();

    // 空キュー表示
    if (count === 0) {
      ctx.fillStyle = "#445566"; ctx.font = "11px monospace";
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

      ctx.fillStyle = "#0d1117"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
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
}
