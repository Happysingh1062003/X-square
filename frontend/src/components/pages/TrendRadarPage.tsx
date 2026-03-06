"use client";

import { TrendingUp, TrendingDown, Minus, Sparkles, ExternalLink } from "lucide-react";
import { mockTrending } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";

const categories = ["all", "AI", "Dev", "SaaS", "Business", "Startups"];

export default function TrendRadarPage() {
    const { trendCategory, setTrendCategory } = useDashboardStore();

    const filtered = trendCategory === "all"
        ? mockTrending
        : mockTrending.filter((t) => t.category === trendCategory);

    return (
        <div>
            {/* Header */}
            <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                marginBottom: 24,
            }}>
                <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <div className="pulse-dot" />
                        <span style={{ fontSize: 13, color: "var(--success)", fontWeight: 600 }}>
                            Live Monitoring
                        </span>
                    </div>
                    <p style={{ fontSize: 14, color: "var(--text-tertiary)" }}>
                        Pre-viral signal detection — trends detected 12-24h before mainstream spike
                    </p>
                </div>
                <button className="btn btn-secondary btn-sm">
                    <Sparkles size={14} /> Generate content on trending topic
                </button>
            </div>

            {/* Category Filter */}
            <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
                {categories.map((cat) => (
                    <button
                        key={cat}
                        className={`btn btn-sm ${trendCategory === cat ? "btn-primary" : "btn-secondary"}`}
                        onClick={() => setTrendCategory(cat)}
                    >
                        {cat === "all" ? "All Topics" : cat}
                    </button>
                ))}
            </div>

            {/* Rising Trends */}
            <div style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--text-secondary)" }}>
                    🔥 Rising Trends
                </h3>
                <div className="trends-grid">
                    {filtered.filter((t) => t.status === "rising").map((trend) => (
                        <TrendCard key={trend.id} trend={trend} />
                    ))}
                </div>
            </div>

            {/* Peaking */}
            {filtered.some((t) => t.status === "peaking") && (
                <div style={{ marginBottom: 24 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--text-secondary)" }}>
                        📈 At Peak
                    </h3>
                    <div className="trends-grid">
                        {filtered.filter((t) => t.status === "peaking").map((trend) => (
                            <TrendCard key={trend.id} trend={trend} />
                        ))}
                    </div>
                </div>
            )}

            {/* Declining */}
            {filtered.some((t) => t.status === "declining") && (
                <div>
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--text-secondary)" }}>
                        📉 Declining
                    </h3>
                    <div className="trends-grid">
                        {filtered.filter((t) => t.status === "declining").map((trend) => (
                            <TrendCard key={trend.id} trend={trend} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function TrendCard({ trend }: { trend: typeof mockTrending[0] }) {
    const statusIcon = {
        rising: <TrendingUp size={14} style={{ color: "var(--success)" }} />,
        peaking: <Minus size={14} style={{ color: "var(--warning)" }} />,
        declining: <TrendingDown size={14} style={{ color: "var(--danger)" }} />,
    };
    const statusColor = {
        rising: "badge-green",
        peaking: "badge-yellow",
        declining: "badge-red",
    };

    return (
        <div className="trend-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <span className={`badge ${statusColor[trend.status]}`}>
                    {statusIcon[trend.status]} {trend.status}
                </span>
                <span className="badge badge-purple" style={{ fontSize: 11 }}>{trend.category}</span>
            </div>
            <div className="trend-topic">{trend.topic}</div>
            <div className="trend-category">
                Score: {(trend.score * 100).toFixed(0)}% viral potential
            </div>

            {/* Velocity Bar */}
            <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                    <span style={{ color: "var(--text-muted)" }}>Velocity</span>
                    <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>{trend.velocity.toFixed(1)}x</span>
                </div>
                <div style={{ height: 4, background: "var(--bg-tertiary)", borderRadius: 2 }}>
                    <div style={{
                        width: `${Math.min(trend.velocity / 5 * 100, 100)}%`,
                        height: "100%",
                        background: trend.velocity > 3 ? "var(--success)" : trend.velocity > 2 ? "var(--accent-primary)" : "var(--warning)",
                        borderRadius: 2,
                        transition: "width 0.3s ease",
                    }} />
                </div>
            </div>

            <div className="trend-stats">
                <div className="trend-stat">
                    Volume: <span>{(trend.tweetVolume / 1000).toFixed(1)}K</span>
                </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button className="btn btn-secondary btn-sm" style={{ flex: 1 }}>
                    <Sparkles size={12} /> Write about this
                </button>
                <button className="btn btn-ghost btn-sm btn-icon">
                    <ExternalLink size={14} />
                </button>
            </div>
        </div>
    );
}
