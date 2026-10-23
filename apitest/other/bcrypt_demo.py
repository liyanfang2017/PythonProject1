import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI(title="JWT + bcrypt Demo")

# 生产环境务必放到环境变量，不要硬编码
SECRET_KEY = "my-secret-key-keep-safe-2026-demo-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ========== bcrypt 用户密码哈希 ==========
def hash_password(raw_pwd: str) -> bytes:
    """密码加密，存入数据库"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_pwd.encode("utf-8"), salt)


def verify_password(raw_pwd: str, hashed_pwd: bytes) -> bool:
    """登录校验密码"""
    return bcrypt.checkpw(raw_pwd.encode("utf-8"), hashed_pwd)


# ========== PyJWT 生成&解析token ==========
def create_access_token(user_id: int, expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES):
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str):
    """解析token，过期/篡改会抛异常"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


# ---------------- FastAPI 鉴权依赖 ----------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="token无效或已过期")
    return user_id


# ---------------- 模拟数据库：内存用户 ----------------
mock_user_db = {
    1001: {
        "user_id": 1001,
        "username": "demo_user",
        "password_hash": hash_password("123456")
    }
}


# 登录接口，获取token；OAuth2PasswordRequestForm 会接收 form‑data username/password
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 这里把 form_data.username 当做 user_id 字符串
    try:
        user_id = int(form_data.username)
    except ValueError:
        raise HTTPException(status_code=401, detail="用户名密码错误")

    user = mock_user_db.get(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="用户名密码错误")

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名密码错误")

    access_token = create_access_token(user_id=user_id)
    return {"access_token": access_token, "token_type": "bearer"}


# 需要鉴权的接口
@app.get("/profile")
async def profile(user_id: int = Depends(get_current_user)):
    return {"user_id": user_id, "msg": "这是需要登录才能访问的个人资料"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bcrypt_demo:app", host="127.0.0.1", port=8000, reload=True)
