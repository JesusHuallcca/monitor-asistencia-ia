"""Snapshots y archivos en RAM: propiedad, revocación, TTL y límites por proceso."""
from collections import deque
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import logging
import secrets
import threading
import time
from fastapi import HTTPException

TTL=600
MAX_ENTRIES=32
MAX_BYTES=24*1024*1024
MAX_FILE_BYTES=8*1024*1024
logger=logging.getLogger("monitor.chatbot.exports")

def audit(event,fmt="none",actor=None):
    # Sin nombres, preguntas, identificadores de estudiantes o contenidos.
    from app.core.config import settings
    pseudonym=hmac.new(settings.JWT_SECRET_KEY.encode(),f"report-audit:{actor}".encode(),hashlib.sha256).hexdigest()[:16] if actor is not None else "none"
    logger.info("chatbot_report event=%s format=%s actor=%s",event,fmt,pseudonym)

class RateLimiter:
    def __init__(self,clock=time.monotonic):self.clock=clock;self.lock=threading.Lock();self.hits={}
    def check(self,uid,action,limit):
        now=self.clock()
        with self.lock:
            for key in list(self.hits):
                while self.hits[key] and self.hits[key][0]<=now-60:self.hits[key].popleft()
                if not self.hits[key]:del self.hits[key]
            key=(uid,action)
            if key not in self.hits and len(self.hits)>=2048:raise HTTPException(503,"Demasiadas cuentas activas; vuelve a intentar.")
            values=self.hits.setdefault(key,deque())
            if len(values)>=limit:
                audit("rate_rejected",actor=uid)
                raise HTTPException(429,"Límite de reportes/exportaciones alcanzado. Espera un minuto.",headers={"Retry-After":"60"})
            values.append(now)

@dataclass
class Entry:
    owner:int
    scope:str
    payload:str
    fingerprint:str
    expires:float
    files:dict=field(default_factory=dict)
    timer:object=None
    @property
    def size(self):return len(self.payload.encode())+sum(len(v) for v in self.files.values())
    def dataset(self):return json.loads(self.payload)

class ReportStore:
    def __init__(self,clock=time.monotonic,ttl=TTL):
        self.clock=clock;self.ttl=ttl;self.lock=threading.RLock();self.entries={};self.limiter=RateLimiter(clock)
    def purge(self):
        with self.lock:
            for key in list(self.entries):
                if self.entries[key].expires<=self.clock():self.remove(key)
    def remove(self,key):
        with self.lock:
            entry=self.entries.pop(key,None)
            if entry and entry.timer:entry.timer.cancel()
    def close(self):
        with self.lock:
            for key in list(self.entries):self.remove(key)
    def add(self,uid,scope,dataset):
        payload=json.dumps(dataset,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
        if len(payload.encode())>2*1024*1024:raise HTTPException(413,"El conjunto del reporte supera 2 MiB; reduce los filtros.")
        with self.lock:
            self.purge()
            if len(self.entries)>=MAX_ENTRIES or sum(e.size for e in self.entries.values())+len(payload.encode())>MAX_BYTES:
                raise HTTPException(503,"Capacidad temporal de reportes ocupada; espera o reduce los filtros.")
            key=secrets.token_urlsafe(24)
            entry=Entry(uid,scope,payload,hashlib.sha256(payload.encode()).hexdigest(),self.clock()+self.ttl)
            timer=threading.Timer(self.ttl,self.remove,args=(key,));timer.daemon=True;entry.timer=timer
            self.entries[key]=entry;timer.start()
            return key,entry
    def get(self,key,uid,scope):
        with self.lock:
            entry=self.entries.get(key)
            if entry is None or entry.owner!=uid:
                audit("access_rejected",actor=uid)
                raise HTTPException(404,"Reporte no disponible para esta cuenta o vencido.")
            if entry.expires<=self.clock():
                self.remove(key);raise HTTPException(410,"El reporte venció. Genera una nueva vista previa.")
            if entry.scope!=scope:
                self.remove(key);audit("scope_rejected",actor=uid)
                raise HTTPException(403,"Tus permisos cambiaron; genera un reporte autorizado nuevamente.")
            return entry
    def cache(self,key,entry,fmt,content):
        if len(content)>MAX_FILE_BYTES:raise HTTPException(413,"El archivo supera 8 MiB; reduce los filtros.")
        with self.lock:
            # Evitar reinsertar un snapshot vencido durante el renderizado.
            self.get(key,entry.owner,entry.scope)
            if fmt in entry.files:return
            if sum(e.size for e in self.entries.values())+len(content)>MAX_BYTES:raise HTTPException(503,"Capacidad temporal de exportación ocupada.")
            entry.files[fmt]=content

store=ReportStore()
render_slots=threading.BoundedSemaphore(2)
