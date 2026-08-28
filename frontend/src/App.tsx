import { lazy, Suspense, useEffect } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { LoadingPage } from "@/components/common/LoadingSpinner";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { Toaster } from "@/components/ui/toast";
import { useAuth } from "@/contexts/AuthContext";

const Dashboard = lazy(() => import("@/features/dashboard/DashboardPage"));
const Chat = lazy(() => import("@/features/chat/Chat"));
const Reports = lazy(() => import("@/features/reports/Reports"));
const Landing = lazy(() => import("@/features/auth/Landing"));

function App() {
  return (
    <>
      <Toaster richColors position="top-right" />
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<LandingRoute />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route
                path="dashboard"
                element={
                  <Suspense fallback={<LoadingPage />}>
                    <Dashboard />
                  </Suspense>
                }
              />
              <Route
                path="chat"
                element={
                  <Suspense fallback={<LoadingPage />}>
                    <Chat />
                  </Suspense>
                }
              />
              <Route
                path="reports"
                element={
                  <Suspense fallback={<LoadingPage />}>
                    <Reports />
                  </Suspense>
                }
              />
            </Route>
          </Route>
        </Routes>
      </ErrorBoundary>
    </>
  );
}

function LandingRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return (
    <Suspense fallback={<LoadingPage />}>
      <Landing />
    </Suspense>
  );
}

export default App;
