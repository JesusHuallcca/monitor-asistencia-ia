"""Bounded, process-local volatile jobs. No facial payloads reach disk or logs."""
from dataclasses import dataclass
import multiprocessing
import threading
import time
from uuid import uuid4

from app.services.expression_worker import infer_expression


@dataclass
class Job:
    owner: int
    revision: str
    deadline: float
    frame: object
    status: str = 'QUEUED'
    result: dict | None = None


class ExpressionService:
    def __init__(self, consent_reader, *, enabled=False, model_path='', capacity=4,
                 job_ttl=10.0, result_ttl=30.0, max_results=32,
                 clock=time.monotonic, target=infer_expression):
        if capacity < 1 or job_ttl <= 0 or result_ttl <= 0 or max_results < capacity:
            raise ValueError('Límites EmoScan inválidos')
        self.consent_reader = consent_reader
        self.enabled = enabled
        self.model_path = model_path
        self.capacity = capacity
        self.job_ttl = job_ttl
        self.result_ttl = result_ttl
        self.max_results = max_results
        self.clock = clock
        self.target = target
        self.jobs = {}
        self.lock = threading.Lock()
        self.wakeup = threading.Event()
        self.closed = threading.Event()
        self.thread = None
        self.cleaner = None

    def _revision(self, owner):
        try:
            return self.consent_reader(owner)
        except Exception:
            return None  # Missing table / database failure: no processing.

    def _purge(self):
        for key, job in list(self.jobs.items()):
            if self.clock() >= job.deadline:
                job.frame = None
                job.result = None
                del self.jobs[key]

    def submit(self, owner, frame):
        if not self.enabled or self.closed.is_set():
            return {'status': 'DISABLED'}
        revision = self._revision(owner)
        if not revision:
            return {'status': 'NO_CONSENT'}
        # The existing frontend sends 640x480. Bound any extra retained RAM.
        if (frame is None or frame.ndim != 3 or frame.shape[2] != 3
                or str(frame.dtype) != 'uint8' or frame.size > 1280*1280*3):
            return {'status': 'UNAVAILABLE'}
        with self.lock:
            self._purge()
            if any(job.owner == owner and job.status in ('QUEUED', 'RUNNING')
                   for job in self.jobs.values()):
                return {'status': 'BUSY'}
            if (sum(job.status in ('QUEUED', 'RUNNING') for job in self.jobs.values()) >= self.capacity
                    or len(self.jobs) >= self.max_results):
                return {'status': 'BUSY'}
            job_id = uuid4().hex
            self.jobs[job_id] = Job(owner, revision, self.clock() + self.job_ttl, frame.copy())
            if self.thread is None:
                self.cleaner = threading.Thread(target=self._sweep, name='emoscan-expiry', daemon=True)
                self.cleaner.start()
                self.thread = threading.Thread(target=self._loop, name='emoscan', daemon=True)
                self.thread.start()
        self.wakeup.set()
        return {'status': 'QUEUED', 'job_id': job_id, 'expires_in': self.job_ttl}

    def revoke(self, owner):
        with self.lock:
            for key, job in list(self.jobs.items()):
                if job.owner == owner:
                    job.frame = None
                    job.result = None
                    del self.jobs[key]
        self.wakeup.set()

    def get(self, owner, job_id):
        revision = self._revision(owner)
        with self.lock:
            self._purge()
            job = self.jobs.get(job_id)
            if job is None or job.owner != owner:
                return None
            if not revision or revision != job.revision:
                job.frame = None
                job.result = None
                del self.jobs[job_id]
                return None
            return {**(job.result or {'status': job.status}),
                    'expires_in': max(0, job.deadline - self.clock())}

    def _alive(self, key, job):
        with self.lock:
            self._purge()
            return not self.closed.is_set() and self.jobs.get(key) is job

    def _allowed(self, key, job):
        if not self._alive(key, job):
            return False
        revision = self._revision(job.owner)
        return self._alive(key, job) and revision is not None and revision == job.revision

    def _finish(self, key, job, result):
        if not self._allowed(key, job):
            self._discard(key, job)
            return
        with self.lock:
            if self.jobs.get(key) is job:
                job.frame = None
                job.result = result
                job.status = result['status']
                job.deadline = self.clock() + self.result_ttl

    def _discard(self, key, job):
        with self.lock:
            if self.jobs.get(key) is job:
                del self.jobs[key]
            job.frame = None
            job.result = None

    def _run(self, key, job):
        if not self._allowed(key, job):
            self._discard(key, job)
            return

        class LocalConnection:
            def __init__(self):
                self.result = {'status': 'UNAVAILABLE'}
            def send(self, val):
                self.result = val
            def close(self):
                pass

        conn = LocalConnection()
        result = None
        try:
            self.target(conn, job.frame, self.model_path)
            result = conn.result
        except Exception:
            import traceback
            traceback.print_exc()
            result = {'status': 'UNAVAILABLE'}
        finally:
            job.frame = None

        if result is not None:
            self._finish(key, job, result)

    def _sweep(self):
        # Expire RAM even if a consent query or process startup is slow.
        while not self.closed.wait(0.1):
            with self.lock:
                self._purge()

    def _loop(self):
        while not self.closed.is_set():
            with self.lock:
                self._purge()
                next_job = next(((key, job) for key, job in self.jobs.items()
                                 if job.status == 'QUEUED'), None)
                if next_job:
                    next_job[1].status = 'RUNNING'
            if next_job:
                try:
                    self._run(*next_job)
                except Exception:
                    self._finish(*next_job, {'status': 'UNAVAILABLE'})
            else:
                self.wakeup.wait(0.1)
                self.wakeup.clear()

    def close(self):
        self.closed.set()
        self.wakeup.set()
        with self.lock:
            for job in self.jobs.values():
                job.frame = None
                job.result = None
            self.jobs.clear()
        if self.thread is not None:
            self.thread.join(timeout=3)
        if self.cleaner is not None:
            self.cleaner.join(timeout=1)


def create_service():
    from app.core.config import settings
    from app.db.expression_consent import current_revision
    return ExpressionService(
        current_revision, enabled=settings.EMOSCAN_ENABLED, model_path=settings.EMOSCAN_MODEL_PATH,
        capacity=settings.EMOSCAN_QUEUE_SIZE, job_ttl=settings.EMOSCAN_JOB_TTL_SECONDS,
        result_ttl=settings.EMOSCAN_RESULT_TTL_SECONDS, max_results=settings.EMOSCAN_MAX_RESULTS)


expression_service = create_service()


def after_attendance(result, owner, frame):
    """Called only AFTER register() has committed. Optional failures never escape."""
    if result.get('status') != 'REGISTERED' or not result.get('success'):
        return result
    try:
        expression = expression_service.submit(owner, frame)
    except Exception:
        expression = {'status': 'UNAVAILABLE'}
    return {**result, 'expression_analysis': expression}
