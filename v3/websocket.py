from fastapi import WebSocket
from typing import Dict, List, Optional
import asyncio

class ConnectionManager:
    def __init__(self):
        # Store connections by store_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connections interested in all updates
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, store_id: Optional[int] = None):
        await websocket.accept()
        if store_id:
            if store_id not in self.active_connections:
                self.active_connections[store_id] = []
            self.active_connections[store_id].append(websocket)
        else:
            self.global_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, store_id: Optional[int] = None):
        if store_id and store_id in self.active_connections:
            if websocket in self.active_connections[store_id]:
                self.active_connections[store_id].remove(websocket)
        elif websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def broadcast_to_store(self, store_id: int, message: dict):
        # Send message to all clients watching this store
        if store_id in self.active_connections:
            for connection in self.active_connections[store_id]:
                await connection.send_json(message)
        
        # Also send to global watchers
        for connection in self.global_connections:
            await connection.send_json(message)

    async def broadcast_global(self, message: dict):
        # Send to all connected clients
        for connection in self.global_connections:
            await connection.send_json(message)

# Create a single instance to be imported by other modules
manager = ConnectionManager()