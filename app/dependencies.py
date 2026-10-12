import jwt, uuid, os, string, secrets
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models import UserDB
from app.database import get_db

load_dotenv()
try:
    SECRET_KEY = os.environ["SECRET_KEY"]
except KeyError:
    raise RuntimeError("SECRET_KEY is missing")
security = HTTPBearer()
ALGORITHM = "HS256"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> UserDB:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        user_uuid = uuid.UUID(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    user = db.query(UserDB).filter(UserDB.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def require_verification(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification required")
    return current_user

def gen_token(length=6):
    pool = string.ascii_uppercase + string.digits
    gen_token = ''.join(secrets.choice(pool) for _ in range(length))
    return gen_token