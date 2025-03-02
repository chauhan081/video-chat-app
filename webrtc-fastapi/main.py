from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dictionary to manage active rooms and connected users
rooms = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """Handles WebSocket connections for a specific room."""
    await websocket.accept()
    
    # Add client to the room
    rooms.setdefault(room_id, set()).add(websocket)
    print(f"Client connected to Room: {room_id} | Total Users: {len(rooms[room_id])}")

    try:
        while True:
            data = await websocket.receive_text()
            await broadcast(room_id, data, websocket)
    
    except WebSocketDisconnect:
        print(f"Client disconnected from Room: {room_id}")
    
    except Exception as e:
        print(f"Error in Room {room_id}: {e}")

    finally:
        # Remove disconnected client safely
        rooms[room_id].discard(websocket)
        
        # If no clients are left, delete the room
        if not rooms[room_id]:  
            del rooms[room_id]
        print(f"Updated Room {room_id} Users: {len(rooms.get(room_id, []))}")

async def broadcast(room_id: str, message: str, sender: WebSocket):
    """Broadcasts a message to all clients in the room except the sender."""
    to_remove = set()
    
    for client in rooms.get(room_id, set()):
        if client != sender:
            try:
                await client.send_text(message)
            except WebSocketDisconnect:
                to_remove.add(client)  # Mark for removal

    # Remove disconnected clients safely
    for client in to_remove:
        rooms[room_id].discard(client)

