import uuid
from fastapi import HTTPException, status
from sqlmodel import Session

from src.models import Confession
from src.schemas import ConfessionCreate


async def create_confession_service(
    session: Session,
    author_id: int,
    data: ConfessionCreate,
) -> Confession:

    try:
        
        confession = Confession(
            **data.model_dump(exclude={"author_id"}),
            author_id=author_id,
        )

        session.add(confession)
        session.commit()
        session.refresh(confession)

        return confession

    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist confession: {str(exc)}",
        )


async def delete_confession_service(
    session: Session,
    author_id: int,
    id: int,
) -> dict:
    """Delete a confession after verifying record existence and author ownership."""
    try:
        # Retrieve confession record by primary key
        check_confession = session.get(Confession, id)

        # Check if confession exists
        if not check_confession:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confession not found",
            )

        # Verify that only the author can delete the confession
        if check_confession.author_id != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this confession",
            )

        # Delete record and commit transaction
        session.delete(check_confession)
        session.commit()

        return {"status": "ok", "message": "Confession deleted successfully"}

    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code and message
        raise
    except Exception as exc:
        # Rollback on database failure
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete confession: {str(exc)}",
        )
