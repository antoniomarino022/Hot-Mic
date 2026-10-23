from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import TriageCategory


class ReportCreateRequest(BaseModel):
    """Richiesta di segnalazione di un post da parte di un utente."""
    reason: TriageCategory = Field(
        ...,
        description="Motivo della segnalazione (es. self_harm, violence, abuse, doxxing, etc.)",
    )
    details: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Eventuali dettagli aggiuntivi opzionali forniti dall'utente",
    )

    @field_validator("reason")
    @classmethod
    def cannot_report_as_ok(cls, v: TriageCategory) -> TriageCategory:
        if v == TriageCategory.OK:
            raise ValueError("Non è possibile inviare una segnalazione con categoria 'ok'")
        return v


class ReportCreate(BaseModel):
    """Schema per la registrazione della segnalazione nel database."""
    confession_id: int = Field(..., description="ID della confessione segnalata")
    reporter_id: int = Field(..., description="ID dell'utente segnalatore")
    reason: TriageCategory = Field(..., description="Motivo della segnalazione")


class ReportResolveRequest(BaseModel):
    """Richiesta amministratore per risolvere o chiudere una segnalazione."""
    resolved: bool = Field(
        default=True,
        description="Stato di risoluzione della segnalazione",
    )


class ReportResponse(BaseModel):
    """Schema di risposta per una segnalazione."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    confession_id: int
    reporter_id: int
    reason: TriageCategory
    resolved: bool
    created_at: datetime
