from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import PollChoice


class PollVoteCreateRequest(BaseModel):
    """Richiesta inviata dal client (es. HTMX) per esprimere un voto su un sondaggio."""
    choice: PollChoice = Field(
        ...,
        description="Scelta espressa: 'a' per la prima opzione, 'b' per la seconda",
    )


class PollVoteCreate(BaseModel):
    """Schema per la persistenza del voto a database."""
    confession_id: uuid.UUID = Field(..., description="ID della confessione con sondaggio")
    user_id: uuid.UUID = Field(..., description="ID dell'utente votante")
    choice: PollChoice = Field(..., description="Scelta effettuata ('a' o 'b')")


class PollVoteResponse(BaseModel):
    """Risposta contenente i risultati percentuali aggiornati per il widget sondaggio."""
    model_config = ConfigDict(from_attributes=True)

    confession_id: uuid.UUID
    user_id: uuid.UUID
    choice: PollChoice
    created_at: datetime

    # Statistiche aggiornate del sondaggio
    poll_votes_a: Optional[int] = None
    poll_votes_b: Optional[int] = None
    percentage_a: Optional[float] = None
    percentage_b: Optional[float] = None
