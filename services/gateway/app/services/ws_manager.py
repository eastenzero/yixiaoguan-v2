from fastapi import WebSocket
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    管理 WebSocket 连接。

    两层映射：
    1. user_connections: user_id → set[WebSocket]
       用于向特定用户推送（如工单通知）
    2. room_connections: room_id → set[WebSocket]
       用于向会话房间广播（如新消息、状态变更）
       room_id 格式: "conv:{conversation_id}"
    """

    def __init__(self):
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        self.ws_user_map: Dict[WebSocket, int] = {}  # 反向映射

    async def connect(self, ws: WebSocket, user_id: int):
        """接受连接并注册"""
        await ws.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(ws)
        self.ws_user_map[ws] = user_id
        logger.info(f"WS connected: user={user_id}, total={self.total_connections}")

    def disconnect(self, ws: WebSocket):
        """断开并清理"""
        user_id = self.ws_user_map.pop(ws, None)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(ws)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        # 从所有房间移除
        for room_id in list(self.room_connections.keys()):
            self.room_connections[room_id].discard(ws)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        logger.info(f"WS disconnected: user={user_id}")

    def join_room(self, ws: WebSocket, room_id: str):
        """加入房间"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(ws)

    def leave_room(self, ws: WebSocket, room_id: str):
        """离开房间"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(ws)

    async def send_to_user(self, user_id: int, message: dict):
        """向指定用户的所有连接发送消息"""
        if user_id in self.user_connections:
            dead = []
            for ws in self.user_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws)

    async def broadcast_to_room(self, room_id: str, message: dict):
        """向房间内所有连接广播"""
        if room_id in self.room_connections:
            dead = []
            for ws in self.room_connections[room_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws)

    async def broadcast_to_college_teachers(
        self,
        college_id: int,
        teacher_ids: list[int],
        message: dict,
    ):
        """向学院内所有在线教师广播（如新工单通知）"""
        for tid in teacher_ids:
            await self.send_to_user(tid, message)

    @property
    def total_connections(self) -> int:
        return len(self.ws_user_map)


# 全局单例
manager = ConnectionManager()
