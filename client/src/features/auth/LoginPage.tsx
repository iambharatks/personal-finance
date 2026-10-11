import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { AUTH_KEY } from "../../App";
import { api } from "../../api/client";
import type { AuthStatus } from "../../api/types";

export function LoginPage() {
  const queryClient = useQueryClient();
  const [password, setPassword] = useState("");
  const login = useMutation({
    mutationFn: () => api<AuthStatus>("/auth/login", { method: "POST", body: { password } }),
    onSuccess: (status) => queryClient.setQueryData(AUTH_KEY, status),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (password) login.mutate();
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-xl border border-line bg-surface p-6 shadow-sm"
      >
        <h1 className="text-lg font-semibold">Finance Command Center</h1>
        <p className="mt-1 text-sm text-muted">Enter your password to continue.</p>

        <label htmlFor="password" className="mt-5 block text-sm font-medium text-ink-2">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoFocus
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="field mt-1 w-full"
        />
        {login.isError && (
          <p role="alert" className="mt-2 text-sm text-rose-600 dark:text-rose-400">
            {login.error.message}
          </p>
        )}
        <button
          type="submit"
          disabled={!password || login.isPending}
          className="mt-5 h-9 w-full rounded-md bg-sky-600 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
        >
          {login.isPending ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
