from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List

app = FastAPI()

# 연결된 클라이언트 관리 클래스
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.usernames = set()

    async def connect(self, websocket: WebSocket, username: str):
        if username in self.usernames:
            await websocket.close(code=1000, reason="Username already taken.")
            raise HTTPException(status_code=400, detail="Username already taken.")
        await websocket.accept()
        self.active_connections.append((websocket, username))
        self.usernames.add(username)

    def disconnect(self, websocket: WebSocket):
        for connection, username in self.active_connections:
            if connection == websocket:
                self.active_connections.remove((websocket, username))
                self.usernames.remove(username)
                break

    async def broadcast(self, message: str):
        for connection, _ in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat Service! Use /ws for WebSocket connections."}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    try:
        await manager.connect(websocket, username)
        await manager.broadcast(f"{username} has joined the chat!")
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(f"{username}: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            await manager.broadcast(f"{username} has left the chat.")
    except HTTPException as e:
        print(e.detail)
