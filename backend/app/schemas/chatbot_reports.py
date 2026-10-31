from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ReportType(str, Enum):
    ASISTENCIA="asistencia"
    TARDANZAS="tardanzas"
    AUSENCIAS="ausencias"
    ACADEMICO="academico"
    COMPARACION="comparacion"

class ReportSpec(BaseModel):
    model_config=ConfigDict(extra="forbid")
    report_type:ReportType=ReportType.ASISTENCIA
    course_id:int|None=Field(default=None,gt=0)
    student_id:int|None=Field(default=None,gt=0)
    period_start:date
    period_end:date
    compare_start:date|None=None
    compare_end:date|None=None

    @model_validator(mode="after")
    def periods(self):
        pairs=[(self.period_start,self.period_end)]
        if (self.compare_start is None)!=(self.compare_end is None):raise ValueError("Indica ambos límites de comparación.")
        if self.report_type==ReportType.COMPARACION:
            if self.compare_start is None:raise ValueError("Indica dos períodos para comparar.")
            pairs.append((self.compare_start,self.compare_end))
            if not (self.period_end<self.compare_start or self.compare_end<self.period_start):raise ValueError("Los períodos de comparación no deben superponerse.")
        elif self.compare_start is not None:raise ValueError("Solo comparación admite un segundo período.")
        if any(end<start for start,end in pairs) or (max(end for _,end in pairs)-min(start for start,_ in pairs)).days>365:
            raise ValueError("El rango total debe estar ordenado y no superar 366 días inclusivos.")
        return self
