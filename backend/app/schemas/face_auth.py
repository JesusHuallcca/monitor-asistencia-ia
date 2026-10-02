from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field

Imagen = Annotated[str, Field(min_length=100, max_length=2_000_000)]


class EnrolarRostro(BaseModel):
    consentimiento: bool
    imagenes: list[Imagen] = Field(min_length=3, max_length=5)


class FaceLogin(BaseModel):
    identificador: str = Field(min_length=3, max_length=120)
    imagen: Imagen


class EstadoRostro(BaseModel):
    activo: bool
    retener_hasta: date | None = None