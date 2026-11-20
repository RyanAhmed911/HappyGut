import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router";
import { AppShell } from "./components/shell";
import { About, PublicFrame } from "./pages/About";
import { auth } from "./lib/api";
import { CarePage } from "./pages/Care";
import { Check } from "./pages/Check";
import { Diary } from "./pages/Diary";
import { Docs } from "./pages/Docs";
import { DocsAdmin } from "./pages/DocsAdmin";
import { Foods } from "./pages/Foods";
import { Gut } from "./pages/Gut";
import { History, HistoryDetail } from "./pages/History";
import { Patterns } from "./pages/Patterns";
import { Report } from "./pages/Report";
import { SettingsPage } from "./pages/Settings";
import { Today } from "./pages/Today";
import { Welcome } from "./pages/Welcome";

function Protected() {
  const location = useLocation();
  if (!auth.token) return <Navigate to="/welcome" replace state={{ from: location.pathname }} />;
  return <AppShell />;
}

export function App() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { pathname } = useLocation();

  useEffect(() => {
    const onSignedOut = (): void => {
      queryClient.clear();
      void navigate("/welcome", { replace: true });
    };
    window.addEventListener("hg:signed-out", onSignedOut);
    return () => window.removeEventListener("hg:signed-out", onSignedOut);
  }, [navigate, queryClient]);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [pathname]);

  return (
    <Routes>
      <Route path="/welcome" element={<Welcome />} />
      <Route path="/docs" element={<Docs />} />
      <Route path="/docs/admin" element={<DocsAdmin />} />
      <Route path="/about" element={auth.token ? <AppShell /> : <PublicFrame />}>
        <Route index element={<About />} />
      </Route>
      <Route element={<Protected />}>
        <Route index element={<Today />} />
        <Route path="check" element={<Check />} />
        <Route path="diary" element={<Diary />} />
        <Route path="diary/:date" element={<Diary />} />
        <Route path="care" element={<CarePage />} />
        <Route path="patterns" element={<Patterns />} />
        <Route path="gut" element={<Gut />} />
        <Route path="foods" element={<Foods />} />
        <Route path="history" element={<History />} />
        <Route path="history/:id" element={<HistoryDetail />} />
        <Route path="report" element={<Report />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
