from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from config import db
from src.schemas import (
    TelegramAuthRequest,
    TelegramWidgetAuthRequest,
    UserResponse,
    UserTermsAcceptRequest,
)
from src.services import TelegramAuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def register(
    data: TelegramAuthRequest,
    checkbox: UserTermsAcceptRequest,
    response: Response,
    session: Session = Depends(db),
) -> UserResponse:
    # Verify terms of service acceptance
    if not checkbox.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted to register.",
        )

    # Authenticate or create user with Zero-PII guarantees
    user, created = TelegramAuthService.get_or_create_user(
        session=session,
        init_data_str=data.init_data,
        referral_code=data.referral_code,
    )

    # Differentiate HTTP status: 201 Created for new users, 200 OK for returning users
    if created:
        response.status_code = status.HTTP_201_CREATED

    # Set secure HTTP-only session cookie
    response.set_cookie(
        key="hotmic_session",
        value=user.user_key,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/widget",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def login_widget(
    data: TelegramWidgetAuthRequest,
    response: Response,
    session: Session = Depends(db),
) -> UserResponse:
    if not data.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted to register.",
        )

    user, created = TelegramAuthService.get_or_create_user_from_widget(
        session=session,
        widget_data=data.model_dump(),
        referral_code=data.referral_code,
    )

    if created:
        response.status_code = status.HTTP_201_CREATED

    # Set secure HTTP-only session cookie
    response.set_cookie(
        key="hotmic_session",
        value=user.user_key,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30, 
    )

    return UserResponse.model_validate(user)




@router.post(
    "/logout",
    summary="Logout user session",
)
async def logout(response: Response):
    response.delete_cookie(key="hotmic_session")
    return {"status": "ok", "message": "Logged out successfully"}
