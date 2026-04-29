"""Employee router — CRUD for employees within a company."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.company import Company
from api.models.employee import Employee
from api.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an employee to a company",
)
async def create_employee(
    payload: EmployeeCreate,
    company_id: uuid.UUID = Query(..., description="Company the employee belongs to"),
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    result = await db.execute(select(Company).where(Company.id == company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    employee = Employee(
        id=uuid.uuid4(),
        company_id=company_id,
        name=payload.name,
        role=payload.role,
        base_salary=payload.base_salary,
        phone_number=payload.phone_number,
        bank_account=payload.bank_account,
        bank_ifsc=payload.bank_ifsc,
        pf_account=payload.pf_account,
        joined_at=payload.joined_at,
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.get(
    "",
    response_model=list[EmployeeResponse],
    summary="List all employees for a company",
)
async def list_employees(
    company_id: uuid.UUID = Query(..., description="Filter by company"),
    active_only: bool = Query(True, description="Return only active employees"),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeResponse]:
    query = select(Employee).where(Employee.company_id == company_id)
    if active_only:
        query = query.where(Employee.is_active.is_(True))
    query = query.order_by(Employee.name)
    result = await db.execute(query)
    return [EmployeeResponse.model_validate(e) for e in result.scalars().all()]


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get a single employee",
)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeResponse.model_validate(employee)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee details",
)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an employee (sets is_active = false)",
)
async def deactivate_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee.is_active = False
    await db.commit()
