import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import SubjectExplorerPage from "./pages/SubjectExplorerPage";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import QuizPage from "./pages/QuizPage";
import SummaryPage from "./pages/SummaryPage";
import MindMapPage from "./pages/MindMapPage";
import ArchitecturePage from "./pages/ArchitecturePage";
import AnalyticsPage from "./pages/AnalyticsPage";

export default function App() {
  return (
    <BrowserRouter>
      <React.StrictMode>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/subjects" element={<SubjectExplorerPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />

          <Route path="/chat" element={<ChatPage />} />
          <Route path="/quiz" element={<QuizPage />} />
          <Route path="/summary" element={<SummaryPage />} />
          <Route path="/mindmap" element={<MindMapPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/architecture" element={<ArchitecturePage />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </React.StrictMode>
    </BrowserRouter>
  );
}