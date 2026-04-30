// ── Company ───────────────────────────────────────────────────────────────

export interface Company {
  id: string;
  name: string;
  address: string | null;
  gstin: string | null;
  state: string;
  whatsapp_number: string | null;
  owner_phone: string | null;
  created_at: string;
}

export interface CompanyCreate {
  name: string;
  address?: string;
  gstin?: string;
  state: string;
  whatsapp_number?: string;
  owner_phone?: string;
}

// ── Employee ──────────────────────────────────────────────────────────────

export interface Employee {
  id: string;
  company_id: string;
  name: string;
  role: string | null;
  base_salary: number;
  phone_number: string | null;
  bank_account: string | null;
  bank_ifsc: string | null;
  pf_account: string | null;
  is_active: boolean;
  joined_at: string | null;
  created_at: string;
}

export interface EmployeeCreate {
  name: string;
  role?: string;
  base_salary: number;
  phone_number?: string;
  bank_account?: string;
  bank_ifsc?: string;
  pf_account?: string;
  joined_at?: string;
}

export interface EmployeeUpdate {
  name?: string;
  role?: string;
  base_salary?: number;
  phone_number?: string;
  bank_account?: string;
  bank_ifsc?: string;
  pf_account?: string;
  is_active?: boolean;
}

// ── Attendance ────────────────────────────────────────────────────────────

export type AttendanceStatus = "present" | "absent" | "half_day" | "holiday";
export type AttendanceSource = "whatsapp" | "qr_code" | "manual";

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  date: string;
  punch_in: string | null;
  punch_out: string | null;
  hours_worked: number | null;
  overtime_hours: number | null;
  status: AttendanceStatus;
  source: AttendanceSource;
  created_at: string;
}

export interface MonthlyAttendance {
  employee_id: string;
  employee_name: string;
  year: number;
  month: number;
  records: AttendanceRecord[];
  days_present: number;
  days_absent: number;
  total_overtime_hours: number;
}

export interface AttendanceManualCreate {
  employee_id: string;
  date: string;
  status: AttendanceStatus;
  punch_in?: string;
  punch_out?: string;
  overtime_hours?: number;
}

// ── Payroll ───────────────────────────────────────────────────────────────

export type PayrollRunStatus = "draft" | "approved" | "paid";

export interface PayrollRun {
  id: string;
  company_id: string;
  month: number;
  year: number;
  status: PayrollRunStatus;
  total_payout: number | null;
  run_at: string | null;
  created_by: string | null;
  created_at: string;
}

export interface PayrollLineItem {
  id: string;
  run_id: string;
  employee_id: string;
  basic: number;
  overtime_pay: number;
  leave_deduction: number;
  festival_bonus: number;
  gross: number;
  pf_employee: number;
  esic_employee: number;
  professional_tax: number;
  total_deductions: number;
  net_pay: number;
  snapshot: Record<string, unknown> | null;
  created_at: string;
}

export interface PayrollRunDetail extends PayrollRun {
  line_items: PayrollLineItem[];
}
