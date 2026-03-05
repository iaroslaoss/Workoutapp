import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";
import { Exercise, ExerciseCatalogResponse, ExerciseFilterMetaResponse } from "../lib/types";

const fallbackCategories = ["push", "pull", "legs", "core", "cardio", "other"];

type ExerciseForm = {
  name: string;
  category: string;
  equipment: string;
  muscle_group: string;
  default_tempo: string;
  description: string;
  video_url: string;
};

const PAGE_SIZE = 25;

export function ExercisesPage() {
  const api = useApi();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState("");
  const [equipment, setEquipment] = useState("");
  const [muscleGroup, setMuscleGroup] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<ExerciseForm>({
    name: "",
    category: "push",
    equipment: "",
    muscle_group: "",
    default_tempo: "3-1-1-0",
    description: "",
    video_url: "",
  });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingForm, setEditingForm] = useState<ExerciseForm | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 250);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, category, equipment, muscleGroup]);

  const metaQuery = useQuery({
    queryKey: ["exercises-meta"],
    queryFn: () => api.get<ExerciseFilterMetaResponse>("/exercises/meta"),
  });

  const catalogQuery = useQuery({
    queryKey: ["exercises-catalog", debouncedSearch, category, equipment, muscleGroup, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (debouncedSearch) params.set("name", debouncedSearch);
      if (category) params.set("category", category);
      if (equipment) params.set("equipment", equipment);
      if (muscleGroup) params.set("muscle_group", muscleGroup);
      params.set("page", String(page));
      params.set("page_size", String(PAGE_SIZE));
      return api.get<ExerciseCatalogResponse>(`/exercises/catalog?${params.toString()}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post<Exercise>("/exercises", { ...form, video_url: form.video_url || null }),
    onSuccess: () => {
      setForm({
        name: "",
        category: "push",
        equipment: "",
        muscle_group: "",
        default_tempo: "3-1-1-0",
        description: "",
        video_url: "",
      });
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["exercises-catalog"] });
      queryClient.invalidateQueries({ queryKey: ["exercises-meta"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: string; body: Partial<ExerciseForm> }) => api.put<Exercise>(`/exercises/${payload.id}`, payload.body),
    onSuccess: () => {
      setEditingId(null);
      setEditingForm(null);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["exercises-catalog"] });
      queryClient.invalidateQueries({ queryKey: ["exercises-meta"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.del<void>(`/exercises/${id}`),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["exercises-catalog"] });
      queryClient.invalidateQueries({ queryKey: ["exercises-meta"] });
    },
    onError: (err) => setError((err as Error).message),
  });

  const categories = useMemo(() => {
    const fromMeta = metaQuery.data?.categories || [];
    return fromMeta.length > 0 ? fromMeta : fallbackCategories;
  }, [metaQuery.data?.categories]);

  const equipmentValues = metaQuery.data?.equipments || [];
  const muscleValues = metaQuery.data?.muscle_groups || [];

  const onCreate = (e: FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.equipment.trim() || !form.muscle_group.trim() || !form.description.trim()) {
      setError("Name, equipment, muscle group, and description are required.");
      return;
    }
    setError(null);
    createMutation.mutate();
  };

  const startEdit = (exercise: Exercise) => {
    setEditingId(exercise.id);
    setEditingForm({
      name: exercise.name,
      category: exercise.category,
      equipment: exercise.equipment,
      muscle_group: exercise.muscle_group,
      default_tempo: exercise.default_tempo,
      description: exercise.description,
      video_url: exercise.video_url || "",
    });
  };

  const saveEdit = (id: string) => {
    if (!editingForm) return;
    updateMutation.mutate({
      id,
      body: {
        ...editingForm,
        video_url: editingForm.video_url || undefined,
      },
    });
  };

  const rows = catalogQuery.data?.items || [];
  const total = catalogQuery.data?.total || 0;
  const totalPages = catalogQuery.data?.total_pages || 1;
  const start = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const end = total === 0 ? 0 : Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-2xl font-semibold">Exercise Bank</h1>
          <p className="text-sm text-slate-500">{total} total matches</p>
        </div>

        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div className="flex flex-wrap gap-2">
          <button className={`btn-secondary ${category === "" ? "ring-2 ring-teal-200" : ""}`} onClick={() => setCategory("")}>All</button>
          {categories.map((c) => (
            <button
              key={c}
              className={`btn-secondary ${category === c ? "ring-2 ring-teal-200" : ""}`}
              onClick={() => setCategory(c)}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="grid gap-2 md:grid-cols-4">
          <input className="input" placeholder="Search by name" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select className="input" value={equipment} onChange={(e) => setEquipment(e.target.value)}>
            <option value="">All equipment</option>
            {equipmentValues.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
          <select className="input" value={muscleGroup} onChange={(e) => setMuscleGroup(e.target.value)}>
            <option value="">All muscle groups</option>
            {muscleValues.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
          <button
            className="btn-secondary"
            onClick={() => {
              setSearch("");
              setCategory("");
              setEquipment("");
              setMuscleGroup("");
              setPage(1);
            }}
          >
            Clear Filters
          </button>
        </div>
      </div>

      <div className="card overflow-x-auto">
        <div className="mb-2 flex items-center justify-between text-sm text-slate-500">
          <p>Showing {start}-{end} of {total}</p>
          <div className="flex items-center gap-2">
            <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
            <span>Page {page} / {totalPages}</span>
            <button className="btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</button>
          </div>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left">Name</th>
              <th className="px-3 py-2 text-left">Category</th>
              <th className="px-3 py-2 text-left">Equipment</th>
              <th className="px-3 py-2 text-left">Muscle</th>
              <th className="px-3 py-2 text-left">Tempo</th>
              <th className="px-3 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((ex) => {
              const isEditing = editingId === ex.id && editingForm;
              return (
                <tr key={ex.id}>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <input className="input" value={editingForm.name} onChange={(e) => setEditingForm({ ...editingForm, name: e.target.value })} />
                    ) : ex.name}
                  </td>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <select className="input" value={editingForm.category} onChange={(e) => setEditingForm({ ...editingForm, category: e.target.value })}>
                        {fallbackCategories.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    ) : ex.category}
                  </td>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <input className="input" value={editingForm.equipment} onChange={(e) => setEditingForm({ ...editingForm, equipment: e.target.value })} />
                    ) : ex.equipment}
                  </td>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <input className="input" value={editingForm.muscle_group} onChange={(e) => setEditingForm({ ...editingForm, muscle_group: e.target.value })} />
                    ) : ex.muscle_group}
                  </td>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <input className="input" value={editingForm.default_tempo} onChange={(e) => setEditingForm({ ...editingForm, default_tempo: e.target.value })} />
                    ) : ex.default_tempo}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-2">
                      {isEditing ? (
                        <>
                          <button className="btn" onClick={() => saveEdit(ex.id)} disabled={updateMutation.isPending}>Save</button>
                          <button className="btn-secondary" onClick={() => { setEditingId(null); setEditingForm(null); }}>Cancel</button>
                        </>
                      ) : (
                        <button className="btn-secondary" onClick={() => startEdit(ex)}>Edit</button>
                      )}
                      <button className="btn-danger" onClick={() => deleteMutation.mutate(ex.id)} disabled={deleteMutation.isPending}>Delete</button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <form className="card grid gap-2 md:grid-cols-3" onSubmit={onCreate}>
        <h2 className="md:col-span-3 text-lg font-medium">Create Exercise</h2>
        <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} />
        <select className="input" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))}>
          {fallbackCategories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <input className="input" placeholder="Equipment" value={form.equipment} onChange={(e) => setForm((p) => ({ ...p, equipment: e.target.value }))} />
        <input className="input" placeholder="Muscle group" value={form.muscle_group} onChange={(e) => setForm((p) => ({ ...p, muscle_group: e.target.value }))} />
        <input className="input" placeholder="Default tempo (3-1-1-0)" value={form.default_tempo} onChange={(e) => setForm((p) => ({ ...p, default_tempo: e.target.value }))} />
        <input className="input" placeholder="Video URL (optional)" value={form.video_url} onChange={(e) => setForm((p) => ({ ...p, video_url: e.target.value }))} />
        <textarea className="input md:col-span-3" placeholder="Description" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
        <button className="btn md:col-span-3" type="submit" disabled={createMutation.isPending}>Add Exercise</button>
      </form>
    </div>
  );
}
