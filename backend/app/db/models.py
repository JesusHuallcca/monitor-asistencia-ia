from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer,
    LargeBinary, String, Text, func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    rol = Column(String(20), nullable=False)      # superadmin | admin | profesor | estudiante
    estado = Column(String(20), nullable=False, default="activo")  # pendiente | activo | inactivo
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profesor = relationship("Profesor", back_populates="usuario", uselist=False)
    estudiante = relationship("Estudiante", back_populates="usuario", uselist=False)
    rostro = relationship("Rostro", back_populates="usuario", uselist=False)


class Profesor(Base):
    __tablename__ = "profesores"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    especialidad = Column(String(120), nullable=True)
    telefono = Column(String(20), nullable=True)

    usuario = relationship("Usuario", back_populates="profesor")


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    carrera = Column(String(120), nullable=True)
    ciclo = Column(Integer, nullable=True)
    telefono = Column(String(20), nullable=True)

    usuario = relationship("Usuario", back_populates="estudiante")


class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    periodo = Column(String(20), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, server_default=func.now())


class Rostro(Base):
    __tablename__ = "rostros"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    consentimiento = Column(Boolean, nullable=False, default=False)
    fecha_consentimiento = Column(DateTime, nullable=True)
    login_facial_activo = Column(Boolean, nullable=False, default=True)
    retener_hasta = Column(Date, nullable=True)
    registrado_en = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="rostro")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(BigInteger, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    accion = Column(String(60), nullable=False)
    detalle = Column(String(500), nullable=True)
    ip = Column(String(45), nullable=True)
    exito = Column(Boolean, nullable=False, default=True)
    fecha = Column(DateTime, server_default=func.now())

class AsignacionProfesor(Base):
    __tablename__ = "asignaciones_profesor"

    id = Column(Integer, primary_key=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    asignado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    asignado_en = Column(DateTime, server_default=func.now())


class Matricula(Base):
    __tablename__ = "matriculas"

    id = Column(Integer, primary_key=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    matriculado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    matriculado_en = Column(DateTime, server_default=func.now())