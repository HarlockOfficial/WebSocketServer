import asyncio

from fastapi import FastAPI
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedError

app = FastAPI()
queue = asyncio.Queue()
is_sender_connected = False
is_receiver_connected = False

@app.get("/")
async def root():
    return {"status": "ok", "is_sender_connected": is_sender_connected, "is_receiver_connected": is_receiver_connected}


@app.websocket("/ws/send")
async def send(websocket: WebSocket):
    global is_sender_connected
    await websocket.accept()
    is_sender_connected = True
    try:
        while True:
            payload_to_be_produced = await websocket.receive_text()
            if is_receiver_connected:
                await queue.put(payload_to_be_produced)
            await websocket.send_text(payload_to_be_produced)
    except WebSocketDisconnect:
        is_sender_connected = False
        await websocket.close()

@app.websocket("/ws/receive")
async def receive(websocket: WebSocket):
    global is_receiver_connected
    await websocket.accept()
    is_receiver_connected = True
    try:
        while True:
            payload_to_be_consumed = await queue.get()
            await websocket.send_text(payload_to_be_consumed)
            queue.task_done()
    except (WebSocketDisconnect, ConnectionClosedError):
        is_receiver_connected = False
        await websocket.close()
