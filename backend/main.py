from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from db_async.commands import get_user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_methods=["*"],  # Разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

@app.get("/users/{username}", response_model=dict)
async def read_user(username: str):
    user = await get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "lastname": user.lastname,
        "post": user.post,
        "email": user.email,
        "phone_number": user.phone_number,
        "status": user.status,
        "last_check": user.last_check,
    }