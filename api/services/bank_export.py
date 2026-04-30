"""Bank export service — generates NEFT-ready bulk payment CSV.

Column layout matches the format accepted by most Indian bank portals
for NEFT/RTGS bulk upload (SBI, HDFC, ICICI, Kotak):

  Employee Name, Account Number, IFSC Code, Amount, Remarks

The CSV is returned as a string. The caller is responsible for streaming
it to the HTTP response with the appropriate Content-Disposition header.
"""

import csv
import calendar
import io
from typing import Any


def build_bank_csv(
    *,
    employees_by_id: dict[str, Any],
    line_items: list[Any],
    month: int,
    year: int,
) -> str:
    """Build a NEFT bulk-transfer CSV for all line items in a payroll run.

    Args:
        employees_by_id: Mapping of str(employee_id) → Employee ORM instance.
        line_items: List of PayrollLineItem ORM instances for the run.
        month: Payroll month (1–12).
        year: Payroll year.

    Returns:
        A UTF-8 CSV string with a header row followed by one row per employee.
    """
    month_label = f"{calendar.month_abbr[month]}{year}"
    remarks_prefix = f"Salary {month_label}"

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    writer.writerow(["Employee Name", "Account Number", "IFSC Code", "Amount", "Remarks"])

    for item in line_items:
        emp = employees_by_id.get(str(item.employee_id))
        if emp is None:
            continue

        writer.writerow([
            emp.name,
            emp.bank_account or "",
            emp.bank_ifsc or "",
            f"{item.net_pay:.2f}",
            f"{remarks_prefix} - {emp.name}",
        ])

    return output.getvalue()
