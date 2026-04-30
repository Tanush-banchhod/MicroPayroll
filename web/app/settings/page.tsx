"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { INDIAN_STATES } from "@/lib/utils";
import type { CompanyCreate } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { CheckCircle2, ChevronRight, ArrowRight, ChevronDown, Check } from "lucide-react";

export default function SettingsPage() {
  const { company, setCompany } = useCompany();
  const qc = useQueryClient();

  const { data: companies = [], isLoading } = useQuery({
    queryKey: ["companies"],
    queryFn: api.companies.list,
  });

  const [form, setForm] = useState<CompanyCreate>({
    name: "",
    address: "",
    gstin: "",
    state: "Maharashtra",
    whatsapp_number: "",
    owner_phone: "",
  });

  const createMutation = useMutation({
    mutationFn: api.companies.create,
    onSuccess: (c) => {
      setCompany(c);
      qc.invalidateQueries({ queryKey: ["companies"] });
      toast.success(`${c.name} created and set as active company.`);
      setForm({ name: "", address: "", gstin: "", state: "Maharashtra", whatsapp_number: "", owner_phone: "" });
    },
    onError: () => toast.error("Failed to create company. Please try again."),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    createMutation.mutate(form);
  };

  return (
    <div className="min-h-screen bg-[#120F17] px-10 md:px-20 py-16">

      {/* ── Page header ── */}
      <div className="mb-16 border-b border-white/8 pb-10">
        <p className="text-xs font-semibold tracking-[0.2em] uppercase text-indigo-400 mb-4">
          Configuration
        </p>
        <h1
          className="font-black uppercase leading-none tracking-[-3px] text-white"
          style={{ fontSize: "clamp(3rem, 7vw, 7rem)" }}
        >
          Settings
        </h1>
        <p className="text-slate-500 text-sm mt-4 max-w-sm leading-relaxed">
          Manage your active company or register a new one to start running payroll.
        </p>
      </div>

      <div className="max-w-3xl space-y-20">

        {/* ── Your companies ── */}
        {(isLoading || companies.length > 0) && (
          <section>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-600 mb-6">
              Your Companies
            </p>
            {isLoading ? (
              <p className="text-slate-700 text-sm">Loading…</p>
            ) : (
              <div className="divide-y divide-white/6">
                {companies.map((c, idx) => {
                  const isActive = company?.id === c.id;
                  return (
                    <button
                      key={c.id}
                      onClick={() => { setCompany(c); toast.success(`Switched to ${c.name}`); }}
                      className="group w-full flex items-center justify-between py-5 text-left transition-all"
                    >
                      <div className="flex items-baseline gap-5">
                        <span className="text-[11px] font-black tabular-nums text-slate-700 group-hover:text-indigo-500 transition-colors w-5 shrink-0">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <p
                            className="font-black uppercase tracking-tight text-white group-hover:text-indigo-200 transition-colors"
                            style={{ fontSize: "clamp(1.1rem, 2.5vw, 1.75rem)", letterSpacing: "-0.04em" }}
                          >
                            {c.name}
                          </p>
                          <p className="text-xs text-slate-600 mt-1 tracking-wide">
                            {c.state}{c.gstin ? ` · ${c.gstin}` : ""}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        {isActive ? (
                          <span className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.15em] text-emerald-400 border border-emerald-500/25 px-3 py-1.5 rounded-full">
                            <CheckCircle2 className="w-3 h-3" /> Active
                          </span>
                        ) : (
                          <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-700 group-hover:text-slate-400 transition-colors">
                            Switch
                          </span>
                        )}
                        <ChevronRight className="w-4 h-4 text-slate-700 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* ── Create new company ── */}
        <section>
          <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-600 mb-6">
            New Company
          </p>

          <form onSubmit={handleSubmit}>
            <div className="divide-y divide-white/6">

              <FormRow label="Company Name" required>
                <input
                  placeholder="e.g. Sharma Garments"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  className="w-full bg-transparent text-white placeholder:text-slate-700 focus:outline-none font-semibold text-lg py-5 pr-4"
                  style={{ letterSpacing: "-0.02em" }}
                />
              </FormRow>

              <FormRow label="Address">
                <input
                  placeholder="Shop / office address"
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  className="w-full bg-transparent text-white placeholder:text-slate-700 focus:outline-none font-semibold text-lg py-5 pr-4"
                  style={{ letterSpacing: "-0.02em" }}
                />
              </FormRow>

              {/* State — fully custom inline dropdown */}
              <StateRow
                value={form.state}
                onChange={(v) => setForm({ ...form, state: v })}
              />

              <FormRow label="GSTIN">
                <input
                  placeholder="22AAAAA0000A1Z5"
                  value={form.gstin}
                  onChange={(e) => setForm({ ...form, gstin: e.target.value.toUpperCase() })}
                  maxLength={15}
                  className="w-full bg-transparent text-white placeholder:text-slate-700 focus:outline-none font-mono font-semibold text-lg py-5 pr-4 tracking-wider"
                />
              </FormRow>

              <FormRow label="Owner Phone">
                <input
                  placeholder="+91 98765 43210"
                  value={form.owner_phone}
                  onChange={(e) => setForm({ ...form, owner_phone: e.target.value })}
                  className="w-full bg-transparent text-white placeholder:text-slate-700 focus:outline-none font-semibold text-lg py-5 pr-4"
                  style={{ letterSpacing: "-0.02em" }}
                />
              </FormRow>

              <FormRow label="WhatsApp">
                <input
                  placeholder="+91 98765 43210"
                  value={form.whatsapp_number}
                  onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                  className="w-full bg-transparent text-white placeholder:text-slate-700 focus:outline-none font-semibold text-lg py-5 pr-4"
                  style={{ letterSpacing: "-0.02em" }}
                />
              </FormRow>

            </div>

            <div className="pt-8">
              <Button
                type="submit"
                disabled={createMutation.isPending || !form.name.trim()}
                className="bg-white text-black hover:bg-slate-100 font-black uppercase tracking-tight rounded-full px-8 py-6 text-base disabled:opacity-30 disabled:cursor-not-allowed"
                style={{ letterSpacing: "-0.02em" }}
              >
                {createMutation.isPending ? "Creating…" : (
                  <><span>Create Company</span><ArrowRight className="w-4 h-4 ml-2" /></>
                )}
              </Button>
            </div>
          </form>
        </section>

      </div>
    </div>
  );
}

// ── FormRow ────────────────────────────────────────────────────────────────

function FormRow({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[180px_1fr] items-start gap-6 group">
      <span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600 group-focus-within:text-indigo-400 transition-colors py-5 shrink-0 select-none">
        {label}
        {required && <span className="text-indigo-500 ml-1">*</span>}
      </span>
      {children}
    </div>
  );
}

// ── StateRow — custom inline dropdown ──────────────────────────────────────

function StateRow({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div className="grid grid-cols-[180px_1fr] items-start gap-6 group border-t border-white/6 first:border-t-0" ref={ref}>
      <span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-600 group-focus-within:text-indigo-400 transition-colors py-5 shrink-0 select-none">
        State <span className="text-indigo-500">*</span>
      </span>

      <div className="relative">
        {/* Trigger */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="w-full flex items-center justify-between py-5 pr-1 text-left focus:outline-none"
        >
          <span className="text-white font-semibold text-lg" style={{ letterSpacing: "-0.02em" }}>
            {value}
          </span>
          <ChevronDown
            className={`w-4 h-4 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          />
        </button>

        {/* Inline list — renders in normal flow, pushes rows below down */}
        {open && (
          <div className="border border-white/10 rounded-2xl overflow-hidden mb-2 bg-[#1a1720]">
            <div className="overflow-y-auto max-h-56 overscroll-contain">
              {INDIAN_STATES.map((s) => {
                const isSelected = s === value;
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => { onChange(s); setOpen(false); }}
                    className={`w-full flex items-center justify-between px-5 py-3 text-left text-sm font-semibold transition-colors ${
                      isSelected
                        ? "bg-indigo-500/20 text-indigo-300"
                        : "text-slate-300 hover:bg-indigo-500/10 hover:text-indigo-200"
                    }`}
                    style={{ letterSpacing: "-0.01em" }}
                  >
                    {s}
                    {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
