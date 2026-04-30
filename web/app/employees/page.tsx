"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { fmtInr } from "@/lib/utils";
import type { Employee, EmployeeCreate, EmployeeUpdate } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { Plus, MoreHorizontal, Pencil, UserX, Users } from "lucide-react";
import Link from "next/link";

const EMPTY_FORM: EmployeeCreate = {
  name: "", role: "", base_salary: 0,
  phone_number: "", bank_account: "", bank_ifsc: "", pf_account: "",
};

export default function EmployeesPage() {
  const { company } = useCompany();
  const qc = useQueryClient();

  const { data: employees = [], isLoading } = useQuery({
    queryKey: ["employees", company?.id],
    queryFn: () => api.employees.list(company!.id),
    enabled: !!company,
  });

  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Employee | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<Employee | null>(null);
  const [form, setForm] = useState<EmployeeCreate>(EMPTY_FORM);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["employees", company?.id] });

  const addMutation = useMutation({
    mutationFn: (data: EmployeeCreate) => api.employees.create(company!.id, data),
    onSuccess: () => { invalidate(); setAddOpen(false); setForm(EMPTY_FORM); toast.success("Employee added."); },
    onError: () => toast.error("Failed to add employee."),
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: EmployeeUpdate }) => api.employees.update(id, data),
    onSuccess: () => { invalidate(); setEditTarget(null); toast.success("Employee updated."); },
    onError: () => toast.error("Failed to update employee."),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => api.employees.deactivate(id),
    onSuccess: () => { invalidate(); setDeactivateTarget(null); toast.success("Employee deactivated."); },
    onError: () => toast.error("Failed to deactivate employee."),
  });

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
            Employees
          </h1>
          <p className="text-slate-500 text-sm mt-2">{employees.length} active</p>
        </div>
        <Button
          className="bg-white text-black hover:bg-slate-100 font-semibold rounded-full px-6 shrink-0"
          onClick={() => { setForm(EMPTY_FORM); setAddOpen(true); }}
        >
          <Plus className="w-4 h-4 mr-2" /> Add employee
        </Button>
      </div>

      {isLoading ? (
        <div className="text-slate-600 text-sm">Loading…</div>
      ) : employees.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center border border-white/8 rounded-2xl">
          <Users className="w-8 h-8 text-slate-700 mb-4" />
          <p className="text-slate-400 font-semibold uppercase tracking-widest text-xs">No employees yet</p>
          <p className="text-slate-600 text-sm mt-1">Add your first employee to get started.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-white/8 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-white/8 hover:bg-transparent">
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Name</TableHead>
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Role</TableHead>
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Base Salary</TableHead>
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Phone</TableHead>
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">Bank A/C</TableHead>
                <TableHead className="text-[11px] font-bold uppercase tracking-widest text-slate-500 bg-white/3">IFSC</TableHead>
                <TableHead className="w-10 bg-white/3"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {employees.map((emp) => (
                <TableRow key={emp.id} className="border-white/8 hover:bg-white/3 transition-colors">
                  <TableCell className="font-semibold text-white">{emp.name}</TableCell>
                  <TableCell>
                    {emp.role ? (
                      <span className="text-[11px] font-bold uppercase tracking-widest border border-indigo-500/30 text-indigo-400 px-2 py-0.5 rounded-full">
                        {emp.role}
                      </span>
                    ) : <span className="text-slate-600 text-xs">—</span>}
                  </TableCell>
                  <TableCell className="font-bold text-slate-200 tabular-nums">{fmtInr(emp.base_salary)}</TableCell>
                  <TableCell className="text-slate-500 text-sm">{emp.phone_number || "—"}</TableCell>
                  <TableCell className="text-slate-500 text-xs font-mono">{emp.bank_account || "—"}</TableCell>
                  <TableCell className="text-slate-500 text-xs font-mono">{emp.bank_ifsc || "—"}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        className="inline-flex items-center justify-center h-8 w-8 rounded-md text-slate-500 hover:text-white hover:bg-white/8 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 aria-expanded:text-white aria-expanded:bg-white/8"
                        aria-label="Row actions"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-[#1a1720] border-white/10 text-slate-200">
                        <DropdownMenuItem className="hover:bg-white/8 focus:bg-white/8" onClick={() => setEditTarget(emp)}>
                          <Pencil className="w-3.5 h-3.5 mr-2" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-red-400 focus:text-red-400 hover:bg-white/8 focus:bg-white/8"
                          onClick={() => setDeactivateTarget(emp)}
                        >
                          <UserX className="w-3.5 h-3.5 mr-2" /> Deactivate
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Add Employee Dialog */}
      <EmployeeDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        title="Add Employee"
        form={form}
        setForm={setForm}
        onSubmit={() => addMutation.mutate(form)}
        isPending={addMutation.isPending}
      />

      {/* Edit Employee Dialog */}
      {editTarget && (
        <EmployeeDialog
          open={!!editTarget}
          onOpenChange={(o) => !o && setEditTarget(null)}
          title="Edit Employee"
          form={{
            name: editTarget.name,
            role: editTarget.role ?? "",
            base_salary: editTarget.base_salary,
            phone_number: editTarget.phone_number ?? "",
            bank_account: editTarget.bank_account ?? "",
            bank_ifsc: editTarget.bank_ifsc ?? "",
            pf_account: editTarget.pf_account ?? "",
          }}
          setForm={(f) => setEditTarget({ ...editTarget, ...f, base_salary: f.base_salary ?? editTarget.base_salary })}
          onSubmit={() =>
            editMutation.mutate({
              id: editTarget.id,
              data: {
                name: editTarget.name,
                role: editTarget.role ?? undefined,
                base_salary: editTarget.base_salary,
                phone_number: editTarget.phone_number ?? undefined,
                bank_account: editTarget.bank_account ?? undefined,
                bank_ifsc: editTarget.bank_ifsc ?? undefined,
                pf_account: editTarget.pf_account ?? undefined,
              },
            })
          }
          isPending={editMutation.isPending}
        />
      )}

      {/* Deactivate Confirm */}
      <AlertDialog open={!!deactivateTarget} onOpenChange={(o) => !o && setDeactivateTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Deactivate {deactivateTarget?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This employee will be hidden from future payroll runs. Their historical data will be preserved.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => deactivateTarget && deactivateMutation.mutate(deactivateTarget.id)}
            >
              Deactivate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function EmployeeDialog({
  open, onOpenChange, title, form, setForm, onSubmit, isPending,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  title: string;
  form: EmployeeCreate;
  setForm: (f: EmployeeCreate) => void;
  onSubmit: () => void;
  isPending: boolean;
}) {
  const f = (field: keyof EmployeeCreate, value: string | number) =>
    setForm({ ...form, [field]: value });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#0e0b14]">

      {/* ── Top bar ── */}
      <div className="flex items-center justify-between px-8 py-5 border-b border-white/8 shrink-0">
        <div>
          <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-indigo-400 mb-0.5">
            {title === "Add Employee" ? "New Member" : "Edit Member"}
          </p>
          <h2 className="text-xl font-black uppercase tracking-[-1px] text-white leading-none">
            {title}
          </h2>
        </div>
        <button
          onClick={() => onOpenChange(false)}
          className="text-slate-500 hover:text-white transition-colors p-2 rounded-full hover:bg-white/8"
          aria-label="Close"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* ── Centered form panel ── */}
      <div className="flex-1 min-h-0 flex items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-2xl max-h-full flex flex-col rounded-3xl border border-white/10 bg-white/[0.025] backdrop-blur-xl overflow-hidden">

          <div className="flex-1 overflow-y-auto px-8 py-8">
            <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-slate-500 mb-1">
              Member Details
            </p>
            <h3 className="font-heading text-2xl font-black uppercase tracking-[-1px] text-white leading-none mb-7">
              Identity & Pay
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-5">
              <div className="sm:col-span-2 space-y-1.5">
                <FieldLabel required>Full Name</FieldLabel>
                <DarkInput placeholder="Ramesh Yadav" value={form.name} onChange={(e) => f("name", e.target.value)} />
              </div>

              <div className="space-y-1.5">
                <FieldLabel>Role</FieldLabel>
                <DarkInput placeholder="Senior Tailor" value={form.role ?? ""} onChange={(e) => f("role", e.target.value)} />
              </div>

              <div className="space-y-1.5">
                <FieldLabel required>Base Salary (₹)</FieldLabel>
                <DarkInput
                  type="number" placeholder="18000"
                  value={form.base_salary || ""}
                  onChange={(e) => f("base_salary", parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="sm:col-span-2 space-y-1.5">
                <FieldLabel>Phone</FieldLabel>
                <DarkInput placeholder="+91 98765 43210" value={form.phone_number ?? ""} onChange={(e) => f("phone_number", e.target.value)} />
              </div>

              <div className="space-y-1.5">
                <FieldLabel>Bank Account</FieldLabel>
                <DarkInput placeholder="123456789012" value={form.bank_account ?? ""} onChange={(e) => f("bank_account", e.target.value)} />
              </div>

              <div className="space-y-1.5">
                <FieldLabel>IFSC</FieldLabel>
                <DarkInput
                  placeholder="SBIN0001234"
                  value={form.bank_ifsc ?? ""}
                  onChange={(e) => f("bank_ifsc", e.target.value.toUpperCase())}
                  maxLength={11}
                />
              </div>
            </div>
          </div>

          <div className="shrink-0 px-8 py-5 border-t border-white/8 bg-white/[0.02] flex justify-end gap-3">
            <Button
              variant="ghost"
              className="rounded-full text-slate-400 hover:text-white hover:bg-white/8 font-semibold"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              className="bg-white text-black hover:bg-slate-100 font-bold rounded-full px-8"
              onClick={onSubmit}
              disabled={isPending || !form.name.trim() || !form.base_salary}
            >
              {isPending ? "Saving…" : "Save Employee"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function FieldLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <label className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500 flex items-center gap-1">
      {children}
      {required && <span className="text-indigo-400">*</span>}
    </label>
  );
}

function DarkInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={[
        "w-full h-10 rounded-xl bg-white/5 border border-white/10 px-3.5 text-sm text-white",
        "placeholder:text-slate-600 outline-none transition-colors",
        "focus:border-indigo-500/60 focus:bg-white/8 focus:ring-2 focus:ring-indigo-500/20",
        "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none",
        props.className ?? "",
      ].join(" ")}
    />
  );
}
