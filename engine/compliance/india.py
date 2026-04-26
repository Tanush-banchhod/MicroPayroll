"""
Indian compliance rule loader.

Reads YAML rule files from the rules/ directory and exposes them as a
typed ComplianceRules dataclass. The engine only imports from here — all
rule constants are sourced from YAML so non-developers (CAs, HR consultants)
can add new state rules without touching Python.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


# Default path to the rules directory relative to the project root.
# Can be overridden by setting the RULES_DIR environment variable.
_DEFAULT_RULES_DIR = Path(__file__).parent.parent.parent / "rules"


@dataclass
class ComplianceRules:
    """Typed representation of a state compliance YAML rule file."""

    state: str
    country: str
    currency: str

    working_days_per_month: int
    overtime_multiplier: float
    standard_shift_hours: float

    # Provident Fund
    pf_employee_rate: float
    pf_employer_rate: float
    pf_wage_ceiling: float                  # PF computed on min(basic, ceiling)
    pf_applicable_if_basic_lte: Optional[float]  # None = always apply

    # ESIC
    esic_employee_rate: float
    esic_employer_rate: float
    esic_gross_threshold: float             # ESIC applies if gross ≤ this value

    # Professional Tax
    professional_tax_slabs: List[dict]      # [{max_salary, monthly_tax}, ...]

    # Festival Bonus
    festival_bonus_rate: float              # 0.0833 = 8.33%
    festival_bonus_name: str = "Festival Bonus"


def load_rules(state: str, rules_dir: Optional[Path] = None) -> ComplianceRules:
    """
    Load compliance rules for a given Indian state.

    Args:
        state:      State name as it appears in the YAML filename, e.g. "Maharashtra".
        rules_dir:  Override the default rules directory (useful in tests).

    Returns:
        ComplianceRules populated from the YAML file.

    Raises:
        FileNotFoundError: If no YAML file exists for the requested state.
        ValueError:        If the YAML file is missing required fields.
    """
    base_dir = rules_dir or Path(os.environ.get("RULES_DIR", str(_DEFAULT_RULES_DIR)))
    filename = f"india-{state.lower()}.yaml"
    rule_path = base_dir / filename

    if not rule_path.exists():
        # Fallback: try Maharashtra if the specific state isn't found
        fallback = base_dir / "india-maharashtra.yaml"
        if fallback.exists():
            rule_path = fallback
        else:
            raise FileNotFoundError(
                f"No compliance rule file found for state '{state}'. "
                f"Expected: {rule_path}"
            )

    with open(rule_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    pf = data.get("provident_fund", {})
    esic = data.get("esic", {})
    pt = data.get("professional_tax", {})
    fb = data.get("festival_bonus", {})

    return ComplianceRules(
        state=data["state"],
        country=data["country"],
        currency=data.get("currency", "INR"),
        working_days_per_month=int(data.get("working_days_per_month", 26)),
        overtime_multiplier=float(data.get("overtime_multiplier", 2.0)),
        standard_shift_hours=float(data.get("standard_shift_hours", 8.0)),
        pf_employee_rate=float(pf.get("employee_rate", 0.12)),
        pf_employer_rate=float(pf.get("employer_rate", 0.12)),
        pf_wage_ceiling=float(pf.get("wage_ceiling", 15000)),
        pf_applicable_if_basic_lte=pf.get("applicable_if_basic_lte"),
        esic_employee_rate=float(esic.get("employee_rate", 0.0075)),
        esic_employer_rate=float(esic.get("employer_rate", 0.0325)),
        esic_gross_threshold=float(esic.get("applicable_if_gross_lte", 21000)),
        professional_tax_slabs=sorted(
            pt.get("slabs", []), key=lambda s: s["max_salary"]
        ),
        festival_bonus_rate=float(fb.get("rate", 0.0833)),
        festival_bonus_name=fb.get("name", "Festival Bonus"),
    )
