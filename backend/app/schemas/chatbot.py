from pydantic import BaseModel, Field, ConfigDict
class ChatMessage(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    message: str = Field(min_length=1,max_length=2000)
    course_id: int | None = Field(default=None,gt=0)
    student_id: int | None = Field(default=None,gt=0)
    source: str = Field(default='text',pattern='^(text|voice)$')
