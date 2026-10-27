"""Cola personal aislada que reutiliza ExpressionService y el mismo FERPlus ONNX."""
from app.core.config import settings
from app.db.personal_expression_consent import current_revision
from app.services.expression_service import ExpressionService

personal_service = ExpressionService(
    current_revision, enabled=settings.EMOSCAN_ENABLED, model_path=settings.EMOSCAN_MODEL_PATH,
    capacity=settings.EMOSCAN_QUEUE_SIZE, job_ttl=settings.EMOSCAN_JOB_TTL_SECONDS,
    result_ttl=settings.EMOSCAN_RESULT_TTL_SECONDS, max_results=settings.EMOSCAN_MAX_RESULTS,
)
