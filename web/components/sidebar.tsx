"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Users, CalendarDays, IndianRupee, Building2, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCompany } from "@/lib/company-context";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/attendance", label: "Attendance", icon: CalendarDays },
  { href: "/payroll", label: "Payroll", icon: IndianRupee },
];

export function Sidebar() {
  const pathname = usePathname();
  const { company } = useCompany();

  return (
    <aside className="w-56 shrink-0 border-r border-white/8 bg-[#120F17] flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/8">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
            <IndianRupee className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white text-sm tracking-tight">MicroPayroll</span>
        </div>
      </div>

      {/* Company chip */}
      {company && (
        <div className="mx-3 mt-3 px-3 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
          <p className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wide">Active company</p>
          <p className="text-xs font-semibold text-indigo-200 truncate mt-0.5">{company.name}</p>
          <p className="text-[10px] text-indigo-400">{company.state}</p>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-indigo-600/90 text-white"
                  : "text-slate-400 hover:bg-white/6 hover:text-slate-200"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-white/8">
        <Link
          href="/settings"
          className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          <Building2 className="w-3.5 h-3.5" />
          Company settings
        </Link>
      </div>
    </aside>
  );
}
