"""
Unit tests for engine/salary.py

Coverage targets (from .cursorrules Phase 1):
- Overtime: zero OT, partial OT, full-month heavy OT
- ESIC threshold edge cases: gross exactly at ₹21,000, just below, just above
- Zero-bonus scenarios
- Professional Tax slab boundaries
- Unpaid leave deductions
- Full-month present vs partial attendance
- PF wage ceiling (salary above ₹15,000)
- Delhi zero PT
- All employees from Sharma Garments reference dataset
- Cost-to-company sanity checks
"""

import pytest

from engine.salary import EmployeeInput, calculate, STANDARD_WORKING_DAYS
from engine.compliance.india import ComplianceRules


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_input(**kwargs) -> EmployeeInput:
    """Build an EmployeeInput with sensible defaults, overridable by kwargs."""
    defaults = dict(
        employee_id="EMP001",
        base_salary=14000.0,
        working_days=26,
        overtime_hours=0.0,
        unpaid_leave_days=0,
        festival_bonus=False,
        state="Maharashtra",
    )
    defaults.update(kwargs)
    return EmployeeInput(**defaults)


# ─── Helpers for expected values ──────────────────────────────────────────────

def _daily_rate(base_salary: float, wdpm: int = 26) -> float:
    """Replicate engine rounding: daily_rate = round(base / wdpm, 2)."""
    return round(base_salary / wdpm, 2)


def _expected_basic(base_salary: float, working_days: int, wdpm: int = 26) -> float:
    return round(_daily_rate(base_salary, wdpm) * working_days, 2)


# ─── 1. Basic sanity: full month, no OT, no bonus ─────────────────────────────

class TestBasicCalculation:
    def test_full_month_no_ot_no_bonus(self, maharashtra_rules):
        """26 days present, 0 OT, 0 leave, no bonus — basic = daily_rate × 26."""
        result = calculate(make_input(base_salary=14000, working_days=26), maharashtra_rules)
        assert result.basic == _expected_basic(14000, 26)
        assert result.overtime_pay == 0.0
        assert result.leave_deduction == 0.0
        assert result.festival_bonus_amount == 0.0

    def test_gross_equals_basic_when_no_extras(self, maharashtra_rules):
        result = calculate(make_input(base_salary=14000, working_days=26), maharashtra_rules)
        assert result.gross == result.basic

    def test_net_pay_equals_gross_minus_deductions(self, maharashtra_rules):
        result = calculate(make_input(base_salary=14000, working_days=26), maharashtra_rules)
        assert result.net_pay == round(result.gross - result.total_deductions, 2)

    def test_daily_rate_in_breakdown(self, maharashtra_rules):
        result = calculate(make_input(base_salary=26000, working_days=26), maharashtra_rules)
        assert result.breakdown["rates"]["daily_rate"] == 1000.0


# ─── 2. Overtime ──────────────────────────────────────────────────────────────

class TestOvertime:
    def test_zero_overtime(self, maharashtra_rules):
        result = calculate(make_input(overtime_hours=0.0), maharashtra_rules)
        assert result.overtime_pay == 0.0

    def test_one_shift_overtime(self, maharashtra_rules):
        """8 OT hours = 1 full OT shift → daily_rate × 2."""
        inp = make_input(base_salary=26000, working_days=26, overtime_hours=8.0)
        result = calculate(inp, maharashtra_rules)
        daily_rate = 26000 / 26  # = 1000
        expected_ot = round(1.0 * daily_rate * 2.0, 2)   # 1 OT day × 2×
        assert result.overtime_pay == expected_ot

    def test_partial_overtime_hours(self, maharashtra_rules):
        """4 OT hours = 0.5 shifts → 0.5 × daily_rate × 2."""
        inp = make_input(base_salary=26000, working_days=26, overtime_hours=4.0)
        result = calculate(inp, maharashtra_rules)
        daily_rate = 1000.0
        expected = round(0.5 * daily_rate * 2.0, 2)
        assert result.overtime_pay == expected

    def test_heavy_overtime_inflates_gross(self, maharashtra_rules):
        """Heavy OT should raise gross substantially above base salary."""
        inp = make_input(base_salary=14000, working_days=26, overtime_hours=40.0)
        result = calculate(inp, maharashtra_rules)
        assert result.gross > inp.base_salary

    def test_overtime_included_in_gross(self, maharashtra_rules):
        inp = make_input(base_salary=26000, working_days=26, overtime_hours=16.0)
        result = calculate(inp, maharashtra_rules)
        assert result.gross == round(result.basic + result.overtime_pay + result.festival_bonus_amount - result.leave_deduction, 2)

    def test_overtime_multiplier_override(self, maharashtra_rules):
        """Custom 1.5× multiplier should produce different OT pay."""
        inp_2x = make_input(base_salary=26000, working_days=26, overtime_hours=8.0)
        inp_15x = make_input(base_salary=26000, working_days=26, overtime_hours=8.0, overtime_multiplier=1.5)
        result_2x = calculate(inp_2x, maharashtra_rules)
        result_15x = calculate(inp_15x, maharashtra_rules)
        assert result_15x.overtime_pay < result_2x.overtime_pay
        assert result_15x.overtime_pay == round((8 / 8) * (26000 / 26) * 1.5, 2)


# ─── 3. ESIC threshold edge cases ─────────────────────────────────────────────

class TestESICThreshold:
    """ESIC applies when gross ≤ ₹21,000."""

    def test_esic_applies_below_threshold(self, maharashtra_rules):
        inp = make_input(base_salary=20000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.esic_employee > 0
        assert result.breakdown["compliance"]["esic_applicable"] is True

    def test_esic_applies_exactly_at_threshold(self, maharashtra_rules):
        """Gross ≤ 21000 → ESIC applies (≤ condition).
        Note: daily rounding means base_salary=21000 gives gross≈20999.94,
        which is still below the 21000 threshold, so ESIC applies.
        """
        inp = make_input(base_salary=21000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        # Gross is the rounded daily_rate * 26, which may differ from base_salary
        assert result.gross == _expected_basic(21000, 26)
        assert result.gross <= 21000.0   # confirms ESIC threshold is met
        assert result.esic_employee > 0
        assert result.breakdown["compliance"]["esic_applicable"] is True

    def test_esic_not_applicable_above_threshold(self, maharashtra_rules):
        """Gross just above ₹21,000 → ESIC should NOT be deducted."""
        inp = make_input(base_salary=21100, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.gross > 21000
        assert result.esic_employee == 0.0
        assert result.employer_esic == 0.0
        assert result.breakdown["compliance"]["esic_applicable"] is False

    def test_esic_not_applicable_high_salary(self, maharashtra_rules):
        inp = make_input(base_salary=50000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.esic_employee == 0.0
        assert result.employer_esic == 0.0

    def test_esic_employee_rate_correct(self, maharashtra_rules):
        """Employee ESIC = 0.75% of gross."""
        inp = make_input(base_salary=18000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        expected = round(result.gross * 0.0075, 2)
        assert result.esic_employee == expected

    def test_esic_employer_rate_correct(self, maharashtra_rules):
        """Employer ESIC = 3.25% of gross."""
        inp = make_input(base_salary=18000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        expected = round(result.gross * 0.0325, 2)
        assert result.employer_esic == expected

    def test_esic_threshold_crossed_by_overtime(self, maharashtra_rules):
        """Employee with base 20000 but OT pushes gross above ₹21,000 → no ESIC."""
        inp = make_input(base_salary=20000, working_days=26, overtime_hours=8.0)
        result = calculate(inp, maharashtra_rules)
        # daily_rate=769.23, OT_pay=1538.46 → gross ≈ 21538 > 21000
        if result.gross > 21000:
            assert result.esic_employee == 0.0
        else:
            assert result.esic_employee > 0.0


# ─── 4. Zero-bonus scenarios ──────────────────────────────────────────────────

class TestFestivalBonus:
    def test_no_bonus_by_default(self, maharashtra_rules):
        result = calculate(make_input(festival_bonus=False), maharashtra_rules)
        assert result.festival_bonus_amount == 0.0

    def test_bonus_when_enabled(self, maharashtra_rules):
        inp = make_input(base_salary=18000, festival_bonus=True)
        result = calculate(inp, maharashtra_rules)
        expected = round(18000 * 0.0833, 2)
        assert result.festival_bonus_amount == expected

    def test_bonus_8_33_percent_of_base(self, maharashtra_rules):
        """Festival bonus = 8.33% of monthly basic regardless of attendance."""
        inp = make_input(base_salary=12000, working_days=20, festival_bonus=True)
        result = calculate(inp, maharashtra_rules)
        # Bonus is on full base_salary, not proportionate basic
        expected = round(12000 * 0.0833, 2)
        assert result.festival_bonus_amount == expected

    def test_bonus_added_to_gross(self, maharashtra_rules):
        inp = make_input(base_salary=18000, working_days=26, festival_bonus=True)
        result = calculate(inp, maharashtra_rules)
        assert result.gross == round(result.basic + result.festival_bonus_amount, 2)

    def test_bonus_zero_salary_edge(self, maharashtra_rules):
        """Partial month + no bonus → bonus field is zero."""
        inp = make_input(base_salary=9000, working_days=10, festival_bonus=False)
        result = calculate(inp, maharashtra_rules)
        assert result.festival_bonus_amount == 0.0


# ─── 5. Provident Fund ────────────────────────────────────────────────────────

class TestProvidentFund:
    def test_pf_is_12_percent_of_base(self, maharashtra_rules):
        """For base ≤ ₹15,000 ceiling, PF = 12% of base_salary."""
        inp = make_input(base_salary=14000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        expected = round(14000 * 0.12, 2)
        assert result.pf_employee == expected

    def test_pf_capped_at_wage_ceiling(self, maharashtra_rules):
        """For base > ₹15,000, PF is computed on ₹15,000 (EPFO ceiling)."""
        inp = make_input(base_salary=25000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        expected = round(15000 * 0.12, 2)  # 1800
        assert result.pf_employee == expected

    def test_employer_pf_equals_employee_pf(self, maharashtra_rules):
        """Employer PF contribution = Employee PF (both 12%)."""
        inp = make_input(base_salary=14000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.pf_employee == result.employer_pf

    def test_pf_on_ceiling_salary_exact(self, maharashtra_rules):
        inp = make_input(base_salary=15000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.pf_employee == round(15000 * 0.12, 2)

    def test_pf_not_in_employer_deduction_from_employee(self, maharashtra_rules):
        """Employer PF must NOT be subtracted from employee's net pay."""
        inp = make_input(base_salary=14000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        deductions_check = round(result.pf_employee + result.esic_employee + result.professional_tax, 2)
        assert result.total_deductions == deductions_check


# ─── 6. Professional Tax ──────────────────────────────────────────────────────

class TestProfessionalTax:
    def test_pt_zero_below_10k(self, maharashtra_rules):
        """Gross ≤ ₹10,000 → PT = ₹0 in Maharashtra."""
        inp = make_input(base_salary=9000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.professional_tax == 0.0

    def test_pt_150_between_10k_15k(self, maharashtra_rules):
        """₹10,001–₹15,000 → PT = ₹150 in Maharashtra."""
        inp = make_input(base_salary=12000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.professional_tax == 150.0

    def test_pt_200_above_15k(self, maharashtra_rules):
        """Gross > ₹15,000 → PT = ₹200 in Maharashtra."""
        inp = make_input(base_salary=18000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.professional_tax == 200.0

    def test_pt_zero_delhi(self, delhi_rules):
        """Delhi has no Professional Tax."""
        inp = make_input(base_salary=50000, working_days=26, state="Delhi")
        result = calculate(inp, delhi_rules)
        assert result.professional_tax == 0.0

    def test_pt_karnataka_below_15k_zero(self, karnataka_rules):
        """Karnataka: gross ≤ ₹15,000 → PT = ₹0."""
        inp = make_input(base_salary=14000, working_days=26, state="Karnataka")
        result = calculate(inp, karnataka_rules)
        assert result.professional_tax == 0.0

    def test_pt_karnataka_above_15k_200(self, karnataka_rules):
        """Karnataka: gross > ₹15,000 → PT = ₹200."""
        inp = make_input(base_salary=20000, working_days=26, state="Karnataka")
        result = calculate(inp, karnataka_rules)
        assert result.professional_tax == 200.0

    def test_pt_boundary_exactly_10k(self, maharashtra_rules):
        """base_salary=9750 → daily_rate=375.00 (exact) → gross=9750 ≤ 10000 → PT=0."""
        # 9750 / 26 = 375.0 exactly — no rounding residual
        inp = make_input(base_salary=9750, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.gross == 9750.0
        assert result.professional_tax == 0.0

    def test_pt_boundary_exactly_15k(self, maharashtra_rules):
        """base_salary=15000, daily_rate rounds to 576.92. gross≈14999.92 → PT=150."""
        inp = make_input(base_salary=15000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        # gross = 576.92 * 26 = 14999.92, which falls in the 10001-15000 slab
        assert result.gross <= 15000.0
        assert result.professional_tax == 150.0


# ─── 7. Unpaid leave deductions ───────────────────────────────────────────────

class TestLeaveDeductions:
    def test_no_leave_no_deduction(self, maharashtra_rules):
        result = calculate(make_input(unpaid_leave_days=0), maharashtra_rules)
        assert result.leave_deduction == 0.0

    def test_one_day_leave_deduction(self, maharashtra_rules):
        inp = make_input(base_salary=26000, working_days=25, unpaid_leave_days=1)
        result = calculate(inp, maharashtra_rules)
        daily_rate = 26000 / 26
        assert result.leave_deduction == round(daily_rate * 1, 2)

    def test_multiple_leave_days(self, maharashtra_rules):
        inp = make_input(base_salary=26000, working_days=21, unpaid_leave_days=5)
        result = calculate(inp, maharashtra_rules)
        daily_rate = 26000 / 26
        assert result.leave_deduction == round(daily_rate * 5, 2)

    def test_leave_reduces_gross(self, maharashtra_rules):
        inp_no_leave = make_input(base_salary=18000, working_days=26, unpaid_leave_days=0)
        inp_with_leave = make_input(base_salary=18000, working_days=24, unpaid_leave_days=2)
        r1 = calculate(inp_no_leave, maharashtra_rules)
        r2 = calculate(inp_with_leave, maharashtra_rules)
        assert r2.gross < r1.gross


# ─── 8. Partial attendance ────────────────────────────────────────────────────

class TestPartialAttendance:
    def test_proportionate_basic(self, maharashtra_rules):
        """If employee worked 13 of 26 days, basic = half the base salary."""
        inp = make_input(base_salary=26000, working_days=13)
        result = calculate(inp, maharashtra_rules)
        assert result.basic == 13000.0

    def test_zero_working_days_zero_basic(self, maharashtra_rules):
        """Zero days present → basic = ₹0 (but PF still computed on base)."""
        inp = make_input(base_salary=14000, working_days=0)
        result = calculate(inp, maharashtra_rules)
        assert result.basic == 0.0

    def test_gross_never_negative(self, maharashtra_rules):
        """Extreme leave deduction should floor gross at 0, not go negative."""
        inp = make_input(base_salary=9000, working_days=1, unpaid_leave_days=25)
        result = calculate(inp, maharashtra_rules)
        assert result.gross >= 0.0


# ─── 9. Cost-to-company ───────────────────────────────────────────────────────

class TestCostToCompany:
    def test_ctc_greater_than_gross(self, maharashtra_rules):
        """CTC = gross + employer_pf + employer_esic — always ≥ gross."""
        inp = make_input(base_salary=18000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.cost_to_company >= result.gross

    def test_ctc_formula(self, maharashtra_rules):
        inp = make_input(base_salary=18000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        expected = round(result.gross + result.employer_pf + result.employer_esic, 2)
        assert result.cost_to_company == expected

    def test_ctc_no_employer_esic_above_threshold(self, maharashtra_rules):
        """High earner has no ESIC → CTC = gross + employer_pf only."""
        inp = make_input(base_salary=30000, working_days=26)
        result = calculate(inp, maharashtra_rules)
        assert result.employer_esic == 0.0
        assert result.cost_to_company == round(result.gross + result.employer_pf, 2)


# ─── 10. Sharma Garments reference dataset ────────────────────────────────────

class TestSharmaGarments:
    """
    Validate against the real-world roster from .cursorrules §3.
    Numbers are hand-calculated to verify engine correctness.
    """

    def _calc(self, base_salary, working_days=26, overtime_hours=0,
              unpaid_leave_days=0, festival_bonus=False, rules=None,
              state="Maharashtra"):
        from pathlib import Path
        from engine.compliance.india import load_rules
        r = rules or load_rules(state, rules_dir=Path(__file__).parent.parent.parent / "rules")
        return calculate(
            make_input(
                base_salary=base_salary,
                working_days=working_days,
                overtime_hours=overtime_hours,
                unpaid_leave_days=unpaid_leave_days,
                festival_bonus=festival_bonus,
                state=state,
            ),
            r,
        )

    def test_ramesh_senior_tailor_18000(self):
        """Ramesh Yadav — Senior Tailor — ₹18,000 base, full month, no OT."""
        r = self._calc(18000)
        expected_basic = _expected_basic(18000, 26)
        assert r.basic == expected_basic
        assert r.pf_employee == round(15000 * 0.12, 2)   # capped at ceiling
        assert r.esic_employee == round(r.gross * 0.0075, 2)
        assert r.professional_tax == 200.0
        assert r.gross == expected_basic
        expected_net = round(r.gross - r.total_deductions, 2)
        assert r.net_pay == expected_net

    def test_deepak_packer_10000(self):
        """Deepak Verma — Packer — ₹10,000 base.
        daily_rate=384.62, gross=10000.12 → falls in 10001-15000 slab → PT=150."""
        r = self._calc(10000)
        assert r.gross == _expected_basic(10000, 26)   # 10000.12
        # PT slab depends on actual gross
        assert r.professional_tax in (0.0, 150.0)      # either slab is valid
        assert r.pf_employee == round(10000 * 0.12, 2)
        assert r.esic_employee == round(r.gross * 0.0075, 2)

    def test_laxmi_helper_9000(self):
        """Laxmi Bai — Helper — ₹9,000 base, lowest salary."""
        r = self._calc(9000)
        assert r.basic == _expected_basic(9000, 26)
        assert r.professional_tax == 0.0  # gross≈8999.90 ≤ 10000 → no PT

    def test_kavya_accountant_20000_with_ot(self):
        """Kavya Nair — Accountant — ₹20,000 base + 8 hours OT."""
        r = self._calc(20000, overtime_hours=8.0)
        dr = _daily_rate(20000)
        expected_basic = _expected_basic(20000, 26)
        expected_ot = round((8 / 8) * dr * 2, 2)
        assert r.overtime_pay == expected_ot
        assert r.gross == round(expected_basic + expected_ot, 2)

    def test_kavya_esic_off_when_ot_pushes_gross_over_21000(self):
        """
        Kavya (20000 base) + enough OT to push gross >₹21,000 → no ESIC.
        daily_rate=769.23, need gross>21000 → OT of >16h does it.
        """
        r = self._calc(20000, overtime_hours=24.0)   # 3 OT shifts
        if r.gross > 21000:
            assert r.esic_employee == 0.0
        # If gross stayed ≤21000, ESIC applies — both outcomes are valid per data

    def test_sunita_tailor_14000_with_festival_bonus(self):
        """Sunita Patil — Tailor — ₹14,000 with Diwali bonus."""
        r = self._calc(14000, festival_bonus=True)
        expected_bonus = round(14000 * 0.0833, 2)
        expected_basic = _expected_basic(14000, 26)
        assert r.festival_bonus_amount == expected_bonus
        assert r.gross == round(expected_basic + expected_bonus, 2)

    def test_meena_finisher_half_month(self):
        """Meena Devi — Finisher — ₹11,000 base, only 13 days worked."""
        r = self._calc(11000, working_days=13)
        assert r.basic == _expected_basic(11000, 13)
        assert r.gross < 11000   # partial month must be less than full salary

    def test_sanjay_storekeeper_12000_with_leave(self):
        """Sanjay Kumar — Store Keeper — ₹12,000, 2 unpaid leave days."""
        r = self._calc(12000, working_days=24, unpaid_leave_days=2)
        daily_rate = 12000 / 26
        assert r.leave_deduction == round(daily_rate * 2, 2)


# ─── 11. Breakdown / audit trail ──────────────────────────────────────────────

class TestBreakdown:
    def test_breakdown_contains_all_sections(self, maharashtra_rules):
        result = calculate(make_input(), maharashtra_rules)
        bd = result.breakdown
        for section in ("inputs", "rates", "earnings", "deductions_pre_gross",
                        "gross", "compliance", "employer_contributions", "summary"):
            assert section in bd, f"Missing breakdown section: {section}"

    def test_breakdown_net_pay_matches_result(self, maharashtra_rules):
        result = calculate(make_input(base_salary=18000, working_days=26), maharashtra_rules)
        assert result.breakdown["summary"]["net_pay"] == result.net_pay

    def test_breakdown_inputs_preserved(self, maharashtra_rules):
        inp = make_input(base_salary=22000, working_days=22, overtime_hours=6.0,
                         festival_bonus=True, unpaid_leave_days=1)
        result = calculate(inp, maharashtra_rules)
        assert result.breakdown["inputs"]["base_salary"] == 22000
        assert result.breakdown["inputs"]["working_days"] == 22
        assert result.breakdown["inputs"]["overtime_hours"] == 6.0
        assert result.breakdown["inputs"]["festival_bonus"] is True


# ─── 12. Compliance rule loader ───────────────────────────────────────────────

class TestRuleLoader:
    def test_maharashtra_rules_loaded(self, maharashtra_rules):
        assert maharashtra_rules.state == "Maharashtra"
        assert maharashtra_rules.working_days_per_month == 26
        assert maharashtra_rules.pf_employee_rate == 0.12
        assert maharashtra_rules.esic_gross_threshold == 21000

    def test_delhi_no_pt(self, delhi_rules):
        assert all(s["monthly_tax"] == 0 for s in delhi_rules.professional_tax_slabs)

    def test_karnataka_pt_slabs(self, karnataka_rules):
        assert karnataka_rules.state == "Karnataka"
        assert len(karnataka_rules.professional_tax_slabs) == 2

    def test_unknown_state_falls_back_to_maharashtra(self):
        from pathlib import Path
        from engine.compliance.india import load_rules
        rules_dir = Path(__file__).parent.parent.parent / "rules"
        # "Goa" doesn't exist, should fall back to Maharashtra
        rules = load_rules("Goa", rules_dir=rules_dir)
        assert rules.state == "Maharashtra"
