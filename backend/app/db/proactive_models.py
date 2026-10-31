"""Metadatos AISLADOS: app.main no crea estas tablas. Migración explícita aparte."""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import declarative_base
ProactiveBase=declarative_base()

class ProactiveAction(ProactiveBase):
    __tablename__="chatbot_proactive_actions"
    id=Column(String(36),primary_key=True)
    owner_id=Column(Integer,nullable=False,index=True)
    recipient_id=Column(Integer,nullable=False)
    kind=Column(String(32),nullable=False)
    course_id=Column(Integer)
    student_id=Column(Integer)
    source_id=Column(Integer)
    config_json=Column(Text,nullable=False)
    timezone=Column(String(64),nullable=False)
    frequency=Column(String(12),nullable=False)
    status=Column(String(16),nullable=False)
    next_run=Column(DateTime,index=True)
    last_run=Column(DateTime)
    last_signature=Column(String(64))
    version=Column(Integer,nullable=False,default=1)
    scope_key=Column(String(64),nullable=False)
    identity=Column(String(64),nullable=False,unique=True)
    created_at=Column(DateTime,nullable=False)
    updated_at=Column(DateTime,nullable=False)
    Index("ix_proactive_due","status","next_run")

class ProactiveNotification(ProactiveBase):
    __tablename__="chatbot_proactive_notifications"
    id=Column(String(36),primary_key=True)
    action_id=Column(String(36),nullable=False,index=True)
    owner_id=Column(Integer,nullable=False,index=True)
    execution_key=Column(String(64),nullable=False,unique=True)
    scheduled_for=Column(DateTime,nullable=False)
    title=Column(String(180),nullable=False)
    message=Column(Text,nullable=False)
    data_json=Column(Text,nullable=False)
    scope_key=Column(String(64),nullable=False)
    state=Column(String(16),nullable=False,default="unread")
    created_at=Column(DateTime,nullable=False)
    expires_at=Column(DateTime,nullable=False)

class ProactivePreference(ProactiveBase):
    __tablename__="chatbot_proactive_preferences"
    owner_id=Column(Integer,primary_key=True)
    enabled=Column(Boolean,nullable=False,default=True)
    timezone=Column(String(64),nullable=False,default="America/Lima")
    updated_at=Column(DateTime,nullable=False)

class ProactiveAudit(ProactiveBase):
    __tablename__="chatbot_proactive_audit"
    id=Column(Integer,primary_key=True,autoincrement=True)
    owner_id=Column(Integer,nullable=False,index=True)
    action_id=Column(String(36))
    event=Column(String(40),nullable=False)
    created_at=Column(DateTime,nullable=False)

class ProactiveWorkerState(ProactiveBase):
    __tablename__="chatbot_proactive_worker"
    id=Column(String(16),primary_key=True)
    last_seen=Column(DateTime,nullable=False)
