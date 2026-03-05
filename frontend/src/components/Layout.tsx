import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../lib/auth";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/plans", label: "Plans" },
  { to: "/clients", label: "Clients" },
  { to: "/exercises", label: "Exercise Bank" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { setToken } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="brand-font text-xl font-semibold text-slate-900">
              Lift & Move
            </Link>
            <span className="hidden rounded-full bg-teal-100 px-2.5 py-1 text-xs font-semibold text-teal-700 md:inline-block">
              Trainer Studio
            </span>
          </div>

          <nav className="flex items-center gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => `app-nav-link ${isActive ? "active" : ""}`}
              >
                {link.label}
              </NavLink>
            ))}
            <button className="btn-secondary ml-1" onClick={() => setToken(null)}>
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-4 md:p-6">
        <div className="reveal">{children}</div>
      </main>
    </div>
  );
}
