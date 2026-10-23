from datetime import datetime, timezone
import hashlib
import hmac
import secrets
import time
from typing import Optional

from aiogram.utils.web_app import safe_parse_webapp_init_data
from fastapi import Header, HTTPException, status
from sqlmodel import Session, select

from config.settings import settings
from src.models import User, UserStatus


class TelegramAuthService:
    

    # Maximum allowed age for initData (24 hours) to prevent replay attacks
    MAX_AUTH_AGE_SECONDS: int = 86400

    @classmethod
    def validate_and_extract_telegram_id(cls, init_data_str: str) -> tuple[int, Optional[str]]:
        """Validate the cryptographic HMAC signature of Telegram initData.

        Returns:
            A tuple of (telegram_id, start_param).

        Raises:
            HTTPException: 401 if signature is invalid or auth_date is expired.
            HTTPException: 400 if user data is missing.
        """
        bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
        if not bot_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TELEGRAM_BOT_TOKEN is not configured on the server",
            )

        try:
            # Cryptographic signature validation via aiogram
            parsed_data = safe_parse_webapp_init_data(
                token=bot_token,
                init_data=init_data_str,
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or forged Telegram initData signature",
            )

        # Replay attack prevention: verify auth_date freshness
        auth_timestamp = parsed_data.auth_date.timestamp()
        current_timestamp = time.time()
        if current_timestamp - auth_timestamp > cls.MAX_AUTH_AGE_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Telegram authentication data has expired",
            )

        if not parsed_data.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User object missing from Telegram initData",
            )

        return parsed_data.user.id, parsed_data.start_param

    @classmethod
    def derive_user_key(cls, telegram_id: int) -> str:
        """Derive a one-way pseudonymous user_key using HMAC-SHA256.

        Zero-PII guarantee: the raw Telegram ID is dropped from memory immediately.
        """
        secret_key = settings.HMAC_SECRET_KEY.get_secret_value().encode("utf-8")
        telegram_id_bytes = str(telegram_id).encode("utf-8")

        return hmac.new(
            key=secret_key,
            msg=telegram_id_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

    @classmethod
    def generate_unique_referral_code(cls, session: Session) -> str:
        """Generate a cryptographically secure, unique 8-character referral code."""
        for _ in range(10):
            candidate = f"HM{secrets.token_hex(3).upper()}"  # e.g., 'HM4A8F9B' (8 chars)
            existing = session.exec(select(User).where(User.referral_code == candidate)).first()
            if not existing:
                return candidate
        # Fallback to 12 chars if collisions occur
        return f"HM{secrets.token_hex(5).upper()}"

    @classmethod
    def validate_and_extract_widget_telegram_id(cls, widget_data: dict) -> int:
        """Validate HMAC signature of data received from the Telegram Login Widget (Web)."""
        bot_token = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
        if not bot_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TELEGRAM_BOT_TOKEN is not configured on the server",
            )

        data = widget_data.copy()
        check_hash = data.pop("hash", None)
        if not check_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'hash' parameter in widget authorization data",
            )

        # Ignore non-Telegram fields that frontend may append
        data.pop("referral_code", None)
        data.pop("accepted", None)

        auth_date = data.get("auth_date")
        if not auth_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'auth_date' in widget authorization data",
            )

        try:
            if time.time() - int(auth_date) > cls.MAX_AUTH_AGE_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Telegram authentication data has expired",
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 'auth_date' format",
            )

        # Telegram widget data check string: sorted by key, key=value joined with \n
        sorted_keys = sorted(data.keys())
        data_check_arr = [f"{key}={data[key]}" for key in sorted_keys if data[key] is not None]
        data_check_string = "\n".join(data_check_arr)

        # Secret key for widget is SHA256 of bot token
        secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, check_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram Login Widget signature",
            )

        telegram_id = data.get("id")
        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram user ID missing from widget data",
            )

        return int(telegram_id)

    @classmethod
    def get_or_create_user_by_telegram_id(
        cls,
        session: Session,
        telegram_id: int,
        referral_code: Optional[str] = None,
    ) -> tuple[User, bool]:
        """Resolve or register a user by telegram_id with Zero-PII protection.

        Derives pseudonymous user_key and drops the raw telegram_id.
        """
        user_key = cls.derive_user_key(telegram_id)

        statement = select(User).where(User.user_key == user_key)
        user = session.exec(statement).first()

        if user:
            if user.status == UserStatus.BANNED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User account is banned. Reason: {user.ban_reason or 'Violation of terms'}",
                )
            return user, False

        referred_by_id = None
        if referral_code:
            referrer = session.exec(
                select(User).where(User.referral_code == referral_code.strip().upper())
            ).first()
            if referrer:
                referred_by_id = referrer.id

        new_referral_code = cls.generate_unique_referral_code(session)

        user = User(
            user_key=user_key,
            status=UserStatus.ACTIVE,
            coins_balance=50,
            referral_code=new_referral_code,
            referred_by_id=referred_by_id,
            terms_accepted_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return user, True

    @classmethod
    def get_or_create_user(
        cls,
        session: Session,
        init_data_str: str,
        referral_code: Optional[str] = None,
    ) -> tuple[User, bool]:
        """Authenticate a user via Telegram Mini App initData."""
        telegram_id, start_param = cls.validate_and_extract_telegram_id(init_data_str)
        effective_ref = referral_code or start_param
        return cls.get_or_create_user_by_telegram_id(
            session=session,
            telegram_id=telegram_id,
            referral_code=effective_ref,
        )

    @classmethod
    def get_or_create_user_from_widget(
        cls,
        session: Session,
        widget_data: dict,
        referral_code: Optional[str] = None,
    ) -> tuple[User, bool]:
        """Authenticate a user via Telegram Login Widget (Web)."""
        telegram_id = cls.validate_and_extract_widget_telegram_id(widget_data)
        effective_ref = referral_code or widget_data.get("referral_code")
        return cls.get_or_create_user_by_telegram_id(
            session=session,
            telegram_id=telegram_id,
            referral_code=effective_ref,
        )
