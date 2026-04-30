"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { fmtInr, monthName, MONTH_OPTIONS } from "@/lib/utils";
import type { PayrollRunDetail, PayrollLineItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  Play, CheckCircle2, Download, FileText, IndianRupee,
  ChevronDown, ChevronRight, AlertCircle,
} from "lucide-react";
import Link from "next/link";

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-amber-100 text-amber-700" },
  approved: { label: "Approved", className: "bg-blue-100 text-blue-700" },
  paid: { label: "Paid", className: "bg-emerald-100 text-emerald-700" },
};

const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

export default function PayrollPage() {
  const { company } = useCompany();
  const qc = useQueryClient();

  const { data: employees = [] } = useQuery({
    queryKey: ["employees", company?.id],
    queryFn: () => api.employees.list(company!.id),
    enabled: !!company,
  });

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["payroll-runs", company?.id],
    queryFn: () => api.payroll.listRuns(company!.id),
    enabled: !!company,
  });

  const now = new Date();
  const [newMonth, setNewMonth] = useState(now.getMonth() + 1);
  const [newYear, setNewYear] = useState(now.getFullYear());
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [selectedRun, setSelectedRun] = useState<PayrollRunDetail | null>(null);
  const [expandedEmployee, setExpandedEmployee] = useState<string | null>(null);

  const employeeMap: Record<string, string> = {};
  for (const e of employees) employeeMap[e.id] = e.name;

  const createMutation = useMutation({
    mutationFn: () => api.payroll.createRun(company!.id, newMonth, newYear),
    onSuccess: (run) => {
      qc.invalidateQueries({ queryKey: ["payroll-runs", company?.id] });
      setRunDialogOpen(false);
      setSelectedRun(run);
      toast.success(`Payroll run for ${monthName(run.month)} ${run.year} created.`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "Failed to create payroll run.");
    },
  });

  const approveMutation = useMutation({
    mutationFn: (runId: string) => api.payroll.approveRun(runId),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ["payroll-runs", company?.id] });
      if (selectedRun) setSelectedRun({ ...selectedRun, status: updated.status });
      toast.success("Payroll approved!");
    },
    onError: () => toast.error("Failed to approve payroll run."),
  });

  const loadRun = async (runId: string) => {
    try {
      const detail = await api.payroll.getRun(runId);
      setSelectedRun(detail);
    } catch {
      toast.error("Failed to load payroll run.");
    }
  };

  if (!company) {
    return (
      <div className="min-h-screen bg-[#120F17] flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500 mb-4 text-sm">No company selected.</p>
          <Link href="/settings">
            <Button className="bg-white text-black hover:bg-slate-100 rounded-full font-semibold">Set up company</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#120F17] px-10 md:px-20 py-16">
      {/* Page header */}
      <div className="mb-10 border-b border-white/8 pb-8 flex items-end justify-between">
        <div>
          <p className="text-xs font-semibold tracking-[0.2em] uppercase text-indigo-400 mb-3">
            {company.name}
          </p>
          <h1
            className="font-black uppercase leading-none tracking-[-2px] text-white"
            style={{ fontSize: "clamp(2rem, 5vw, 5rem)" }}
          >
            Payroll
          </h1>
          <p className="text-slate-500 text-sm mt-2">Run monthly payroll and download payslips.</p>
        </div>
        <Button
          className="bg-white text-black hover:bg-slate-100 font-semibold rounded-full px-6 shrink-0"
          onClick={() => setRunDialogOpen(true)}
        >
          <Play className="w-4 h-4 mr-2" /> Run payroll
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Run list */}
        <div className="col-span-1 space-y-2">
          <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-600 mb-3">All Runs</p>
          {isLoading ? (
            <p className="text-sm text-slate-600">Loading…</p>
          ) : runs.length === 0 ? (
            <p className="text-sm text-slate-600">No payroll runs yet.</p>
          ) : (
            runs.map((run) => {
              const badge = STATUS_BADGE[run.status];
              const isSelected = selectedRun?.id === run.id;
              return (
                <button
                  key={run.id}
                  onClick={() => loadRun(run.id)}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-colors ${
                    isSelected
                      ? "border-indigo-500/60 bg-indigo-500/10"
                      : "border-white/8 bg-white/3 hover:bg-white/6 hover:border-white/15"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-bold uppercase tracking-wide text-white">
                      {monthName(run.month)} {run.year}
                    </p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest border ${
                      run.status === "draft" ? "border-amber-500/30 text-amber-400" :
                      run.status === "approved" ? "border-blue-500/30 text-blue-400" :
                      "border-emerald-500/30 text-emerald-400"
                    }`}>
                      {badge.label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 tabular-nums">
                    {run.total_payout != null ? fmtInr(run.total_payout) : "Calculating…"}
                  </p>
                </button>
              );
            })
          )}
        </div>

        {/* Run detail */}
        <div className="col-span-2">
          {!selectedRun ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-24 border border-white/8 rounded-2xl">
              <IndianRupee className="w-8 h-8 text-slate-700 mb-3" />
              <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">Select a run to view details</p>
              <p className="text-slate-600 text-sm mt-1">or click &ldquo;Run payroll&rdquo; to create a new one.</p>
            </div>
          ) : (
            <RunDetail
              run={selectedRun}
              employeeMap={employeeMap}
              expandedEmployee={expandedEmployee}
              setExpandedEmployee={setExpandedEmployee}
              onApprove={() => approveMutation.mutate(selectedRun.id)}
              isApproving={approveMutation.isPending}
            />
          )}
        </div>
      </div>

      {/* New Run Dialog */}
      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent className="max-w-sm bg-[#1a1720] border-white/10 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-white">Run Payroll</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="flex items-center gap-2 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <p className="text-xs text-amber-300">
                Payroll will be calculated from attendance records for the selected month.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Month</Label>
                <Select value={String(newMonth)} onValueChange={(v) => setNewMonth(Number(v))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {MONTH_OPTIONS.map((m) => (
                      <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Year</Label>
                <Select value={String(newYear)} onValueChange={(v) => setNewYear(Number(v))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {YEAR_OPTIONS.map((y) => (
                      <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRunDialogOpen(false)}>Cancel</Button>
            <Button
              className="bg-indigo-600 hover:bg-indigo-700"
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Calculating…" : `Run ${monthName(newMonth)} ${newYear}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RunDetail({
  run,
  employeeMap,
  expandedEmployee,
  setExpandedEmployee,
  onApprove,
  isApproving,
}: {
  run: PayrollRunDetail;
  employeeMap: Record<string, string>;
  expandedEmployee: string | null;
  setExpandedEmployee: (id: string | null) => void;
  onApprove: () => void;
  isApproving: boolean;
}) {
  const badge = STATUS_BADGE[run.status];

  return (
    <div className="space-y-4">
      {/* Run header */}
      <div className="border border-white/8 rounded-2xl px-6 py-5 bg-white/3">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-black uppercase tracking-tight text-white">
              {monthName(run.month)} {run.year}
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              {run.run_at ? new Date(run.run_at).toLocaleString("en-IN") : "—"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-black text-white tabular-nums">
              {run.total_payout != null ? fmtInr(run.total_payout) : "—"}
            </p>
            <p className="text-[11px] uppercase tracking-widest text-slate-600 mt-0.5">Total net payout</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest border ${
            run.status === "draft" ? "border-amber-500/30 text-amber-400" :
            run.status === "approved" ? "border-blue-500/30 text-blue-400" :
            "border-emerald-500/30 text-emerald-400"
          }`}>
            {badge.label}
          </span>

          {run.status === "draft" && (
            <Button
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-full"
              onClick={onApprove}
              disabled={isApproving}
            >
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
              {isApproving ? "Approving…" : "Approve run"}
            </Button>
          )}

          <a href={api.payroll.bankExportUrl(run.id)} download className="ml-auto">
            <Button
              variant="ghost"
              size="sm"
              className="border border-white/10 text-slate-400 hover:bg-white/8 hover:text-white rounded-full"
            >
              <Download className="w-3.5 h-3.5 mr-1.5" /> Bank CSV
            </Button>
          </a>
        </div>
      </div>

      {/* Line items */}
      <div className="rounded-2xl border border-white/8 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Employee</th>
              <th className="px-3 py-3 text-right text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Basic</th>
              <th className="px-3 py-3 text-right text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">OT</th>
              <th className="px-3 py-3 text-right text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Gross</th>
              <th className="px-3 py-3 text-right text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Deductions</th>
              <th className="px-3 py-3 text-right text-[11px] font-bold uppercase tracking-widest text-white bg-white/3">Net Pay</th>
              <th className="px-3 py-3 text-center text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Payslip</th>
            </tr>
          </thead>
          <tbody>
            {run.line_items.map((item, i) => {
              const name = employeeMap[item.employee_id] ?? "Unknown";
              const isExpanded = expandedEmployee === item.employee_id;

              return (
                <>
                  <tr
                    key={item.id}
                    className={`border-b border-white/5 hover:bg-white/4 cursor-pointer transition-colors ${i % 2 === 0 ? "" : "bg-white/2"}`}
                    onClick={() => setExpandedEmployee(isExpanded ? null : item.employee_id)}
                  >
                    <td className="px-4 py-2.5 font-semibold text-slate-200">
                      <span className="flex items-center gap-1.5">
                        {isExpanded
                          ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                          : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
                        {name}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-slate-400 tabular-nums">{fmtInr(item.basic)}</td>
                    <td className="px-3 py-2.5 text-right text-slate-400 tabular-nums">
                      {item.overtime_pay > 0 ? fmtInr(item.overtime_pay) : <span className="text-slate-700">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-right text-slate-300 font-semibold tabular-nums">{fmtInr(item.gross)}</td>
                    <td className="px-3 py-2.5 text-right text-red-400 tabular-nums">
                      {item.total_deductions > 0 ? `−${fmtInr(item.total_deductions)}` : <span className="text-slate-700">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-right font-black text-white tabular-nums">{fmtInr(item.net_pay)}</td>
                    <td className="px-3 py-2.5 text-center">
                      <a
                        href={api.payroll.payslipUrl(run.id, item.employee_id)}
                        download
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10">
                          <FileText className="w-3.5 h-3.5" />
                        </Button>
                      </a>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr key={`${item.id}-detail`} className="bg-indigo-500/5 border-b border-white/5">
                      <td colSpan={7} className="px-6 py-4">
                        <BreakdownTable item={item} />
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BreakdownTable({ item }: { item: PayrollLineItem }) {
  const snap = item.snapshot ?? {};
  return (
    <div className="grid grid-cols-2 gap-6 text-xs">
      <div>
        <p className="font-bold text-[11px] uppercase tracking-widest text-slate-500 mb-2">Earnings</p>
        <div className="space-y-1">
          <Row label="Basic Pay" value={fmtInr(item.basic)} />
          {item.overtime_pay > 0 && <Row label="Overtime Pay" value={fmtInr(item.overtime_pay)} positive />}
          {item.festival_bonus > 0 && <Row label="Festival Bonus" value={fmtInr(item.festival_bonus)} positive />}
          {item.leave_deduction > 0 && <Row label="Leave Deduction" value={`−${fmtInr(item.leave_deduction)}`} negative />}
          <Separator className="my-1 bg-white/8" />
          <Row label="Gross Pay" value={fmtInr(item.gross)} bold />
        </div>
      </div>
      <div>
        <p className="font-bold text-[11px] uppercase tracking-widest text-slate-500 mb-2">Deductions</p>
        <div className="space-y-1">
          {item.pf_employee > 0 && <Row label="Provident Fund (12%)" value={fmtInr(item.pf_employee)} />}
          {item.esic_employee > 0 && <Row label="ESIC (0.75%)" value={fmtInr(item.esic_employee)} />}
          {item.professional_tax > 0 && <Row label="Professional Tax" value={fmtInr(item.professional_tax)} />}
          <Separator className="my-1 bg-white/8" />
          <Row label="Total Deductions" value={fmtInr(item.total_deductions)} bold negative />
          <Row label="Net Pay" value={fmtInr(item.net_pay)} bold />
          {snap.cost_to_company != null && (
            <Row label="Cost to Company" value={fmtInr(snap.cost_to_company as number)} />
          )}
        </div>
      </div>
    </div>
  );
}

function Row({
  label, value, bold, positive, negative,
}: {
  label: string; value: string; bold?: boolean; positive?: boolean; negative?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className={`tabular-nums ${bold ? "text-white font-bold" : "text-slate-400"} ${positive ? "text-emerald-400" : ""} ${negative ? "text-red-400" : ""}`}>
        {value}
      </span>
    </div>
  );
}
