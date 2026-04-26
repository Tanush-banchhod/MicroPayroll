"""
Core salary calculation engine.

All monetary values are in INR (Indian Rupees), rounded to 2 decimal places.
The engine has zero web/DB dependencies — it can be imported and tested standalone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from engine.compliance.india import ComplianceRules, load_rules


STANDARD_WORKING_DAYS: int = 26  # Indian payroll convention


@dataclass
class EmployeeInput:
    """All variable inputs needed to compute one employee's monthly payroll."""

    employee_id: str
    base_salary: float          # full-month CTC basic component
    working_days: int           # days present this month (from attendance)
    overtime_hours: float       # total overtime *hours* accumulated this month
    unpaid_leave_days: int      # days deducted without pay
    festival_bonus: bool        # whether festival bonus applies this month
    state: str = "Maharashtra"  # drives Professional Tax slab selection

    # Optional overrides – None means "use rule file default"
    working_days_per_month: Optional[int] = None   # override standard 26
    overtime_multiplier: Optional[float] = None    # override 2.0x


@dataclass
class PayrollResult:
    """Full breakdown of one employee's monthly payroll calculation."""

    # Earnings
    basic: float                # proportionate basic for days worked
    overtime_pay: float
    leave_deduction: float      # stored as positive; subtracted from gross
    festival_bonus_amount: float

    # Gross
    gross: float                # basic + overtime_pay + festival_bonus - leave_deduction

    # Employee deductions
    pf_employee: float
    esic_employee: float
    professional_tax: float
    total_deductions: float

    # Net
    net_pay: float

    # Employer contributions (informational, not deducted from employee)
    employer_pf: float
    employer_esic: float
    cost_to_company: float      # gross + employer_pf + employer_esic

    # Audit trail – full step-by-step breakdown stored for payslip / JSONB snapshot
    breakdown: dict = field(default_factory=dict)


def _round(value: float) -> float:
    return round(value, 2)


def calculate(inp: EmployeeInput, rules: Optional[ComplianceRules] = None) -> PayrollResult:
    """
    Calculate complete payroll for one employee for one month.

    Args:
        inp:   EmployeeInput with all variable data for the month.
        rules: ComplianceRules loaded from a YAML rule file.
               If None, defaults to Maharashtra rules.

    Returns:
        PayrollResult with every component and a full breakdown dict.
    """
    if rules is None:
        rules = load_rules(inp.state)

    wdpm = inp.working_days_per_month or rules.working_days_per_month
    ot_multiplier = inp.overtime_multiplier or rules.overtime_multiplier

    # ── 1. Daily rate ─────────────────────────────────────────────────────────
    daily_rate = _round(inp.base_salary / wdpm)

    # ── 2. Proportionate basic (salary for days actually worked) ──────────────
    # We pay for working_days + will add OT separately; leave deduction handled
    # as a separate line so the payslip shows gross before deduction clearly.
    basic = _round(daily_rate * inp.working_days)

    # ── 3. Overtime pay ───────────────────────────────────────────────────────
    # OT input is in *hours*; daily rate covers standard shift hours.
    # OT rate per hour = (daily_rate / standard_shift_hours) * ot_multiplier
    # But per the spec: OT pay = overtime_days × daily_rate × 2
    # The input stores hours; convert using standard shift hours from rules.
    ot_hours_per_shift = rules.standard_shift_hours
    overtime_days_equivalent = inp.overtime_hours / ot_hours_per_shift
    overtime_pay = _round(overtime_days_equivalent * daily_rate * ot_multiplier)

    # ── 4. Unpaid leave deduction ─────────────────────────────────────────────
    leave_deduction = _round(inp.unpaid_leave_days * daily_rate)

    # ── 5. Festival bonus ─────────────────────────────────────────────────────
    festival_bonus_amount = 0.0
    if inp.festival_bonus:
        festival_bonus_amount = _round(inp.base_salary * rules.festival_bonus_rate)

    # ── 6. Gross pay ──────────────────────────────────────────────────────────
    gross = _round(basic + overtime_pay + festival_bonus_amount - leave_deduction)
    # Gross must not go below zero (edge case: mostly absent month)
    gross = max(gross, 0.0)

    # ── 7. Provident Fund (employee share) ────────────────────────────────────
    # PF is calculated on min(base_salary, wage_ceiling) — the *full month* base,
    # not proportionate basic, per EPFO rules.
    pf_base = min(inp.base_salary, rules.pf_wage_ceiling)
    pf_employee = _round(pf_base * rules.pf_employee_rate)
    employer_pf = _round(pf_base * rules.pf_employer_rate)

    # ── 8. ESIC (employee share) ──────────────────────────────────────────────
    # ESIC applies only when gross ≤ ESIC threshold (₹21,000)
    esic_employee = 0.0
    employer_esic = 0.0
    esic_applicable = gross <= rules.esic_gross_threshold
    if esic_applicable:
        esic_employee = _round(gross * rules.esic_employee_rate)
        employer_esic = _round(gross * rules.esic_employer_rate)

    # ── 9. Professional Tax ───────────────────────────────────────────────────
    professional_tax = _compute_professional_tax(gross, rules)

    # ── 10. Totals ────────────────────────────────────────────────────────────
    total_deductions = _round(pf_employee + esic_employee + professional_tax)
    net_pay = _round(gross - total_deductions)
    cost_to_company = _round(gross + employer_pf + employer_esic)

    breakdown = {
        "inputs": {
            "employee_id": inp.employee_id,
            "base_salary": inp.base_salary,
            "working_days": inp.working_days,
            "overtime_hours": inp.overtime_hours,
            "unpaid_leave_days": inp.unpaid_leave_days,
            "festival_bonus": inp.festival_bonus,
            "state": inp.state,
        },
        "rates": {
            "working_days_per_month": wdpm,
            "daily_rate": daily_rate,
            "overtime_multiplier": ot_multiplier,
            "standard_shift_hours": ot_hours_per_shift,
            "overtime_days_equivalent": round(overtime_days_equivalent, 4),
        },
        "earnings": {
            "basic": basic,
            "overtime_pay": overtime_pay,
            "festival_bonus": festival_bonus_amount,
        },
        "deductions_pre_gross": {
            "leave_deduction": leave_deduction,
        },
        "gross": gross,
        "compliance": {
            "pf_base": pf_base,
            "pf_employee_rate": rules.pf_employee_rate,
            "pf_employee": pf_employee,
            "esic_applicable": esic_applicable,
            "esic_gross_threshold": rules.esic_gross_threshold,
            "esic_employee_rate": rules.esic_employee_rate if esic_applicable else 0,
            "esic_employee": esic_employee,
            "professional_tax_slab": professional_tax,
        },
        "employer_contributions": {
            "employer_pf_rate": rules.pf_employer_rate,
            "employer_pf": employer_pf,
            "employer_esic_rate": rules.esic_employer_rate if esic_applicable else 0,
            "employer_esic": employer_esic,
        },
        "summary": {
            "total_deductions": total_deductions,
            "net_pay": net_pay,
            "cost_to_company": cost_to_company,
        },
    }

    return PayrollResult(
        basic=basic,
        overtime_pay=overtime_pay,
        leave_deduction=leave_deduction,
        festival_bonus_amount=festival_bonus_amount,
        gross=gross,
        pf_employee=pf_employee,
        esic_employee=esic_employee,
        professional_tax=professional_tax,
        total_deductions=total_deductions,
        net_pay=net_pay,
        employer_pf=employer_pf,
        employer_esic=employer_esic,
        cost_to_company=cost_to_company,
        breakdown=breakdown,
    )


def _compute_professional_tax(gross: float, rules: ComplianceRules) -> float:
    """
    Look up monthly PT from the state's slab table.
    Slabs are sorted ascending by max_salary; first matching slab wins.
    """
    for slab in rules.professional_tax_slabs:
        if gross <= slab["max_salary"]:
            return float(slab["monthly_tax"])
    # Fallback to highest slab if gross exceeds all defined ceilings
    return float(rules.professional_tax_slabs[-1]["monthly_tax"]) if rules.professional_tax_slabs else 0.0
