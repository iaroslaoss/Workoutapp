import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const { setToken, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
        headers: { "Content-Type": "application/json" },
      });
      setToken(res.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="grid min-h-screen bg-slate-100 md:grid-cols-2">
      <section className="hidden bg-gradient-to-b from-teal-700 to-teal-800 p-10 text-white md:block">
        <p className="brand-font text-2xl font-semibold">Lift & Move</p>
        <h1 className="brand-font mt-10 max-w-md text-4xl font-bold leading-tight">
          Welcome back, coach.
        </h1>
        <p className="mt-4 max-w-md text-teal-50">
          Keep your client programming tight, structured, and easy to communicate.
        </p>
        <div className="mt-10 space-y-3 text-sm">
          <div className="rounded-xl border border-teal-500/50 bg-white/10 px-4 py-3">Plan templates by week and day</div>
          <div className="rounded-xl border border-teal-500/50 bg-white/10 px-4 py-3">Fast assignment for active clients</div>
          <div className="rounded-xl border border-teal-500/50 bg-white/10 px-4 py-3">Clear read-only client plan view</div>
        </div>
      </section>

      <section className="flex items-center justify-center p-4 md:p-10">
        <form onSubmit={onSubmit} className="card w-full max-w-md space-y-3">
          <h2 className="brand-font text-3xl font-semibold">Sign in</h2>
          <p className="text-sm text-slate-500">Access your coaching workspace.</p>
          <input className="input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            className="input"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <button className="btn w-full" type="submit">
            Enter Dashboard
          </button>
          <p className="text-sm text-slate-600">
            Need an account? <Link to="/register" className="font-semibold underline">Register</Link>
          </p>
          <p className="text-sm text-slate-600">
            <Link to="/" className="underline">Back to home</Link>
          </p>
        </form>
      </section>
    </div>
  );
}
