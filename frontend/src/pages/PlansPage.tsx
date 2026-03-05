import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";
import { PlanTemplate, StarterPlanImportResponse, StarterPlanSuggestion } from "../lib/types";

export function PlansPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [weeksCount, setWeeksCount] = useState(4);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["plans"],
    queryFn: () => api.get<PlanTemplate[]>("/plans"),
  });

  const starterQuery = useQuery({
    queryKey: ["starter-plans"],
    queryFn: () => api.get<StarterPlanSuggestion[]>("/plans/starter-suggestions"),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post<PlanTemplate>("/plans", { name, description, weeks_count: weeksCount }),
    onSuccess: () => {
      setName("");
      setDescription("");
      setWeeksCount(4);
      setError(null);
      setNotice("Plan created.");
      queryClient.invalidateQueries({ queryKey: ["plans"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const duplicateMutation = useMutation({
    mutationFn: (plan: PlanTemplate) => api.post<PlanTemplate>(`/plans/${plan.id}/duplicate`, { name: `${plan.name} (Copy)` }),
    onSuccess: () => {
      setNotice("Plan duplicated.");
      queryClient.invalidateQueries({ queryKey: ["plans"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const importStarterMutation = useMutation({
    mutationFn: (slug: string) => api.post<StarterPlanImportResponse>(`/plans/starter/${slug}/import`, {}),
    onSuccess: (res) => {
      const missing = res.missing_exercises.length;
      setNotice(
        missing > 0
          ? `Imported ${res.plan.name}. Added ${res.exercises_created} exercises (${missing} missing mappings).`
          : `Imported ${res.plan.name}. Added ${res.exercises_created} exercises.`
      );
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["plans"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const onCreate = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !description.trim()) {
      setError("Plan name and description are required.");
      return;
    }
    setError(null);
    setNotice(null);
    createMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Plan Templates</h1>
          <p className="text-sm text-slate-500">{(query.data || []).length} templates</p>
        </div>

        {notice && <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>}
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-3">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="font-semibold text-teal-900">Beginner Starter Suggestions</h2>
            <span className="text-xs text-teal-700">One-click import</span>
          </div>

          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {(starterQuery.data || []).map((starter) => (
              <div key={starter.slug} className="rounded-lg border border-teal-200 bg-white p-3">
                <p className="font-medium">{starter.name}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {starter.goal.replace("_", " ")} • {starter.weeks_count} weeks • {starter.sessions_per_week} sessions/week
                </p>
                <p className="mt-1 text-sm text-slate-600">{starter.description}</p>
                <button
                  className="btn-accent mt-3"
                  onClick={() => importStarterMutation.mutate(starter.slug)}
                  disabled={importStarterMutation.isPending}
                >
                  Import Starter
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 grid gap-2 md:grid-cols-3">
          {(query.data || []).map((plan) => (
            <div key={plan.id} className="rounded-lg border border-slate-200 p-3">
              <p className="font-medium">{plan.name}</p>
              <p className="text-sm text-slate-500">{plan.weeks_count} weeks</p>
              <p className="mt-1 line-clamp-2 text-sm text-slate-600">{plan.description}</p>

              <div className="mt-3 flex gap-2">
                <Link className="btn" to={`/plans/${plan.id}`}>
                  Open Builder
                </Link>
                <button className="btn-secondary" onClick={() => duplicateMutation.mutate(plan)} disabled={duplicateMutation.isPending}>
                  Duplicate
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <form className="card space-y-2" onSubmit={onCreate}>
        <h2 className="text-lg font-medium">Create New Plan</h2>
        <input className="input" placeholder="Plan name" value={name} onChange={(e) => setName(e.target.value)} />
        <textarea className="input" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <input
          className="input"
          type="number"
          min={1}
          max={52}
          value={weeksCount}
          onChange={(e) => setWeeksCount(Number(e.target.value))}
        />
        <button className="btn" disabled={createMutation.isPending}>
          Create Template
        </button>
      </form>
    </div>
  );
}
