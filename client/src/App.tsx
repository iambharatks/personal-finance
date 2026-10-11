import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { api, SESSION_EXPIRED } from "./api/client";
import type { AuthStatus } from "./api/types";
import { AppShell } from "./components/layout/AppShell";
import { LoginPage } from "./features/auth/LoginPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { TransactionsPage } from "./features/transactions/TransactionsPage";

export const AUTH_KEY = ["/auth/me"];

export default function App() {
  const queryClient = useQueryClient();
  const auth = useQuery({ queryKey: AUTH_KEY, queryFn: () => api<AuthStatus>("/auth/me") });

  useEffect(() => {
    const onExpired = () => queryClient.invalidateQueries({ queryKey: AUTH_KEY });
    window.addEventListener(SESSION_EXPIRED, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED, onExpired);
  }, [queryClient]);

  if (auth.isPending) return <div className="p-8 text-sm text-muted">Loading…</div>;
  if (auth.isError) {
    return (
      <div className="p-8 text-sm">
        <p className="font-medium">Cannot reach the server.</p>
        <p className="mt-1 text-muted">{auth.error.message}</p>
        <button className="btn mt-4" onClick={() => auth.refetch()}>
          Try again
        </button>
      </div>
    );
  }
  if (!auth.data.authenticated) return <LoginPage />;

  return (
    <Routes>
      <Route element={<AppShell canSignOut={auth.data.auth_required} />}>
        <Route index element={<DashboardPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
