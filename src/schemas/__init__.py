from src.schemas.coin_transaction import (
    CoinSpendRequest,
    CoinTransactionCreate,
    CoinTransactionResponse,
    StarsPurchaseRequest,
)
from src.schemas.confession import (
    ConfessionAIUpdate,
    ConfessionBoostRequest,
    ConfessionCreate,
    ConfessionFilterRequest,
    ConfessionResponse,
)
from src.schemas.poll_vote import (
    PollVoteCreate,
    PollVoteCreateRequest,
    PollVoteResponse,
)
from src.schemas.reaction import (
    ReactionCreate,
    ReactionCreateRequest,
    ReactionResponse,
)
from src.schemas.report import (
    ReportCreate,
    ReportCreateRequest,
    ReportResolveRequest,
    ReportResponse,
)
from src.schemas.user import (
    TelegramAuthRequest,
    TelegramWidgetAuthRequest,
    UserCreate,
    UserResponse,
    UserStatusUpdateRequest,
    UserTermsAcceptRequest,
)

__all__ = [
    # User
    "TelegramAuthRequest",
    "TelegramWidgetAuthRequest",
    "UserTermsAcceptRequest",
    "UserCreate",
    "UserStatusUpdateRequest",
    "UserResponse",
    # Confession
    "ConfessionCreate",
    "ConfessionAIUpdate",
    "ConfessionBoostRequest",
    "ConfessionFilterRequest",
    "ConfessionResponse",
    # Reaction
    "ReactionCreateRequest",
    "ReactionCreate",
    "ReactionResponse",
    # Poll Vote
    "PollVoteCreateRequest",
    "PollVoteCreate",
    "PollVoteResponse",
    # Report
    "ReportCreateRequest",
    "ReportCreate",
    "ReportResolveRequest",
    "ReportResponse",
    # Coin Transaction
    "StarsPurchaseRequest",
    "CoinSpendRequest",
    "CoinTransactionCreate",
    "CoinTransactionResponse",
]
