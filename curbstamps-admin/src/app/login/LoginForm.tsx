"use client";

import { useActionState } from "react";
import { loginAction } from "./actions";

export function LoginForm({ next }: { next: string }) {
  const [state, formAction, pending] = useActionState(loginAction, { error: null });

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <input type="hidden" name="next" value={next} />
      <label className="flex flex-col gap-1 text-[13px] font-bold text-ink/70">
        Email
        <input
          name="email"
          type="email"
          autoComplete="username"
          required
          className="h-11 rounded-xl border border-ink/15 bg-transparent px-3 text-[15px] text-ink"
        />
      </label>
      <label className="flex flex-col gap-1 text-[13px] font-bold text-ink/70">
        Password
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="h-11 rounded-xl border border-ink/15 bg-transparent px-3 text-[15px] text-ink"
        />
      </label>
      {state.error && (
        <p role="alert" className="text-[13px] font-semibold text-red-600">
          {state.error}
        </p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="mt-2 h-11 rounded-xl bg-ink text-[14px] font-bold text-paper disabled:opacity-50"
      >
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
