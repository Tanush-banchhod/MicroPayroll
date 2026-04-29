"""Company router — create and retrieve companies."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.company import Company
from api.schemas.company import CompanyCreate, CompanyResponse

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company",
)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    company = Company(
        id=uuid.uuid4(),
        name=payload.name,
        address=payload.address,
        gstin=payload.gstin,
        state=payload.state,
        whatsapp_number=payload.whatsapp_number,
        owner_phone=payload.owner_phone,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyResponse.model_validate(company)


@router.get(
    "",
    response_model=list[CompanyResponse],
    summary="List all companies",
)
async def list_companies(
    db: AsyncSession = Depends(get_db),
) -> list[CompanyResponse]:
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()
    return [CompanyResponse.model_validate(c) for c in companies]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get a company by ID",
)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyResponse.model_validate(company)
