from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import ReactionType


class ReactionCreateRequest(BaseModel):
    """Richiesta inviata dal client (es. HTMX hx-post) per aggiungere o modificare una reazione."""
    type: ReactionType = Field(
        ...,
        description="Tipologia di reazione selezionata (skull, disagio, popcorn, clown)",
    )


class ReactionCreate(BaseModel):
    """Schema per la persistenza a database di una reazione."""
    confession_id: uuid.UUID = Field(..., description="ID della confessione target")
    user_id: uuid.UUID = Field(..., description="ID dell'utente votante")
    type: ReactionType = Field(..., description="Tipo di reazione")


class ReactionResponse(BaseModel):
    """Risposta con lo stato della reazione e i contatori aggiornati."""
    model_config = ConfigDict(from_attributes=True)

    confession_id: uuid.UUID
    user_id: uuid.UUID
    type: ReactionType
    created_at: datetime

    # Contatori aggiornati per facilitare il re-rendering via HTMX
    count_skull: Optional[int] = None
    count_disagio: Optional[int] = None
    count_popcorn: Optional[int] = None
    count_clown: Optional[int] = None
    total_reactions: Optional[int] = None
