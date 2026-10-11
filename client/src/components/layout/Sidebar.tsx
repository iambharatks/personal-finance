import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";

import { AUTH_KEY } from "../../App";
import { api } from "../../api/client";
import type { AuthStatus } from "../../api/types";
import { useFilters } from "../../lib/useFilters";
import { ThemeToggle } from "./ThemeToggle";

const PAGES = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/transactions", label: "Transactions", end: false },
];

export function Sidebar({ canSignOut }: { canSignOut: boolean }) {
  const { globalSearch } = useFilters();
  const queryClient = useQueryClient();
  const signOut = useMutation({
    mutationFn: () => api<AuthStatus>("/auth/logout", { method: "POST" }),
    onSuccess: (status) => {
      // Back to the login page, and nothing financial stays cached in the tab.
      queryClient.setQueryData(AUTH_KEY, status);
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== AUTH_KEY[0] });
    },
  });

  return (
    <aside className="sticky top-0 flex h-screen w-52 shrink-0 flex-col bg-sidebar text-slate-300 dark:border-r dark:border-line">
      <div className="px-4 py-5">
        <div className="text-sm font-semibold text-white">Finance</div>
        <div className="text-xs text-slate-400">Command Center</div>
      </div>
      <nav className="flex-1 space-y-1 px-2">
        {PAGES.map((page) => (
          <NavLink
            key={page.to}
            to={{ pathname: page.to, search: globalSearch }}
            end={page.end}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm ${
                isActive ? "bg-white/10 font-medium text-white" : "hover:bg-white/5"
              }`
            }
          >
            {page.label}
          </NavLink>
        ))}
      </nav>
      <div className="space-y-1 border-t border-white/10 p-2">
        <ThemeToggle />
        {canSignOut && (
          <button
            onClick={() => signOut.mutate()}
            className="block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-white/5"
          >
            Sign out
          </button>
        )}
      </div>
    </aside>
  );
}
