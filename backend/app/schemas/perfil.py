import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class PerfilOut(BaseModel):
    id: int
    username: str
    email: str
    nombres: str
    apellidos: str
    rol: str
    estado: str
    tiene_login_facial: bool
    telefono: str | None = None
    especialidad: str | None = None
    codigo: str | None = None
    carrera: str | None = None
    ciclo: int | None = None
    ultimo_login: datetime | None = None
    creado_en: datetime | None = None


class PerfilActualizar(BaseModel):
    nombres: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=20, pattern=r"^[0-9+\-\s()]*$")
    especialidad: str | None = Field(default=None, max_length=120)


class CambiarPassword(BaseModel):
    actual: str = Field(min_length=1, max_length=128)
    nueva: str = Field(min_length=8, max_length=128)

    @field_validator("nueva")
    @classmethod
    def validar_nueva(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe tener letras y números")
        return v