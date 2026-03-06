"use client";

import {
    LayoutDashboard,
    FileText,
    Sparkles,
    BarChart3,
    Radar,
    Settings,
    Zap,
    TrendingUp,
    Calendar,
} from "lucide-react";

interface SidebarProps {
    activePage: string;
    onNavigate: (page: string) => void;
}

const navItems = [
    { key: "overview", label: "Overview", icon: LayoutDashboard },
    { key: "content", label: "Content Queue", icon: Calendar, badge: 5 },
    { key: "generator", label: "AI Generator", icon: Sparkles },
    { key: "analytics", label: "Analytics", icon: BarChart3 },
    { key: "trends", label: "Trend Radar", icon: Radar },
];

const bottomItems = [
    { key: "settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <Zap size={18} />
                </div>
                <span className="sidebar-brand">GrowthOS</span>
            </div>

            <nav className="sidebar-nav">
                <span className="nav-section-label">Main</span>
                {navItems.map((item) => (
                    <div
                        key={item.key}
                        className={`nav-item ${activePage === item.key ? "active" : ""}`}
                        onClick={() => onNavigate(item.key)}
                    >
                        <item.icon size={18} />
                        <span>{item.label}</span>
                        {item.badge && <span className="nav-badge">{item.badge}</span>}
                    </div>
                ))}

                <span className="nav-section-label" style={{ marginTop: "16px" }}>
                    Intelligence
                </span>
                <div
                    className="nav-item"
                    style={{ opacity: 0.5, cursor: "default" }}
                >
                    <TrendingUp size={18} />
                    <span>Strategy Engine</span>
                    <span className="badge badge-purple" style={{ marginLeft: "auto", fontSize: 10 }}>
                        Phase 2
                    </span>
                </div>

                <div style={{ flex: 1 }} />

                {bottomItems.map((item) => (
                    <div
                        key={item.key}
                        className={`nav-item ${activePage === item.key ? "active" : ""}`}
                        onClick={() => onNavigate(item.key)}
                    >
                        <item.icon size={18} />
                        <span>{item.label}</span>
                    </div>
                ))}

                {/* Quota indicator */}
                <div style={{
                    padding: "16px",
                    margin: "8px 0",
                    background: "var(--bg-glass)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-subtle)",
                }}>
                    <div style={{
                        display: "flex", justifyContent: "space-between",
                        marginBottom: 8, fontSize: 12,
                    }}>
                        <span style={{ color: "var(--text-tertiary)" }}>Monthly Quota</span>
                        <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>67%</span>
                    </div>
                    <div style={{
                        height: 4, background: "var(--bg-tertiary)",
                        borderRadius: 2, overflow: "hidden",
                    }}>
                        <div style={{
                            width: "67%", height: "100%",
                            background: "var(--gradient-primary)",
                            borderRadius: 2,
                        }} />
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                        1,005 / 1,500 tweets used
                    </div>
                </div>
            </nav>
        </aside>
    );
}
