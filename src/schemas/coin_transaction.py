from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import TxType


class StarsPurchaseRequest(BaseModel):
    """Richiesta di accredito monete a seguito di acquisto con Telegram Stars."""
    stars_amount: int = Field(
        ...,
        gt=0,
        description="Quantità di Telegram Stars acquistate (deve essere maggiore di 0)",
    )
    telegram_charge_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="ID univoco transazione emesso da Telegram Stars",
    )


class CoinSpendRequest(BaseModel):
    """Richiesta di acquisto di un potenziamento, sabotaggio o potere IA tramite monete."""
    tx_type: TxType = Field(
        ...,
        description="Tipologia di spesa (buy_highlight, buy_pin_boost, buy_ai_lawyer, buy_ai_prosecutor, buy_shame_stamp)",
    )
    target_confession_id: Optional[uuid.UUID] = Field(
        default=None,
        description="ID della confessione target per il potenziamento o sabotaggio",
    )

    @field_validator("tx_type")
    @classmethod
    def validate_spend_type(cls, v: TxType) -> TxType:
        valid_spend_types = {
            TxType.BUY_HIGHLIGHT,
            TxType.BUY_PIN_BOOST,
            TxType.BUY_AI_LAWYER,
            TxType.BUY_AI_PROSECUTOR,
            TxType.BUY_SHAME_STAMP,
        }
        if v not in valid_spend_types:
            raise ValueError(f"'{v.value}' non è un tipo di acquisto/spesa valido con monete")
        return v


class CoinTransactionCreate(BaseModel):
    """Schema per la persistenza di una transazione economica nel database."""
    user_id: uuid.UUID = Field(..., description="ID dell'utente associato")
    amount: int = Field(..., description="Variazione monete (positivo = accredito, negativo = addebito)")
    balance_after: int = Field(..., ge=0, description="Saldo risultante dell'utente (deve essere >= 0)")
    tx_type: TxType = Field(..., description="Tipo di transazione")
    stars_paid: Optional[int] = Field(default=None, gt=0, description="Telegram Stars pagate (se applicabile)")
    telegram_charge_id: Optional[str] = Field(default=None, max_length=255, description="ID carica Telegram")
    target_confession_id: Optional[uuid.UUID] = Field(default=None, description="Confessione collegata (se applicabile)")

    @field_validator("amount")
    @classmethod
    def amount_cannot_be_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("L'importo della transazione non può essere pari a zero")
        return v


class CoinTransactionResponse(BaseModel):
    """Schema di risposta per una transazione monetaria."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    amount: int
    balance_after: int
    tx_type: TxType
    stars_paid: Optional[int] = None
    telegram_charge_id: Optional[str] = None
    target_confession_id: Optional[uuid.UUID] = None
    created_at: datetime
