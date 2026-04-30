"use client";

import { StaggeredMenu } from "./StaggeredMenu";
import { useCompany } from "@/lib/company-context";

const NAV_ITEMS = [
  { label: "Overview", ariaLabel: "Go to overview dashboard", link: "/" },
  { label: "Employees", ariaLabel: "Manage employees", link: "/employees" },
  { label: "Attendance", ariaLabel: "View attendance records", link: "/attendance" },
  { label: "Payroll", ariaLabel: "Run and review payroll", link: "/payroll" },
  { label: "Settings", ariaLabel: "Company settings", link: "/settings" },
];

export function AppNav() {
  const { company } = useCompany();

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      <StaggeredMenu
        position="right"
        items={NAV_ITEMS}
        socialItems={[
          { label: "GitHub", link: "https://github.com" },
        ]}
        displaySocials={!!company}
        displayItemNumbering={true}
        menuButtonColor="#e2e8f0"
        openMenuButtonColor="#e2e8f0"
        changeMenuColorOnOpen={false}
        colors={["#312e81", "#4f46e5"]}
        accentColor="#6366f1"
        closeOnClickAway={true}
      />
    </div>
  );
}
