import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";

export type TriageClient = {
  client_id: string;
  client_name: string;
  status: "red" | "yellow" | "green";
  missed_last_two: number;
  avg_rpe_last_14d: number | null;
  last_check_in_date: string | null;
  last_workout_completed_at: string | null;
};

export type RecentActivity = {
  workout_log_id: string;
  client_id: string;
  client_name: string;
  logged_date: string;
  completed_at: string | null;
  status: string;
};

export type DashboardTriageResponse = {
  clients: TriageClient[];
  recent_activity: RecentActivity[];
};

const statusBadge: Record<TriageClient["status"], string> = {
  red: "bg-red-100 text-red-700 border-red-200",
  yellow: "bg-amber-100 text-amber-700 border-amber-200",
  green: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

export function DashboardPage() {
  const api = useApi();

  const triageQuery = useQuery({
    queryKey: ["dashboard-triage"],
    queryFn: () => api.get<DashboardTriageResponse>("/dashboard/triage"),
  });

  const counts = useMemo(() => {
    const rows = triageQuery.data?.clients || [];
    return {
      red: rows.filter((c) => c.status === "red").length,
      yellow: rows.filter((c) => c.status === "yellow").length,
      green: rows.filter((c) => c.status === "green").length,
    };
  }, [triageQuery.data?.clients]);

  if (triageQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading dashboard...</p>;
  }

  if (triageQuery.error) {
    return <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{(triageQuery.error as Error).message}</p>;
  }

  const data = triageQuery.data;
  if (!data) {
    return <p className="text-sm text-slate-600">No dashboard data available.</p>;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
      <section className="card">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="brand-font text-2xl font-semibold">Trainer Triage Dashboard</h1>
            <p className="text-sm text-slate-500">Color-coded client attention matrix</p>
          </div>
          <div className="flex gap-2 text-xs">
            <span className="rounded-full border border-red-200 bg-red-100 px-2 py-1 text-red-700">Red: {counts.red}</span>
            <span className="rounded-full border border-amber-200 bg-amber-100 px-2 py-1 text-amber-700">Yellow: {counts.yellow}</span>
            <span className="rounded-full border border-emerald-200 bg-emerald-100 px-2 py-1 text-emerald-700">Green: {counts.green}</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th className="px-3 py-2 text-left">Client</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Missed (Last 2)</th>
                <th className="px-3 py-2 text-left">Avg RPE (14d)</th>
                <th className="px-3 py-2 text-left">Last Check-In</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.clients.map((client) => (
                <tr key={client.client_id}>
                  <td className="px-3 py-2 font-medium">{client.client_name}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${statusBadge[client.status]}`}>
                      {client.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 py-2">{client.missed_last_two}</td>
                  <td className="px-3 py-2">{client.avg_rpe_last_14d != null ? client.avg_rpe_last_14d.toFixed(1) : "-"}</td>
                  <td className="px-3 py-2">{client.last_check_in_date || "No check-in"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <aside className="card">
        <h2 className="brand-font text-lg font-semibold">Recent Activity Feed</h2>
        <p className="mb-3 text-sm text-slate-500">Latest completed workout logs</p>
        <div className="space-y-2">
          {data.recent_activity.length === 0 && (
            <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">No completed logs yet.</p>
          )}
          {data.recent_activity.map((entry) => (
            <div key={entry.workout_log_id} className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-sm font-medium">{entry.client_name}</p>
              <p className="text-xs text-slate-500">Completed: {entry.completed_at ? new Date(entry.completed_at).toLocaleString() : entry.logged_date}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
