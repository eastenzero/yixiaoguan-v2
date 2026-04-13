from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.ws_manager import manager
from app.utils.jwt import decode_access_token
from jose import JWTError
import json, logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket 入口。
    连接时通过 query param 传 JWT 认证。

    上行消息格式:
    {"type": "join_room",     "data": {"conv_id": 123}}
    {"type": "leave_room",    "data": {"conv_id": 123}}
    {"type": "send_message",  "data": {"conv_id": 123, "content": "..."}}
    {"type": "typing",        "data": {"conv_id": 123}}
    {"type": "ping"}

    下行消息格式:
    {"type": "new_message",       "data": {...}}
    {"type": "status_changed",    "data": {...}}
    {"type": "escalation_notify", "data": {...}}
    {"type": "teacher_typing",    "data": {...}}
    {"type": "pong"}
    {"type": "error",             "data": {"message": "..."}}
    """
    # 1. 认证
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        user_role = payload.get("role", "student")
    except (JWTError, KeyError, ValueError):
        await ws.close(code=4001, reason="Invalid token")
        return

    # 2. 注册连接
    await manager.connect(ws, user_id)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
                continue

            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})

            elif msg_type == "join_room":
                conv_id = data.get("conv_id")
                if conv_id:
                    manager.join_room(ws, f"conv:{conv_id}")
                    await ws.send_json({
                        "type": "room_joined",
                        "data": {"conv_id": conv_id}
                    })

            elif msg_type == "leave_room":
                conv_id = data.get("conv_id")
                if conv_id:
                    manager.leave_room(ws, f"conv:{conv_id}")

            elif msg_type == "typing":
                conv_id = data.get("conv_id")
                if conv_id:
                    # 广播 typing 给房间内其他人
                    await manager.broadcast_to_room(
                        f"conv:{conv_id}",
                        {
                            "type": "teacher_typing" if user_role == "teacher" else "student_typing",
                            "data": {"conv_id": conv_id, "user_id": user_id}
                        }
                    )

            # send_message 通过 WS 发消息 — S2 阶段仅广播，不写库
            # 正式环境应通过 HTTP API 发消息（保证事务性），WS 只做通知
            # 这里做最小实现，后续 S3 完善
            elif msg_type == "send_message":
                conv_id = data.get("conv_id")
                content = data.get("content")
                if conv_id and content:
                    await manager.broadcast_to_room(
                        f"conv:{conv_id}",
                        {
                            "type": "new_message",
                            "data": {
                                "conv_id": conv_id,
                                "sender_id": user_id,
                                "sender_type": user_role,
                                "content": content,
                            }
                        }
                    )

            else:
                await ws.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown type: {msg_type}"}
                })

    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error(f"WS error for user {user_id}: {e}")
        manager.disconnect(ws)
