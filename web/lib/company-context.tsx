"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import type { Company } from "./types";

interface CompanyContextValue {
  company: Company | null;
  setCompany: (c: Company | null) => void;
}

const CompanyContext = createContext<CompanyContextValue>({
  company: null,
  setCompany: () => {},
});

const STORAGE_KEY = "micropayroll_company";

export function CompanyProvider({ children }: { children: ReactNode }) {
  const [company, setCompanyState] = useState<Company | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setCompanyState(JSON.parse(stored));
    } catch {}
  }, []);

  const setCompany = (c: Company | null) => {
    setCompanyState(c);
    if (c) localStorage.setItem(STORAGE_KEY, JSON.stringify(c));
    else localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <CompanyContext.Provider value={{ company, setCompany }}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  return useContext(CompanyContext);
}
