import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ClientDetailsPage } from "./pages/ClientDetailsPage";
import { ClientViewPage } from "./pages/ClientViewPage";
import { ClientsPage } from "./pages/ClientsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExercisesPage } from "./pages/ExercisesPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { PlanBuilderPage } from "./pages/PlanBuilderPage";
import { PlansPage } from "./pages/PlansPage";
import { RegisterPage } from "./pages/RegisterPage";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/exercises" element={<ExercisesPage />} />
        <Route path="/plans" element={<PlansPage />} />
        <Route path="/plans/:id" element={<PlanBuilderPage />} />
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/clients/:id" element={<ClientDetailsPage />} />
        <Route path="/client-view/:clientId" element={<ClientViewPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
