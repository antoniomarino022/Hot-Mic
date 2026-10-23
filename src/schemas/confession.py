from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import (
    ModerationStatus,
    PostStyle,
    ShameBadge,
)


class ConfessionCreate(BaseModel):
    """Schema per la persistenza di una nuova confessione nel database."""
    author_id: Optional[int] = Field(default=None, description="ID dell'autore della confessione (assegnato dal server)")
    content: str = Field(..., min_length=10, max_length=2000)
    poll_option_a: Optional[str] = Field(default=None, max_length=80)
    poll_option_b: Optional[str] = Field(default=None, max_length=80)
    mod_status: ModerationStatus = Field(default=ModerationStatus.PENDING_AI)
    severity: int = Field(default=0, ge=0)


class ConfessionAIUpdate(BaseModel):
    """Schema per l'aggiornamento automatico della pipeline AI (Triage & Roast)."""
    ai_roast: Optional[str] = Field(default=None, description="Testo del roast generato dal Giudice Bastardo")
    mod_status: Optional[ModerationStatus] = Field(default=None, description="Stato di moderazione stabilito")
    severity: Optional[int] = Field(default=None, ge=0, description="Grado di severità (0-10)")
    ai_defense: Optional[str] = Field(default=None, description="Argomentazione difensiva dell'avvocato difensore IA")
    ai_prosecution: Optional[str] = Field(default=None, description="Atto di accusa del pubblico ministero IA")


class ConfessionBoostRequest(BaseModel):
    """Richiesta di acquisto o applicazione boost estetico / pin / sabotaggio."""
    visual_style: Optional[PostStyle] = Field(
        default=None,
        description="Stile visivo premium applicato (es. neon_cyber, gold_glitch)",
    )
    shame_stamp: Optional[ShameBadge] = Field(
        default=None,
        description="Timbro della vergogna acquistato da un rivale",
    )
    pin_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=72,
        description="Ore di permanenza in cima al feed (pin)",
    )


class ConfessionFilterRequest(BaseModel):
    """Parametri di filtro e paginazione del feed confessioni."""
    feed_type: str = Field(
        default="latest",
        pattern=r"^(latest|popular|podium)$",
        description="Tipologia di feed: latest (recenti), popular (più votati), podium (settimanali)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Numero di post per pagina",
    )
    cursor: Optional[datetime] = Field(
        default=None,
        description="Cursore temporale per paginazione infinita",
    )


class ConfessionResponse(BaseModel):
    """Schema di risposta completo per una confessione."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    content: str
    ai_roast: Optional[str] = None
    mod_status: ModerationStatus
    severity: int
    ai_defense: Optional[str] = None
    ai_prosecution: Optional[str] = None
    visual_style: PostStyle
    shame_stamp: ShameBadge
    pinned_until: Optional[datetime] = None
    weekly_rank: Optional[int] = None
    poll_option_a: Optional[str] = None
    poll_option_b: Optional[str] = None
    poll_votes_a: int
    poll_votes_b: int
    count_skull: int
    count_disagio: int
    count_popcorn: int
    count_clown: int
    total_reactions: Optional[int] = None
    reports_count: int
    created_at: datetime
    deleted_at: Optional[datetime] = None
