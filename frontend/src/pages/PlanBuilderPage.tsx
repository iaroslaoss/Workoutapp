import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { useApi } from "../hooks/useApi";
import {
  Exercise,
  ExerciseCatalogResponse,
  ExerciseFilterMetaResponse,
  ExerciseSuggestion,
  ExerciseSuggestResponse,
  PlanDay,
  PlanExercise,
  PlanTemplate,
} from "../lib/types";

const defaultDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const daySortIndex: Record<string, number> = {
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
  Sun: 7,
};

const PICKER_PAGE_SIZE = 20;
const goalOptions = [
  { value: "general_fitness", label: "General Fitness" },
  { value: "strength", label: "Strength" },
  { value: "hypertrophy", label: "Hypertrophy" },
  { value: "fat_loss", label: "Fat Loss" },
  { value: "conditioning", label: "Conditioning" },
] as const;
const focusOptions = [
  { value: "full_body", label: "Full Body" },
  { value: "push", label: "Push" },
  { value: "pull", label: "Pull" },
  { value: "legs", label: "Legs" },
  { value: "core", label: "Core" },
  { value: "conditioning", label: "Conditioning" },
] as const;

const equipmentProfiles = [
  { value: "all", label: "All Equipment" },
  { value: "bodyweight_only", label: "Bodyweight Only" },
  { value: "dumbbells_only", label: "Dumbbells Only" },
  { value: "hotel_gym", label: "Hotel Gym" },
  { value: "garage_gym", label: "Garage Gym" },
  { value: "custom", label: "Custom Selection" },
] as const;

type PlanExerciseDraft = {
  sets: string;
  reps: string;
  rpe: string;
  weight: string;
  rest_seconds: string;
  tempo: string;
  notes: string;
};

type AddExercisePayload = {
  exercise_id: string;
  sets: number;
  reps: string;
  rpe: number | null;
  weight: number | null;
  rest_seconds: number | null;
  tempo: string | null;
  notes: string | null;
};

type GoalValue = (typeof goalOptions)[number]["value"];
type FocusValue = (typeof focusOptions)[number]["value"];
type EquipmentProfile = (typeof equipmentProfiles)[number]["value"];

function buildDraft(item: PlanExercise): PlanExerciseDraft {
  return {
    sets: String(item.sets ?? 3),
    reps: item.reps ?? "8-10",
    rpe: item.rpe == null ? "" : String(item.rpe),
    weight: item.weight == null ? "" : String(item.weight),
    rest_seconds: item.rest_seconds == null ? "" : String(item.rest_seconds),
    tempo: item.tempo ?? "",
    notes: item.notes ?? "",
  };
}

function baseAddPayload(exerciseId: string): AddExercisePayload {
  return {
    exercise_id: exerciseId,
    sets: 3,
    reps: "8-10",
    rpe: null,
    weight: null,
    rest_seconds: 90,
    tempo: null,
    notes: null,
  };
}

function profileToEquipment(profile: EquipmentProfile, custom: string[]): string[] | null {
  if (profile === "all") return null;
  if (profile === "custom") return custom.length > 0 ? custom : null;
  if (profile === "bodyweight_only") return ["Bodyweight"];
  if (profile === "dumbbells_only") return ["Dumbbells", "Bodyweight"];
  if (profile === "hotel_gym") {
    return ["Bodyweight", "Dumbbells", "Band", "Treadmill", "Bike", "Rower", "Elliptical"];
  }
  if (profile === "garage_gym") {
    return ["Barbell", "Dumbbells", "Kettlebell", "Bodyweight", "Band", "Trap Bar", "Landmine", "Sandbag"];
  }
  return null;
}

export function PlanBuilderPage() {
  const { id } = useParams();
  const api = useApi();
  const queryClient = useQueryClient();

  const [selectedDayId, setSelectedDayId] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [exerciseSearch, setExerciseSearch] = useState("");
  const [targetDayId, setTargetDayId] = useState("");
  const [drafts, setDrafts] = useState<Record<string, PlanExerciseDraft>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [pickerCategory, setPickerCategory] = useState("");
  const [pickerEquipment, setPickerEquipment] = useState("");
  const [pickerMuscleGroup, setPickerMuscleGroup] = useState("");
  const [pickerPage, setPickerPage] = useState(1);

  const [composerGoal, setComposerGoal] = useState<GoalValue>("general_fitness");
  const [composerFocus, setComposerFocus] = useState<FocusValue>("full_body");
  const [equipmentProfile, setEquipmentProfile] = useState<EquipmentProfile>("all");
  const [customEquipments, setCustomEquipments] = useState<string[]>([]);
  const [composerLimit, setComposerLimit] = useState(6);
  const [composerSuggestions, setComposerSuggestions] = useState<ExerciseSuggestion[]>([]);

  useEffect(() => {
    setPickerPage(1);
  }, [exerciseSearch, pickerCategory, pickerEquipment, pickerMuscleGroup]);

  const planQuery = useQuery({
    queryKey: ["plan", id],
    queryFn: () => api.get<PlanTemplate>(`/plans/${id}`),
    enabled: Boolean(id),
  });

  const dayQuery = useQuery({
    queryKey: ["days", id],
    queryFn: () => api.get<PlanDay[]>(`/plans/${id}/days`),
    enabled: Boolean(id),
  });

  const exerciseBankQuery = useQuery({
    queryKey: ["exercise-bank-lookup"],
    queryFn: () => api.get<Exercise[]>("/exercises"),
  });

  const exerciseMetaQuery = useQuery({
    queryKey: ["exercise-meta"],
    queryFn: () => api.get<ExerciseFilterMetaResponse>("/exercises/meta"),
  });

  const pickerQuery = useQuery({
    queryKey: ["exercise-picker", exerciseSearch, pickerCategory, pickerEquipment, pickerMuscleGroup, pickerPage],
    queryFn: () => {
      const params = new URLSearchParams();
      if (exerciseSearch.trim()) params.set("name", exerciseSearch.trim());
      if (pickerCategory) params.set("category", pickerCategory);
      if (pickerEquipment) params.set("equipment", pickerEquipment);
      if (pickerMuscleGroup) params.set("muscle_group", pickerMuscleGroup);
      params.set("page", String(pickerPage));
      params.set("page_size", String(PICKER_PAGE_SIZE));
      return api.get<ExerciseCatalogResponse>(`/exercises/catalog?${params.toString()}`);
    },
    enabled: pickerOpen,
  });

  const selectedExercisesQuery = useQuery({
    queryKey: ["day-exercises", selectedDayId],
    queryFn: () => api.get<PlanExercise[]>(`/days/${selectedDayId}/exercises`),
    enabled: Boolean(selectedDayId),
  });

  useEffect(() => {
    if (!selectedDayId && (dayQuery.data?.length || 0) > 0) {
      setSelectedDayId(dayQuery.data![0].id);
    }
  }, [dayQuery.data, selectedDayId]);

  useEffect(() => {
    const nextDrafts: Record<string, PlanExerciseDraft> = {};
    for (const item of selectedExercisesQuery.data || []) {
      nextDrafts[item.id] = buildDraft(item);
    }
    setDrafts(nextDrafts);
  }, [selectedExercisesQuery.data]);

  const createDayMutation = useMutation({
    mutationFn: (payload: { week_number: number; day_name: string }) => api.post<PlanDay>(`/plans/${id}/days`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["days", id] }),
  });

  const addExerciseMutation = useMutation({
    mutationFn: (payload: AddExercisePayload) => api.post<PlanExercise>(`/days/${selectedDayId}/exercises`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["day-exercises", selectedDayId] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const suggestionMutation = useMutation({
    mutationFn: () => {
      const availableEquipment = profileToEquipment(equipmentProfile, customEquipments);
      return api.post<ExerciseSuggestResponse>("/exercises/suggest", {
        goal: composerGoal,
        session_focus: composerFocus,
        available_equipment: availableEquipment,
        limit: composerLimit,
      });
    },
    onSuccess: (res) => {
      setComposerSuggestions(res.suggestions);
      setNotice(`Generated ${res.suggestions.length} suggestions.`);
      setError(null);
    },
    onError: (err) => setError((err as Error).message),
  });

  const updatePlanExercise = useMutation({
    mutationFn: (payload: { id: string; patch: Partial<PlanExercise> }) =>
      api.put<PlanExercise>(`/plan-exercises/${payload.id}`, payload.patch),
    onSuccess: () => {
      setNotice("Exercise updated.");
      queryClient.invalidateQueries({ queryKey: ["day-exercises", selectedDayId] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const deletePlanExercise = useMutation({
    mutationFn: (itemId: string) => api.del<void>(`/plan-exercises/${itemId}`),
    onSuccess: () => {
      setNotice("Exercise removed from day.");
      queryClient.invalidateQueries({ queryKey: ["day-exercises", selectedDayId] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const duplicateDayMutation = useMutation({
    mutationFn: () => api.post(`/days/duplicate`, { source_day_id: selectedDayId, target_day_id: targetDayId }),
    onSuccess: () => {
      setNotice("Day copied successfully.");
      if (targetDayId === selectedDayId) {
        queryClient.invalidateQueries({ queryKey: ["day-exercises", selectedDayId] });
      }
      queryClient.invalidateQueries({ queryKey: ["day-exercises", targetDayId] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const ensureGrid = async () => {
    setError(null);
    setNotice(null);
    if (!planQuery.data || !dayQuery.data) return;

    const existing = new Set(dayQuery.data.map((d) => `${d.week_number}-${d.day_name}`));
    for (let week = 1; week <= planQuery.data.weeks_count; week += 1) {
      for (const name of defaultDays) {
        const key = `${week}-${name}`;
        if (!existing.has(key)) {
          await createDayMutation.mutateAsync({ week_number: week, day_name: name });
        }
      }
    }
    setNotice("Week/day grid generated.");
  };

  const addSuggestionToDay = async (suggestion: ExerciseSuggestion) => {
    await addExerciseMutation.mutateAsync({
      exercise_id: suggestion.exercise_id,
      sets: suggestion.sets,
      reps: suggestion.reps,
      rpe: suggestion.target_rpe,
      weight: null,
      rest_seconds: suggestion.rest_seconds,
      tempo: null,
      notes: `AI suggestion for ${composerGoal.replace("_", " ")} (${composerFocus.replace("_", " ")})`,
    });
    setNotice(`Added ${suggestion.name}.`);
  };

  const addAllSuggestions = async () => {
    if (!selectedDayId || composerSuggestions.length === 0) return;
    setError(null);
    setNotice(null);
    for (const suggestion of composerSuggestions) {
      await addSuggestionToDay(suggestion);
    }
    setNotice(`Added ${composerSuggestions.length} AI suggestions to ${selectedDayLabel}.`);
  };

  const groupedDays = useMemo(() => {
    const map: Record<number, PlanDay[]> = {};
    for (const day of dayQuery.data || []) {
      map[day.week_number] = map[day.week_number] || [];
      map[day.week_number].push(day);
    }
    return Object.entries(map)
      .map(([week, days]) => ({
        week: Number(week),
        days: days.sort((a, b) => {
          const aIdx = daySortIndex[a.day_name] ?? 99;
          const bIdx = daySortIndex[b.day_name] ?? 99;
          if (aIdx !== bIdx) return aIdx - bIdx;
          return a.day_name.localeCompare(b.day_name);
        }),
      }))
      .sort((a, b) => a.week - b.week);
  }, [dayQuery.data]);

  const dayById = useMemo(() => {
    const out: Record<string, PlanDay> = {};
    for (const day of dayQuery.data || []) {
      out[day.id] = day;
    }
    return out;
  }, [dayQuery.data]);

  const exerciseNameById = useMemo(() => {
    const out: Record<string, string> = {};
    for (const ex of exerciseBankQuery.data || []) {
      out[ex.id] = ex.name;
    }
    for (const ex of pickerQuery.data?.items || []) {
      out[ex.id] = ex.name;
    }
    return out;
  }, [exerciseBankQuery.data, pickerQuery.data?.items]);

  const onDraftChange = (itemId: string, field: keyof PlanExerciseDraft, value: string) => {
    setDrafts((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [field]: value,
      },
    }));
  };

  const onSaveExercise = (item: PlanExercise) => {
    const draft = drafts[item.id] || buildDraft(item);
    setError(null);
    setNotice(null);

    updatePlanExercise.mutate({
      id: item.id,
      patch: {
        sets: Number(draft.sets || item.sets),
        reps: draft.reps,
        rpe: draft.rpe === "" ? null : Number(draft.rpe),
        weight: draft.weight === "" ? null : Number(draft.weight),
        rest_seconds: draft.rest_seconds === "" ? null : Number(draft.rest_seconds),
        tempo: draft.tempo.trim() === "" ? null : draft.tempo.trim(),
        notes: draft.notes.trim() === "" ? null : draft.notes.trim(),
      },
    });
  };

  const selectedDayLabel = selectedDayId
    ? `Week ${dayById[selectedDayId]?.week_number ?? "?"} - ${dayById[selectedDayId]?.day_name ?? "Day"}`
    : "Day";

  const pickerTotal = pickerQuery.data?.total || 0;
  const pickerTotalPages = pickerQuery.data?.total_pages || 1;
  const pickerStart = pickerTotal === 0 ? 0 : (pickerPage - 1) * PICKER_PAGE_SIZE + 1;
  const pickerEnd = pickerTotal === 0 ? 0 : Math.min(pickerPage * PICKER_PAGE_SIZE, pickerTotal);

  const allEquipmentOptions = exerciseMetaQuery.data?.equipments || [];

  return (
    <div className="grid gap-4 md:grid-cols-[300px_1fr]">
      <aside className="card h-fit space-y-3">
        <div className="space-y-2">
          <h1 className="text-lg font-semibold">{planQuery.data?.name || "Plan"}</h1>
          <p className="text-sm text-slate-500">{planQuery.data?.weeks_count ?? 0} weeks</p>
        </div>

        <button className="btn w-full" onClick={ensureGrid} disabled={createDayMutation.isPending}>
          Generate Full Week Grid
        </button>

        <div className="space-y-3">
          {groupedDays.map((week) => (
            <div key={week.week}>
              <p className="mb-1 text-xs uppercase tracking-wider text-slate-500">Week {week.week}</p>
              <div className="grid grid-cols-2 gap-1">
                {week.days.map((day) => (
                  <button
                    key={day.id}
                    className={`rounded-md px-2 py-1 text-left text-sm ${selectedDayId === day.id ? "bg-slate-900 text-white" : "bg-slate-200 hover:bg-slate-300"}`}
                    onClick={() => setSelectedDayId(day.id)}
                  >
                    {day.day_name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </aside>

      <section className="card space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl font-semibold">{selectedDayLabel}</h2>
          <button className="btn" disabled={!selectedDayId} onClick={() => setPickerOpen(true)}>
            Add Exercise
          </button>
        </div>

        {notice && <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>}
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div>
              <p className="font-semibold text-teal-900">Workout Composer AI</p>
              <p className="text-xs text-teal-700">Generate sound exercises based on goal, focus, and equipment.</p>
            </div>
            <button className="btn-accent" onClick={() => suggestionMutation.mutate()} disabled={suggestionMutation.isPending || !selectedDayId}>
              {suggestionMutation.isPending ? "Thinking..." : "Suggest Exercises"}
            </button>
          </div>

          <div className="grid gap-2 md:grid-cols-4">
            <select className="input" value={composerGoal} onChange={(e) => setComposerGoal(e.target.value as GoalValue)}>
              {goalOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <select className="input" value={composerFocus} onChange={(e) => setComposerFocus(e.target.value as FocusValue)}>
              {focusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <select className="input" value={equipmentProfile} onChange={(e) => setEquipmentProfile(e.target.value as EquipmentProfile)}>
              {equipmentProfiles.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <input
              className="input"
              type="number"
              min={3}
              max={12}
              value={composerLimit}
              onChange={(e) => setComposerLimit(Math.max(3, Math.min(12, Number(e.target.value) || 6)))}
            />
          </div>

          {equipmentProfile === "custom" && (
            <div className="mt-2 max-h-36 overflow-auto rounded-lg border border-slate-200 bg-white p-2">
              <p className="mb-1 text-xs font-medium text-slate-600">Custom equipment</p>
              <div className="grid gap-1 md:grid-cols-3">
                {allEquipmentOptions.map((item) => (
                  <label key={item} className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={customEquipments.includes(item)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setCustomEquipments((prev) => [...prev, item]);
                        } else {
                          setCustomEquipments((prev) => prev.filter((x) => x !== item));
                        }
                      }}
                    />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {composerSuggestions.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Suggested exercise stack ({composerSuggestions.length})</p>
                <button className="btn" onClick={addAllSuggestions} disabled={addExerciseMutation.isPending || !selectedDayId}>
                  Add All to Day
                </button>
              </div>
              <div className="space-y-2">
                {composerSuggestions.map((s) => (
                  <div key={s.exercise_id} className="rounded-lg border border-teal-200 bg-white p-2">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-slate-500">{s.category} - {s.muscle_group} - {s.equipment}</p>
                        <p className="text-xs text-slate-600">{s.reason}</p>
                        <p className="text-xs text-slate-600">{s.sets} sets | {s.reps} reps | RPE {s.target_rpe ?? "-"} | Rest {s.rest_seconds ?? "-"}s</p>
                      </div>
                      <button className="btn-secondary" onClick={() => addSuggestionToDay(s)} disabled={addExerciseMutation.isPending || !selectedDayId}>
                        Add
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 p-3">
          <p className="mb-2 text-sm font-medium">Copy Current Day Into Another Day</p>
          <div className="flex flex-wrap items-center gap-2">
            <select className="input max-w-xs" value={targetDayId} onChange={(e) => setTargetDayId(e.target.value)}>
              <option value="">Select target day</option>
              {(dayQuery.data || []).map((day) => (
                <option key={day.id} value={day.id}>
                  Week {day.week_number} - {day.day_name}
                </option>
              ))}
            </select>
            <button
              className="btn-secondary"
              disabled={!selectedDayId || !targetDayId || duplicateDayMutation.isPending}
              onClick={() => duplicateDayMutation.mutate()}
            >
              Copy Day Exercises
            </button>
          </div>
        </div>

        {selectedDayId ? (
          <div className="space-y-3">
            {(selectedExercisesQuery.data || []).length === 0 && (
              <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">No exercises for this day yet.</p>
            )}

            {(selectedExercisesQuery.data || []).map((item) => {
              const draft = drafts[item.id] || buildDraft(item);
              return (
                <div key={item.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="font-medium">{exerciseNameById[item.exercise_id] || "Unknown Exercise"}</p>
                    <p className="text-xs text-slate-500">{item.exercise_id}</p>
                  </div>

                  <div className="grid gap-2 md:grid-cols-3">
                    <input className="input" value={draft.sets} onChange={(e) => onDraftChange(item.id, "sets", e.target.value)} placeholder="Sets" />
                    <input className="input" value={draft.reps} onChange={(e) => onDraftChange(item.id, "reps", e.target.value)} placeholder="Reps" />
                    <input className="input" value={draft.rpe} onChange={(e) => onDraftChange(item.id, "rpe", e.target.value)} placeholder="RPE" />
                    <input className="input" value={draft.weight} onChange={(e) => onDraftChange(item.id, "weight", e.target.value)} placeholder="Weight" />
                    <input className="input" value={draft.rest_seconds} onChange={(e) => onDraftChange(item.id, "rest_seconds", e.target.value)} placeholder="Rest sec" />
                    <input className="input" value={draft.tempo} onChange={(e) => onDraftChange(item.id, "tempo", e.target.value)} placeholder="Tempo (3-1-1-0)" />
                  </div>

                  <textarea
                    className="input mt-2"
                    value={draft.notes}
                    onChange={(e) => onDraftChange(item.id, "notes", e.target.value)}
                    placeholder="Exercise notes"
                  />

                  <div className="mt-2 flex gap-2">
                    <button className="btn" onClick={() => onSaveExercise(item)} disabled={updatePlanExercise.isPending}>
                      Save
                    </button>
                    <button
                      className="btn-danger"
                      onClick={() => deletePlanExercise.mutate(item.id)}
                      disabled={deletePlanExercise.isPending}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-500">Select or create day entries from the sidebar.</p>
        )}

        {pickerOpen && (
          <div className="rounded-lg border border-slate-300 bg-slate-50 p-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="font-medium">Exercise Picker</p>
              <button className="btn-secondary" onClick={() => setPickerOpen(false)}>
                Close
              </button>
            </div>

            <div className="grid gap-2 md:grid-cols-2">
              <input
                className="input"
                placeholder="Search by name"
                value={exerciseSearch}
                onChange={(e) => setExerciseSearch(e.target.value)}
              />
              <select className="input" value={pickerCategory} onChange={(e) => setPickerCategory(e.target.value)}>
                <option value="">All categories</option>
                {(exerciseMetaQuery.data?.categories || []).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select className="input" value={pickerEquipment} onChange={(e) => setPickerEquipment(e.target.value)}>
                <option value="">All equipment</option>
                {(exerciseMetaQuery.data?.equipments || []).map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
              <select className="input" value={pickerMuscleGroup} onChange={(e) => setPickerMuscleGroup(e.target.value)}>
                <option value="">All muscle groups</option>
                {(exerciseMetaQuery.data?.muscle_groups || []).map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>

            <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
              <p>Showing {pickerStart}-{pickerEnd} of {pickerTotal}</p>
              <div className="flex items-center gap-2">
                <button className="btn-secondary" disabled={pickerPage <= 1} onClick={() => setPickerPage((p) => Math.max(1, p - 1))}>Prev</button>
                <span>Page {pickerPage} / {pickerTotalPages}</span>
                <button className="btn-secondary" disabled={pickerPage >= pickerTotalPages} onClick={() => setPickerPage((p) => Math.min(pickerTotalPages, p + 1))}>Next</button>
              </div>
            </div>

            <div className="mt-2 max-h-72 space-y-1 overflow-auto">
              {(pickerQuery.data?.items || []).map((exercise) => (
                <button
                  key={exercise.id}
                  className="w-full rounded border border-slate-200 bg-white p-2 text-left hover:border-slate-500"
                  onClick={() => {
                    addExerciseMutation.mutate(baseAddPayload(exercise.id));
                    setNotice(`Added ${exercise.name}.`);
                  }}
                >
                  <p className="font-medium">{exercise.name}</p>
                  <p className="text-xs text-slate-500">{exercise.category} - {exercise.muscle_group} - {exercise.equipment}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
