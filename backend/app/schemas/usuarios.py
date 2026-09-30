import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioBase(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombres: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe tener letras y números")
        return v


class UsuarioCrear(UsuarioBase):
    rol: Literal["admin", "profesor", "estudiante"]
    codigo: str | None = Field(default=None, max_length=20)         # solo estudiantes
    carrera: str | None = Field(default=None, max_length=120)       # solo estudiantes
    ciclo: int | None = Field(default=None, ge=1, le=12)            # solo estudiantes
    especialidad: str | None = Field(default=None, max_length=120)  # solo profesores


class RegistroProfesor(UsuarioBase):
    especialidad: str | None = Field(default=None, max_length=120)


class CambiarEstado(BaseModel):
    estado: Literal["activo", "inactivo", "pendiente"]


class UsuarioListado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    nombres: str
    apellidos: str
    rol: str
    estado: str