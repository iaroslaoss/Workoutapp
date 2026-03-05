import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";
import { Client, PlanTemplate } from "../lib/types";

type AssignmentSummary = {
  assignment: {
    id: string;
    client_id: string;
    plan_template_id: string;
    start_date: string;
    active: boolean;
  } | null;
  plan: PlanTemplate | null;
};

export function ClientDetailsPage() {
  const { id } = useParams();
  const api = useApi();
  const queryClient = useQueryClient();
  const [planTemplateId, setPlanTemplateId] = useState("");
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10));

  const clientQuery = useQuery({ queryKey: ["client", id], queryFn: () => api.get<Client>(`/clients/${id}`), enabled: Boolean(id) });
  const plansQuery = useQuery({ queryKey: ["plans"], queryFn: () => api.get<PlanTemplate[]>("/plans") });
  const assignmentQuery = useQuery({
    queryKey: ["assignment", id],
    queryFn: () => api.get<AssignmentSummary>(`/clients/${id}/assignment`),
    enabled: Boolean(id),
  });

  const assignMutation = useMutation({
    mutationFn: () =>
      api.post("/assignments", {
        client_id: id,
        plan_template_id: planTemplateId,
        start_date: startDate,
        active: true,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["assignment", id] }),
  });

  return (
    <div className="space-y-4">
      <div className="card">
        <h1 className="text-2xl font-semibold">{clientQuery.data?.name}</h1>
        <p className="text-slate-600">{clientQuery.data?.email || "No email"}</p>
        <p className="mt-2 text-sm">{clientQuery.data?.notes || "No notes"}</p>
      </div>

      <div className="card space-y-2">
        <h2 className="text-lg font-medium">Assign Plan</h2>
        <select className="input" value={planTemplateId} onChange={(e) => setPlanTemplateId(e.target.value)}>
          <option value="">Choose a plan</option>
          {(plansQuery.data || []).map((plan) => (
            <option key={plan.id} value={plan.id}>{plan.name}</option>
          ))}
        </select>
        <input className="input" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <button className="btn" onClick={() => assignMutation.mutate()} disabled={!planTemplateId || assignMutation.isPending}>
          Assign
        </button>
      </div>

      <div className="card">
        <h2 className="text-lg font-medium">Assigned Summary</h2>
        {assignmentQuery.data?.assignment ? (
          <>
            <p>Plan: {assignmentQuery.data.plan?.name}</p>
            <p>Start Date: {assignmentQuery.data.assignment.start_date}</p>
            <Link className="text-sm underline" to={`/client-view/${id}`}>
              Open read-only client view
            </Link>
          </>
        ) : (
          <p className="text-slate-500">No plan assigned yet.</p>
        )}
      </div>
    </div>
  );
}
