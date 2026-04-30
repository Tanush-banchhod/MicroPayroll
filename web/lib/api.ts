import axios from "axios";
import type {
  Company,
  CompanyCreate,
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
  MonthlyAttendance,
  AttendanceManualCreate,
  AttendanceRecord,
  PayrollRun,
  PayrollRunDetail,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const http = axios.create({ baseURL: BASE_URL });

// ── Companies ─────────────────────────────────────────────────────────────

export const api = {
  companies: {
    create: (data: CompanyCreate): Promise<Company> =>
      http.post("/api/companies", data).then((r) => r.data),

    list: (): Promise<Company[]> =>
      http.get("/api/companies").then((r) => r.data),

    get: (id: string): Promise<Company> =>
      http.get(`/api/companies/${id}`).then((r) => r.data),
  },

  // ── Employees ──────────────────────────────────────────────────────────

  employees: {
    create: (companyId: string, data: EmployeeCreate): Promise<Employee> =>
      http
        .post("/api/employees", data, { params: { company_id: companyId } })
        .then((r) => r.data),

    list: (companyId: string, activeOnly = true): Promise<Employee[]> =>
      http
        .get("/api/employees", {
          params: { company_id: companyId, active_only: activeOnly },
        })
        .then((r) => r.data),

    get: (id: string): Promise<Employee> =>
      http.get(`/api/employees/${id}`).then((r) => r.data),

    update: (id: string, data: EmployeeUpdate): Promise<Employee> =>
      http.patch(`/api/employees/${id}`, data).then((r) => r.data),

    deactivate: (id: string): Promise<void> =>
      http.delete(`/api/employees/${id}`).then(() => undefined),
  },

  // ── Attendance ─────────────────────────────────────────────────────────

  attendance: {
    markManual: (data: AttendanceManualCreate): Promise<AttendanceRecord> =>
      http.post("/api/attendance/manual", data).then((r) => r.data),

    getMonthly: (
      companyId: string,
      year: number,
      month: number
    ): Promise<MonthlyAttendance[]> =>
      http
        .get(`/api/attendance/${year}/${month}`, {
          params: { company_id: companyId },
        })
        .then((r) => r.data),
  },

  // ── Payroll ────────────────────────────────────────────────────────────

  payroll: {
    createRun: (
      companyId: string,
      month: number,
      year: number
    ): Promise<PayrollRunDetail> =>
      http
        .post("/api/payroll/runs", { company_id: companyId, month, year })
        .then((r) => r.data),

    listRuns: (companyId: string): Promise<PayrollRun[]> =>
      http
        .get("/api/payroll/runs", { params: { company_id: companyId } })
        .then((r) => r.data),

    getRun: (runId: string): Promise<PayrollRunDetail> =>
      http.get(`/api/payroll/runs/${runId}`).then((r) => r.data),

    approveRun: (runId: string): Promise<PayrollRun> =>
      http.patch(`/api/payroll/runs/${runId}/approve`).then((r) => r.data),

    payslipUrl: (runId: string, employeeId: string): string =>
      `${BASE_URL}/api/payroll/runs/${runId}/payslip/${employeeId}`,

    bankExportUrl: (runId: string): string =>
      `${BASE_URL}/api/payroll/runs/${runId}/bank-export`,
  },
};
