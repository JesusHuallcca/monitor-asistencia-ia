from datetime import date
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=2000)
    course_id: int | None = Field(default=None, gt=0)
    student_id: int | None = Field(default=None, gt=0)
    source: str = Field(default="text", pattern="^(text|voice)$")
    context_token: str | None = Field(default=None, min_length=1, max_length=4096)
    period_start: date | None = None
    period_end: date | None = None
    reset_context: bool = False

    @model_validator(mode="after")
    def period(self):
        if ("period_start" in self.model_fields_set) != ("period_end" in self.model_fields_set):
            raise ValueError("Envía ambos límites del período para cambiarlo o borrarlo.")
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("Indica inicio y fin del período.")
        if self.period_start and (self.period_end < self.period_start or (self.period_end-self.period_start).days > 366):
            raise ValueError("El período debe estar ordenado y no superar 367 días.")
        return self
