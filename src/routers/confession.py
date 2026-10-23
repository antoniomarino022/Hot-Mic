from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from config import db
from src.models import User
from src.routers.deps import get_current_user
from src.schemas import ConfessionCreate, ConfessionResponse
from src.services.confession_service import (
    create_confession_service,
    delete_confession_service,
)

router = APIRouter(prefix="/confessions", tags=["Confessions"])


@router.post(
    "/",
    response_model=ConfessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new anonymous confession",
    description="Creates an anonymous confession by delegating to the confession service.",
)
async def create_confession(
    data: ConfessionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db),
) -> ConfessionResponse:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user must have a valid identifier",
        )


    confession = await create_confession_service(
        session=session,
        author_id=current_user.id,
        data=data,
    )

    return ConfessionResponse.model_validate(confession)


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete confession",
    description="Deletes a confession ensuring only the creator has permission to remove it.",
)
async def delete_confession(
    id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db),
) -> dict:
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user must have a valid identifier",
        )

    # Delegate deletion check to service function
    return await delete_confession_service(
        session=session,
        author_id=current_user.id,
        id=id,
    )
