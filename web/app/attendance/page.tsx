"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { monthName } from "@/lib/utils";
import type { AttendanceStatus, AttendanceManualCreate } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

const STATUS_COLORS: Record<AttendanceStatus, string> = {
  present: "bg-emerald-500",
  absent: "bg-red-400",
  half_day: "bg-amber-400",
  holiday: "bg-slate-300",
};

const STATUS_LABELS: Record<AttendanceStatus, string> = {
  present: "P",
  absent: "A",
  half_day: "H",
  holiday: "Ho",
};

function daysInMonth(year: number, month: number) {
  return new Date(year, month, 0).getDate();
}

export default function AttendancePage() {
  const { company } = useCompany();
  const qc = useQueryClient();

  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  const { data: attendance = [], isLoading } = useQuery({
    queryKey: ["attendance", company?.id, year, month],
    queryFn: () => api.attendance.getMonthly(company!.id, year, month),
    enabled: !!company,
  });

  const { data: employees = [] } = useQuery({
    queryKey: ["employees", company?.id],
    queryFn: () => api.employees.list(company!.id),
    enabled: !!company,
  });

  // Mark attendance dialog state
  const [markOpen, setMarkOpen] = useState(false);
  const [markForm, setMarkForm] = useState<AttendanceManualCreate>({
    employee_id: "",
    date: new Date().toISOString().slice(0, 10),
    status: "present",
    overtime_hours: 0,
  });

  const markMutation = useMutation({
    mutationFn: api.attendance.markManual,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["attendance", company?.id, year, month] });
      setMarkOpen(false);
      toast.success("Attendance marked.");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "Failed to mark attendance.");
    },
  });

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  };

  const totalDays = daysInMonth(year, month);
  const dayNumbers = Array.from({ length: totalDays }, (_, i) => i + 1);

  // Build lookup: employee_id -> day -> status
  const statusMap: Record<string, Record<number, AttendanceStatus>> = {};
  for (const row of attendance) {
    statusMap[row.employee_id] = {};
    for (const rec of row.records) {
      const day = new Date(rec.date).getDate();
      statusMap[row.employee_id][day] = rec.status;
    }
  }

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
            Attendance
          </h1>
          <p className="text-slate-500 text-sm mt-2">Monthly grid view</p>
        </div>
        <Button
          className="bg-white text-black hover:bg-slate-100 font-semibold rounded-full px-6 shrink-0"
          onClick={() => {
            setMarkForm({ employee_id: employees[0]?.id ?? "", date: new Date().toISOString().slice(0, 10), status: "present", overtime_hours: 0 });
            setMarkOpen(true);
          }}
        >
          <CalendarDays className="w-4 h-4 mr-2" /> Mark attendance
        </Button>
      </div>

      {/* Month navigator */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <Button
          variant="ghost"
          size="icon"
          onClick={prevMonth}
          className="border border-white/10 text-slate-400 hover:bg-white/8 hover:text-white rounded-full"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <span className="text-sm font-bold uppercase tracking-widest text-white min-w-[160px] text-center">
          {monthName(month)} {year}
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={nextMonth}
          className="border border-white/10 text-slate-400 hover:bg-white/8 hover:text-white rounded-full"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>

        {/* Legend */}
        <div className="ml-4 flex items-center gap-4 text-[11px] text-slate-500">
          {(Object.keys(STATUS_COLORS) as AttendanceStatus[]).map((s) => (
            <span key={s} className="flex items-center gap-1.5 uppercase tracking-wider font-semibold">
              <span className={`w-2.5 h-2.5 rounded-sm ${STATUS_COLORS[s]}`} />
              {s.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-slate-600 text-sm">Loading…</div>
      ) : attendance.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center border border-white/8 rounded-2xl">
          <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">No records for this month</p>
          <p className="text-slate-600 text-sm mt-1">Use &ldquo;Mark attendance&rdquo; to add records.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-white/8 overflow-x-auto">
          <table className="text-xs min-w-max w-full">
            <thead>
              <tr className="border-b border-white/8">
                <th className="sticky left-0 bg-[#120F17] px-5 py-3 text-left font-bold text-[11px] uppercase tracking-widest text-slate-500 min-w-[160px]">
                  Employee
                </th>
                {dayNumbers.map((d) => (
                  <th key={d} className="px-1.5 py-3 text-center font-bold text-slate-600 w-8 text-[11px]">
                    {d}
                  </th>
                ))}
                <th className="px-3 py-3 text-center font-bold text-[11px] uppercase tracking-widest text-emerald-600">P</th>
                <th className="px-3 py-3 text-center font-bold text-[11px] uppercase tracking-widest text-red-500">A</th>
                <th className="px-3 py-3 text-center font-bold text-[11px] uppercase tracking-widest text-slate-500">OT</th>
              </tr>
            </thead>
            <tbody>
              {attendance.map((row, i) => (
                <tr key={row.employee_id} className={`border-b border-white/5 ${i % 2 === 0 ? "" : "bg-white/2"}`}>
                  <td className="sticky left-0 bg-[#120F17] px-5 py-2.5 font-semibold text-slate-200 border-r border-white/8">
                    {row.employee_name}
                  </td>
                  {dayNumbers.map((d) => {
                    const s = statusMap[row.employee_id]?.[d];
                    return (
                      <td key={d} className="px-1.5 py-2.5 text-center">
                        {s ? (
                          <span
                            className={`inline-flex items-center justify-center w-6 h-6 rounded text-white font-bold text-[9px] ${STATUS_COLORS[s]}`}
                            title={s}
                          >
                            {STATUS_LABELS[s]}
                          </span>
                        ) : (
                          <span className="inline-block w-6 h-6 rounded border border-dashed border-white/10" />
                        )}
                      </td>
                    );
                  })}
                  <td className="px-3 py-2.5 text-center font-bold text-emerald-400">{row.days_present}</td>
                  <td className="px-3 py-2.5 text-center font-bold text-red-400">{row.days_absent}</td>
                  <td className="px-3 py-2.5 text-center text-slate-500">{row.total_overtime_hours.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Mark Attendance Dialog */}
      <Dialog open={markOpen} onOpenChange={setMarkOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Mark Attendance</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>Employee <span className="text-red-500">*</span></Label>
              <Select
                value={markForm.employee_id}
                onValueChange={(v) => setMarkForm({ ...markForm, employee_id: v ?? "" })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((e) => (
                    <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Date <span className="text-red-500">*</span></Label>
              <Input
                type="date"
                value={markForm.date}
                onChange={(e) => setMarkForm({ ...markForm, date: e.target.value })}
              />
            </div>

            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select
                value={markForm.status}
                onValueChange={(v) => setMarkForm({ ...markForm, status: v as AttendanceStatus })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="present">Present</SelectItem>
                  <SelectItem value="absent">Absent</SelectItem>
                  <SelectItem value="half_day">Half Day</SelectItem>
                  <SelectItem value="holiday">Holiday</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {markForm.status === "present" && (
              <div className="space-y-1.5">
                <Label>Overtime Hours</Label>
                <Input
                  type="number" min="0" step="0.5" placeholder="0"
                  value={markForm.overtime_hours ?? 0}
                  onChange={(e) => setMarkForm({ ...markForm, overtime_hours: parseFloat(e.target.value) || 0 })}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMarkOpen(false)}>Cancel</Button>
            <Button
              className="bg-indigo-600 hover:bg-indigo-700"
              onClick={() => markMutation.mutate(markForm)}
              disabled={markMutation.isPending || !markForm.employee_id || !markForm.date}
            >
              {markMutation.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
