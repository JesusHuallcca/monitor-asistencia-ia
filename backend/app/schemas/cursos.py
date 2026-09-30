from pydantic import BaseModel, ConfigDict, Field


class CursoCrear(BaseModel):
    codigo: str = Field(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9-]+$")
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    periodo: str = Field(min_length=3, max_length=20)


class CursoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    periodo: str | None = Field(default=None, min_length=3, max_length=20)
    activo: bool | None = None


class CursoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: str | None
    periodo: str
    activo: bool


class AsignarUsuario(BaseModel):
    usuario_id: int


class PersonaCurso(BaseModel):
    usuario_id: int
    username: str
    nombres: str
    apellidos: str
    detalle: str | None = None  # código (alumno) o especialidad (profesor)