from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competence import Competence
from app.models.schemas import CompetenceCreate, CompetenceUpdate


async def create_competence(db: AsyncSession, data: CompetenceCreate) -> Competence:
    competence = Competence(**data.model_dump())
    db.add(competence)
    await db.commit()
    await db.refresh(competence)
    return competence


async def get_competence(db: AsyncSession, competence_id: UUID) -> Optional[Competence]:
    result = await db.execute(select(Competence).where(Competence.id == competence_id))
    return result.scalar_one_or_none()


async def list_competences(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    category: Optional[str] = None,
) -> tuple[list[Competence], int]:
    query = select(Competence)
    count_query = select(func.count(Competence.id))

    if category:
        query = query.where(Competence.category == category)
        count_query = count_query.where(Competence.category == category)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    competences = list(result.scalars().all())
    return competences, total


async def update_competence(
    db: AsyncSession, competence: Competence, data: CompetenceUpdate
) -> Competence:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competence, field, value)
    await db.commit()
    await db.refresh(competence)
    return competence


async def delete_competence(db: AsyncSession, competence: Competence) -> None:
    await db.delete(competence)
    await db.commit()
