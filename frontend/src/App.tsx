import { Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import Dashboard from "@/pages/Dashboard";
import Portfolio from "@/pages/Portfolio";
import Agents from "@/pages/Agents";
import Reports from "@/pages/Reports";
import Chat from "@/pages/Chat";
import Settings from "@/pages/Settings";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
