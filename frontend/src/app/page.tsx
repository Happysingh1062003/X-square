"use client";

import { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import OverviewPage from "@/components/pages/OverviewPage";
import ContentQueuePage from "@/components/pages/ContentQueuePage";
import GeneratorPage from "@/components/pages/GeneratorPage";
import AnalyticsPage from "@/components/pages/AnalyticsPage";
import TrendRadarPage from "@/components/pages/TrendRadarPage";
import { useDashboardStore } from "@/lib/store";

export default function Home() {
  const { activePage, setActivePage } = useDashboardStore();

  const renderPage = () => {
    switch (activePage) {
      case "content": return <ContentQueuePage />;
      case "generator": return <GeneratorPage />;
      case "analytics": return <AnalyticsPage />;
      case "trends": return <TrendRadarPage />;
      default: return <OverviewPage />;
    }
  };

  const pageTitle: Record<string, string> = {
    overview: "Dashboard",
    content: "Content Queue",
    generator: "AI Generator",
    analytics: "Analytics",
    trends: "Trend Radar",
  };

  return (
    <div className="dashboard-layout">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">
        <Header title={pageTitle[activePage] || "Dashboard"} />
        <div className="page-content">{renderPage()}</div>
      </main>
    </div>
  );
}
