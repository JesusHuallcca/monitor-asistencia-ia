from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identificador: str = Field(min_length=3, max_length=120, description="Usuario o correo")
    password: str = Field(min_length=1, max_length=128)
    recordarme: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    nombres: str
    apellidos: str
    rol: str
    estado: str
    tiene_login_facial: bool