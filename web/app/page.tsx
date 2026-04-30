"use client";

import { useCompany } from "@/lib/company-context";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { fmtInr, monthName } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Users, IndianRupee, CalendarDays, TrendingUp,
  ArrowRight, AlertCircle,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

export default function OverviewPage() {
  const { company } = useCompany();

  const { data: employees = [] } = useQuery({
    queryKey: ["employees", company?.id],
    queryFn: () => api.employees.list(company!.id),
    enabled: !!company,
  });

  const { data: runs = [] } = useQuery({
    queryKey: ["payroll-runs", company?.id],
    queryFn: () => api.payroll.listRuns(company!.id),
    enabled: !!company,
  });

  const now = new Date();
  const currentMonth = now.getMonth() + 1;
  const currentYear = now.getFullYear();

  const { data: attendance = [] } = useQuery({
    queryKey: ["attendance", company?.id, currentYear, currentMonth],
    queryFn: () => api.attendance.getMonthly(company!.id, currentYear, currentMonth),
    enabled: !!company,
  });

  // ── No company — welcome screen ───────────────────────────────────────
  if (!company) {
    return (
      <div className="min-h-screen bg-[#120F17] flex flex-col px-10 py-16 md:px-20">
        {/* Eyebrow */}
        <p className="text-xs font-semibold tracking-[0.2em] uppercase text-indigo-400 mb-6">
          MicroPayroll
        </p>

        {/* Hero headline — matches menu's bold uppercase scale */}
        <h1
          className="font-black uppercase leading-[0.9] tracking-[-3px] text-white"
          style={{ fontSize: "clamp(3.5rem, 10vw, 9rem)" }}
        >
          Payroll
          <br />
          <span className="text-indigo-500">Made</span>
          <br />
          Simple.
        </h1>

        <p className="mt-8 text-slate-400 text-lg max-w-md leading-relaxed">
          Built for micro-businesses. Calculate salaries, track attendance, and
          export bank transfers — in minutes, not hours.
        </p>

        <div className="mt-12 flex items-center gap-4">
          <Link href="/settings">
            <Button className="bg-white text-black hover:bg-slate-100 font-semibold h-11 px-7 text-sm rounded-full">
              Set up company <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-slate-500 hover:text-slate-300 transition-colors underline underline-offset-4"
          >
            View on GitHub
          </a>
        </div>

        {/* Decorative rule at bottom */}
        <div className="mt-auto pt-20 border-t border-white/8 flex items-center gap-6">
          {["Open Source", "Self-Hostable", "India Compliance"].map((tag) => (
            <span key={tag} className="text-xs font-semibold uppercase tracking-widest text-slate-600">
              {tag}
            </span>
          ))}
        </div>
      </div>
    );
  }

  // ── Dashboard ─────────────────────────────────────────────────────────
  const latestRun = runs[0];
  const totalPresent = attendance.reduce((s, a) => s + a.days_present, 0);
  const totalOt = attendance.reduce((s, a) => s + a.total_overtime_hours, 0);
  const pendingRun = runs.find((r) => r.status === "draft");

  return (
    <div className="min-h-screen bg-[#120F17] px-10 md:px-20 py-16">

      {/* ── Page header ── */}
      <div className="mb-12 border-b border-white/8 pb-8">
        <p className="text-xs font-semibold tracking-[0.2em] uppercase text-indigo-400 mb-3">
          Overview
        </p>
        <h1
          className="font-black uppercase leading-none tracking-[-2px] text-white"
          style={{ fontSize: "clamp(2.5rem, 6vw, 6rem)" }}
        >
          {company.name}
        </h1>
        <p className="text-slate-500 text-sm mt-3 tracking-wide">
          {company.state} {company.address ? `· ${company.address}` : ""}
        </p>
      </div>

      {/* ── Pending approval alert ── */}
      {pendingRun && (
        <div className="mb-10 flex items-center gap-4 border border-amber-500/30 bg-amber-500/5 rounded-2xl px-5 py-4">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <p className="text-sm text-amber-200 flex-1">
            Payroll for{" "}
            <strong className="text-amber-100 font-semibold">
              {monthName(pendingRun.month)} {pendingRun.year}
            </strong>{" "}
            is a draft — review and approve it.
          </p>
          <Link href="/payroll">
            <Button
              size="sm"
              variant="outline"
              className="border-amber-500/40 text-amber-300 hover:bg-amber-500/10 bg-transparent rounded-full text-xs"
            >
              Review <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          </Link>
        </div>
      )}

      {/* ── Stat strip ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/8 rounded-2xl overflow-hidden mb-12">
        <StatCell
          icon={<Users className="w-4 h-4" />}
          label="Employees"
          value={String(employees.length)}
        />
        <StatCell
          icon={<IndianRupee className="w-4 h-4" />}
          label="Last Payout"
          value={latestRun?.total_payout != null ? fmtInr(latestRun.total_payout) : "—"}
          sub={latestRun ? `${monthName(latestRun.month)} ${latestRun.year}` : undefined}
        />
        <StatCell
          icon={<CalendarDays className="w-4 h-4" />}
          label="Present This Month"
          value={String(totalPresent)}
          sub={`${monthName(currentMonth)} ${currentYear}`}
        />
        <StatCell
          icon={<TrendingUp className="w-4 h-4" />}
          label="Overtime Hours"
          value={`${totalOt.toFixed(1)}h`}
          sub="This month"
        />
      </div>

      {/* ── Recent payroll runs ── */}
      <div>
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">
            Recent Payroll Runs
          </h2>
          <Link href="/payroll">
            <Button
              variant="ghost"
              size="sm"
              className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 text-xs rounded-full"
            >
              View all <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </Link>
        </div>

        {runs.length === 0 ? (
          <div className="py-16 text-center border border-white/8 rounded-2xl">
            <p className="text-slate-600 text-sm">No payroll runs yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/8 border border-white/8 rounded-2xl overflow-hidden">
            {runs.slice(0, 6).map((run) => (
              <div key={run.id} className="flex items-center justify-between px-6 py-4 hover:bg-white/3 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-white uppercase tracking-wide">
                    {monthName(run.month)} {run.year}
                  </p>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {run.run_at
                      ? new Date(run.run_at).toLocaleDateString("en-IN")
                      : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-bold text-slate-200 tabular-nums">
                    {run.total_payout != null ? fmtInr(run.total_payout) : "—"}
                  </span>
                  <RunStatusBadge status={run.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

function StatCell({
  icon, label, value, sub,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-[#120F17] px-6 py-6 flex flex-col gap-3">
      <div className="text-slate-600">{icon}</div>
      <div>
        <p className="text-2xl font-black text-white tracking-tight">{value}</p>
        {sub && <p className="text-[11px] text-slate-600 mt-0.5 tabular-nums">{sub}</p>}
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 mt-1">{label}</p>
      </div>
    </div>
  );
}

function RunStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    draft: "border-amber-500/30 text-amber-400",
    approved: "border-blue-500/30 text-blue-400",
    paid: "border-emerald-500/30 text-emerald-400",
  };
  return (
    <span
      className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-widest border ${
        map[status] ?? "border-slate-500/30 text-slate-500"
      }`}
    >
      {status}
    </span>
  );
}
