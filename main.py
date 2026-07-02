"""
main.py – FastAPI + WebSocket バックエンド (ArrayAnimation)
起動: uvicorn main:app --reload --port 8004
"""

import asyncio
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from algorithms import AlgorithmList, DataSizeList

app = FastAPI(title="ArrayAnimation API")

# セッション管理: { session_id: { generator, speed, paused, stopped, ... } }
sessions: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.get("/api/algorithms")
def get_algorithms():
    return [
        {"id": i, "name": name, "meta": meta}
        for i, (name, fn, meta) in enumerate(AlgorithmList)
    ]


@app.get("/api/datasizes")
def get_datasizes():
    return DataSizeList


class StartParams(BaseModel):
    algorithm_id:   int
    num_items:      int   = 16
    speed:          float = 0.10      # 秒/フレーム
    target:         Optional[int] = None        # 探索対象 (search 用)
    data:           Optional[list[int]] = None  # 初期データ (search / sort 共用)
    data_condition: int   = 0         # 0=ランダム 1=昇順 2=降順 3=ほぼ昇順 (sort 用)
    seed:           Optional[int] = None        # 乱数シード (graph 等)
    init_data:      Optional[list[str]] = None  # ユーザー指定の初期データ (misc init_data 対応アルゴ用)
    ops:            Optional[list[str]] = None  # ユーザー指定の操作列 (misc ops 対応アルゴ用)
    sort_method:    Optional[str] = None        # ソート手法: "quick" | "shell" | "insert"
    traversal:      Optional[str] = None        # 走査種別: "bfs" | "preorder" | "inorder" | "postorder" | "all"
    rotation_pause: bool = False                 # 回転フレームで自動一時停止 (AVL木用)


@app.get("/api/preview")
def get_preview(algorithm_id: int, n: int = 16, seed: Optional[int] = None,
                init_data: Optional[str] = None, ops: Optional[str] = None,
                sort_method: Optional[str] = None, traversal: Optional[str] = None):
    """ジェネレータの第1フレームだけ返す（実行前プレビュー用）"""
    if algorithm_id not in range(len(AlgorithmList)):
        return JSONResponse({"error": "invalid algorithm_id"}, status_code=400)
    algo_name, algo_fn, algo_meta = AlgorithmList[algorithm_id]
    try:
        kw: dict = {"seed": seed, "sort_method": sort_method, "traversal": traversal}
        if init_data:
            import re as _re
            stripped = init_data.strip()
            try:
                # まず整数リストとして解釈を試みる
                parsed = [int(x) for x in _re.split(r"[,\s]+", stripped) if x]
                kw["init_data"] = [str(v) for v in parsed]
            except ValueError:
                # 整数でなければ式/トークン列として扱う
                # 空白・コンマで分割してトークン配列に変換
                # B型式: "(2 + 3)*(8-1)" → ["(2", "+", "3)*(8-1)"] → algo側で join
                # A型式: "2 3 + 8 1 - *" → ["2","3","+","8","1","-","*"]
                tokens = [x for x in _re.split(r"[,\s]+", stripped) if x]
                if tokens:
                    kw["init_data"] = tokens
        if ops:
            # 改行またはセミコロン区切りの操作列文字列をリストに変換
            import re as _re
            op_list = [s.strip() for s in _re.split(r"[\n;]+", ops.strip()) if s.strip()]
            if op_list:
                kw["ops"] = op_list
        gen = algo_fn(n, **kw)
        frame = next(gen)
        return frame
    except StopIteration:
        return JSONResponse({"error": "no frames"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/start")
def start_session(params: StartParams):
    if params.algorithm_id not in range(len(AlgorithmList)):
        return JSONResponse({"error": "invalid algorithm_id"}, status_code=400)

    algo_name, algo_fn, algo_meta = AlgorithmList[params.algorithm_id]
    algo_type = algo_meta.get("type", "search")

    if algo_type == "misc":
        kw = {"seed": params.seed}
        if params.init_data:
            kw["init_data"] = params.init_data
        if params.ops:
            kw["ops"] = params.ops
        if params.sort_method:
            kw["sort_method"] = params.sort_method
        if params.traversal:
            kw["traversal"] = params.traversal
        generator = algo_fn(params.num_items, **kw)
    elif algo_type == "sort":
        # sort: data_condition と data を渡す (target は不要)
        generator = algo_fn(
            params.num_items,
            data_condition=params.data_condition,
            data=params.data,
        )
    else:
        # search: target と data を渡す
        generator = algo_fn(params.num_items, params.target, params.data)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "generator":      generator,
        "speed":          params.speed,
        "paused":         False,
        "stopped":        False,
        "algo_name":      algo_name,
        "num_items":      params.num_items,
        "rotation_pause": params.rotation_pause,
    }
    return {
        "session_id": session_id,
        "algo_name":  algo_name,
        "num_items":  params.num_items,
    }


# ---------------------------------------------------------------------------
# WebSocket  /ws/{session_id}
# クライアントからの制御メッセージ:
#   {"action": "set_speed", "speed": 0.05}
#   {"action": "pause"}
#   {"action": "resume"}
#   {"action": "stop"}
# ---------------------------------------------------------------------------

@app.websocket("/ws/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()

    if session_id not in sessions:
        await ws.send_json({"error": "session not found"})
        await ws.close()
        return

    session = sessions[session_id]

    async def send_frames():
        try:
            for frame in session["generator"]:
                if session["stopped"]:
                    break
                while session["paused"] and not session["stopped"]:
                    await asyncio.sleep(0.05)
                if session["stopped"]:
                    break
                await ws.send_json(frame)
                # 回転で自動停止: クライアントの pause 往復を待たず、
                # 送信直後にサーバー側で即座に一時停止する（往復遅延によるフレームずれを防止）
                if (session.get("rotation_pause") and not frame.get("finished")
                        and any(isinstance(o, dict) and o.get("rotation")
                                for o in (frame.get("objects") or []))):
                    session["paused"] = True
                await asyncio.sleep(session["speed"])
        except Exception:
            pass

    async def recv_controls():
        try:
            while True:
                msg = await ws.receive_json()
                action = msg.get("action", "")
                if action == "set_speed":
                    session["speed"] = float(msg.get("speed", 0.08))
                elif action == "pause":
                    session["paused"] = True
                elif action == "resume":
                    session["paused"] = False
                elif action == "stop":
                    session["stopped"] = True
                    break
        except WebSocketDisconnect:
            session["stopped"] = True
        except Exception:
            session["stopped"] = True

    sender   = asyncio.create_task(send_frames())
    receiver = asyncio.create_task(recv_controls())

    done, pending = await asyncio.wait(
        [sender, receiver],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
        t.cancel()

    sessions.pop(session_id, None)
    try:
        await ws.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 静的ファイル
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
