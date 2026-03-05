import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../lib/auth";

export function HomePage() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen px-4 pb-16 pt-4 md:px-8">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between rounded-2xl border border-slate-200/80 bg-white/80 px-4 py-3 backdrop-blur">
        <p className="brand-font text-xl font-semibold">Lift & Move</p>
        <div className="flex items-center gap-2">
          <Link to="/login" className="btn-secondary">Sign in</Link>
          <Link to="/register" className="btn-accent">Start Free</Link>
        </div>
      </header>

      <main className="mx-auto mt-6 grid w-full max-w-6xl gap-6 md:grid-cols-[1.1fr_0.9fr]">
        <section className="reveal rounded-3xl border border-slate-200 bg-white/85 p-6 md:p-8">
          <p className="mb-3 inline-block rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-orange-700">
            Built for coaches
          </p>
          <h1 className="brand-font text-4xl font-bold leading-tight text-slate-900 md:text-6xl">
            Program design that feels like a real coaching workspace.
          </h1>
          <p className="mt-4 max-w-xl text-base text-slate-600 md:text-lg">
            Build repeatable training templates, assign them to clients, and keep your whole system clean without bouncing between spreadsheets, notes, and chat messages.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link to="/register" className="btn-accent">Create Trainer Account</Link>
            <Link to="/login" className="btn-secondary">I already have access</Link>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-teal-50 p-3">
              <p className="brand-font text-2xl font-bold text-teal-700">12h</p>
              <p className="text-xs text-slate-600">Saved weekly on plan admin</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-orange-50 p-3">
              <p className="brand-font text-2xl font-bold text-orange-700">3x</p>
              <p className="text-xs text-slate-600">Faster template setup</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-100 p-3">
              <p className="brand-font text-2xl font-bold text-slate-700">1 hub</p>
              <p className="text-xs text-slate-600">Plans, clients, exercise bank</p>
            </div>
          </div>
        </section>

        <section className="reveal space-y-4" style={{ animationDelay: "80ms" }}>
          <div className="card">
            <div className="mb-3 flex items-center justify-between">
              <p className="brand-font text-lg font-semibold">Coach Console</p>
              <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">Live</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between rounded-xl bg-slate-100 px-3 py-2">
                <span>Template Library</span>
                <strong>18 plans</strong>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-slate-100 px-3 py-2">
                <span>Assigned this week</span>
                <strong>9 clients</strong>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-slate-100 px-3 py-2">
                <span>Exercise bank</span>
                <strong>64 movements</strong>
              </div>
            </div>
          </div>

          <div className="card">
            <p className="brand-font mb-2 text-lg font-semibold">How it works</p>
            <ol className="space-y-2 text-sm text-slate-700">
              <li>1. Create or import exercises into your bank.</li>
              <li>2. Build week/day plan templates with prescription details.</li>
              <li>3. Assign templates to clients and share read-only view.</li>
            </ol>
          </div>
        </section>
      </main>
    </div>
  );
}
