import uuid
from fastapi import HTTPException, status
from sqlmodel import Session

from src.agents import run_confession_pipeline
from src.models import Confession
from src.models.enums import ModerationStatus
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


async def process_confession_ai_pipeline(
    session: Session,
    confession_id: int,
    active_powers: list[str] | None = None,
) -> Confession:
    """Execute the multi-agent AI pipeline for a confession and persist results."""
    try:
        confession = session.get(Confession, confession_id)
        if not confession:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confession not found for AI processing",
            )

        if confession.id is None:
              raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confession not found for AI processing",
            )
        
        pipeline_result = await run_confession_pipeline(
            content=confession.content,
            confession_id=confession.id,
            active_powers=active_powers or [],
        )

        raw_mod_status = pipeline_result.get("mod_status", "crisis_held")
        confession.mod_status = ModerationStatus(raw_mod_status)
        confession.severity = int(pipeline_result.get("severity", 0))
        confession.ai_roast = pipeline_result.get("ai_roast")
        confession.ai_defense = pipeline_result.get("ai_defense")
        confession.ai_prosecution = pipeline_result.get("ai_prosecution")

        session.add(confession)
        session.commit()
        session.refresh(confession)

        return confession

    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process confession AI pipeline: {str(exc)}",
        )
