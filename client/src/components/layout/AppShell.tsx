import { Outlet } from "react-router-dom";

import { FilterBar } from "./FilterBar";
import { Sidebar } from "./Sidebar";

export function AppShell({ canSignOut }: { canSignOut: boolean }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar canSignOut={canSignOut} />
      <div className="min-w-0 flex-1">
        <FilterBar />
        <main className="mx-auto max-w-[1400px] p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
