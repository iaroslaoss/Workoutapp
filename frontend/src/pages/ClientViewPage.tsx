import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";

type ClientPlanView = {
  client_id: string;
  plan_template_id: string;
  plan_name: string;
  start_date: string;
  active: boolean;
  days: {
    id: string;
    week_number: number;
    day_name: string;
    exercises: {
      id: string;
      exercise_name: string;
      sets: number;
      reps: string;
      rpe?: number | null;
      weight?: number | null;
      rest_seconds?: number | null;
      tempo: string;
      notes?: string | null;
    }[];
  }[];
};

export function ClientViewPage() {
  const { clientId } = useParams();
  const api = useApi();

  const query = useQuery({
    queryKey: ["client-view", clientId],
    queryFn: () => api.get<ClientPlanView>(`/client-view/${clientId}`),
    enabled: Boolean(clientId),
  });

  const grouped = useMemo(() => {
    const map: Record<number, ClientPlanView["days"]> = {};
    for (const day of query.data?.days || []) {
      map[day.week_number] = map[day.week_number] || [];
      map[day.week_number].push(day);
    }
    return Object.entries(map)
      .map(([week, days]) => ({ week: Number(week), days: days.sort((a, b) => a.day_name.localeCompare(b.day_name)) }))
      .sort((a, b) => a.week - b.week);
  }, [query.data]);

  if (query.isLoading) return <p>Loading...</p>;
  if (query.error) return <p className="text-red-600">{(query.error as Error).message}</p>;

  return (
    <div className="space-y-4">
      <div className="card">
        <h1 className="text-2xl font-semibold">{query.data?.plan_name}</h1>
        <p className="text-slate-600">Start date: {query.data?.start_date}</p>
      </div>
      {grouped.map((week) => (
        <div key={week.week} className="card">
          <h2 className="text-lg font-medium">Week {week.week}</h2>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {week.days.map((day) => (
              <div key={day.id} className="rounded-lg border border-slate-200 p-3">
                <p className="font-medium">{day.day_name}</p>
                <ul className="mt-2 space-y-1 text-sm">
                  {day.exercises.map((ex) => (
                    <li key={ex.id}>
                      {ex.exercise_name} - {ex.sets} x {ex.reps} ({ex.tempo})
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
