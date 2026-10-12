from pydantic import BaseModel, EmailStr, HttpUrl

class BookmarkPOST(BaseModel):
    title: str
    url: HttpUrl
    tag: str

class BookmarkPATCH(BaseModel):
    title: str | None = None
    url: HttpUrl | None = None
    tag: str | None = None

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyTokenRequest(BaseModel):
    token: str

class NewPassword(BaseModel):
    password: str

class ForgotPwdEmail(BaseModel):
    email: EmailStr