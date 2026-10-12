import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserDB
from app.schemas import UserRegister, UserLogin, VerifyTokenRequest, NewPassword, ForgotPwdEmail
from app.dependencies import get_current_user, gen_token, SECRET_KEY, ALGORITHM
from app.services.email import send_verify_email, send_forgot_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
hash = PasswordHash.recommended()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User Exist")
    
    new_user = UserDB(
        username = user.username,
        email = user.email,
        password_hash = hash.hash(user.password) 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User Created", "user_id": new_user.id}

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()
    if not user or not hash.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Data")
    
    expire = datetime.now(timezone.utc) + timedelta(hours=1) 

    token = jwt.encode({"sub": str(user.id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/emailer", status_code=status.HTTP_200_OK)
def emailer(background_tasks: BackgroundTasks, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is Verified")

    token = gen_token()

    background_tasks.add_task(send_verify_email, current_user.email, token)

    current_user.otp_code = token
    current_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=20)
    db.commit()

    return {"message": "Check you email for verification"}

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(payload: VerifyTokenRequest, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verified Users")

    if not current_user.otp_code or current_user.otp_code != payload.token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token")

    if current_user.otp_expires_at:
        expires_at = current_user.otp_expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Token has expired"
            )

    current_user.is_verified = True
    current_user.otp_code = None
    current_user.otp_expires_at = None
    db.commit()

    return{"message": "Account Verified"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(background_task: BackgroundTasks, credentials: ForgotPwdEmail, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

    if user:
        expire = datetime.now(timezone.utc) + timedelta(minutes=20) 
        token = jwt.encode({"sub": str(user.email), "exp": expire, "scope": "password_reset"}, SECRET_KEY, algorithm=ALGORITHM)
        background_task.add_task(send_forgot_password, credentials.email, token)

    return{"message": "Check email for reset password link. Make sure you input the correct and active email."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(newpass: NewPassword, token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("scope") != "password_reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    user.password_hash = hash.hash(newpass.password)
    db.commit()

    return{"message": "Pasword Successfully Changed"}
