export type User = {
  id: string;
  email: string;
  role: "trainer" | "admin";
};

export type Exercise = {
  id: string;
  name: string;
  category: string;
  equipment: string;
  muscle_group: string;
  default_tempo: string;
  description: string;
  video_url?: string | null;
  created_by_trainer_id?: string | null;
};

export type Client = {
  id: string;
  trainer_id: string;
  name: string;
  email?: string | null;
  notes?: string | null;
};

export type PlanTemplate = {
  id: string;
  trainer_id: string;
  name: string;
  description: string;
  weeks_count: number;
};

export type PlanDay = {
  id: string;
  plan_template_id: string;
  week_number: number;
  day_name: string;
};

export type PlanExercise = {
  id: string;
  plan_day_id: string;
  exercise_id: string;
  sets: number;
  reps: string;
  rpe?: number | null;
  weight?: number | null;
  rest_seconds?: number | null;
  tempo?: string | null;
  notes?: string | null;
};


export type ExerciseCatalogResponse = {
  items: Exercise[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ExerciseFilterMetaResponse = {
  categories: string[];
  equipments: string[];
  muscle_groups: string[];
};


export type ExerciseSuggestion = {
  exercise_id: string;
  name: string;
  category: string;
  equipment: string;
  muscle_group: string;
  reason: string;
  sets: number;
  reps: string;
  target_rpe: number | null;
  rest_seconds: number | null;
};

export type ExerciseSuggestResponse = {
  goal: "strength" | "hypertrophy" | "fat_loss" | "conditioning" | "general_fitness";
  session_focus: "full_body" | "push" | "pull" | "legs" | "core" | "conditioning";
  suggestions: ExerciseSuggestion[];
};


export type StarterPlanSuggestion = {
  slug: string;
  name: string;
  description: string;
  weeks_count: number;
  sessions_per_week: number;
  goal: string;
};

export type StarterPlanImportResponse = {
  plan: PlanTemplate;
  days_created: number;
  exercises_created: number;
  missing_exercises: string[];
};
