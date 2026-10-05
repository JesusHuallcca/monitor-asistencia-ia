from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Float,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    Time,
    func,
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
    rol = Column(String(20), nullable=False)
    estado = Column(String(20), nullable=False, default="activo")
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profesor = relationship("Profesor", back_populates="usuario", uselist=False)
    estudiante = relationship("Estudiante", back_populates="usuario", uselist=False)
    rostro = relationship("Rostro", back_populates="usuario", uselist=False)
    asistencias = relationship("Asistencia", back_populates="usuario")


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


class SesionClase(Base):
    __tablename__ = "sesiones_clase"

    id = Column(Integer, primary_key=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    tolerancia_minutos = Column(Integer, nullable=False, default=10)
    estado = Column(String(20), nullable=False, default="ACTIVA")
    fecha_registro = Column(DateTime, server_default=func.now())

    curso = relationship("Curso")
    asistencias = relationship("Asistencia", back_populates="sesion")


class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(BigInteger, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    sesion_id = Column(Integer, ForeignKey("sesiones_clase.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    confianza = Column(Numeric(10, 6), nullable=False)
    liveness_score = Column(Numeric(10, 6), nullable=False)
    estado = Column(String(30), nullable=False, default="PRESENTE")
    fecha_registro = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario", back_populates="asistencias")
    sesion = relationship("SesionClase", back_populates="asistencias")


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


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    peso = Column(Numeric(5, 2), nullable=False, default=0)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime, server_default=func.now())


class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True)
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    nota = Column(Numeric(4, 2), nullable=True)
    estado = Column(String(20), nullable=False, default="pendiente")
    registrada_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    registrada_en = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
class Prediccion(Base):
    __tablename__ = "predicciones"

    id_prediccion = Column(Integer, primary_key=True)
    id_estudiante = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    prob_falta = Column(Float)
    prob_tardanza = Column(Float)
    fecha = Column(Date, nullable=False)
    modelo_version = Column(String(100), nullable=False)


class Metrica(Base):
    __tablename__ = "metricas_modelo"

    id_metrica = Column(Integer, primary_key=True)
    modelo = Column(String(100))
    version = Column(String(100))
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)


class ChatHistorial(Base):
    __tablename__ = "chat_historial"

    id_mensaje = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    fecha_hora = Column(DateTime, nullable=False)