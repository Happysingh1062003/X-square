"use client";

import {
    Eye, Heart, Users, TrendingUp,
    ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import {
    AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid,
} from "recharts";
import { mockAnalytics } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";

export default function AnalyticsPage() {
    const { analyticsPeriod, setAnalyticsPeriod } = useDashboardStore();
    const a = mockAnalytics;

    return (
        <div>
            {/* Period Selector */}
            <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
                {(["24h", "7d", "30d", "90d"] as const).map((p) => (
                    <button
                        key={p}
                        className={`btn btn-sm ${analyticsPeriod === p ? "btn-primary" : "btn-secondary"}`}
                        onClick={() => setAnalyticsPeriod(p)}
                    >
                        {p}
                    </button>
                ))}
            </div>

            {/* Metrics */}
            <div className="metrics-grid">
                <MetricCard icon={<Eye size={16} />} label="Impressions"
                    value={fmt(a.impressions)} delta={a.impressionsDelta} color="var(--info)" />
                <MetricCard icon={<Heart size={16} />} label="Engagement Rate"
                    value={`${(a.engagementRate * 100).toFixed(1)}%`} delta={a.engagementDelta} color="var(--accent-primary)" />
                <MetricCard icon={<Users size={16} />} label="New Followers"
                    value={`+${a.followersGained}`} delta={a.followersDelta} color="var(--success)" />
                <MetricCard icon={<TrendingUp size={16} />} label="Tweets Published"
                    value={String(a.tweetsPublished)} delta={a.tweetsDelta} color="var(--warning)" />
            </div>

            {/* Charts */}
            <div className="charts-grid">
                {/* Engagement Over Time */}
                <div className="card">
                    <div className="card-header">
                        <div className="card-title">Engagement Trend</div>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={a.dailyMetrics}>
                                <defs>
                                    <linearGradient id="engGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#7c5cfc" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#7c5cfc" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="impGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.2} />
                                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                <XAxis dataKey="date" tick={{ fill: "#6a6a82", fontSize: 12 }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: "#6a6a82", fontSize: 12 }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{
                                        background: "#1a1a28", border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: 8, fontSize: 13,
                                    }}
                                    labelStyle={{ color: "#f0f0f5" }}
                                />
                                <Area type="monotone" dataKey="impressions" stroke="#3b82f6" fill="url(#impGrad)" strokeWidth={2} name="Impressions" />
                                <Area type="monotone" dataKey="engagements" stroke="#7c5cfc" fill="url(#engGrad)" strokeWidth={2} name="Engagements" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Hourly Heatmap */}
                <div className="card">
                    <div className="card-header">
                        <div className="card-title">Hourly Activity</div>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={a.hourlyEngagement}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                <XAxis dataKey="hour" tick={{ fill: "#6a6a82", fontSize: 11 }} axisLine={false} tickLine={false}
                                    tickFormatter={(h: number) => h % 4 === 0 ? `${h}:00` : ""} />
                                <YAxis tick={{ fill: "#6a6a82", fontSize: 11 }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{
                                        background: "#1a1a28", border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: 8, fontSize: 13,
                                    }}
                                    labelFormatter={(h) => `${h}:00 UTC`}
                                />
                                <Bar dataKey="count" fill="#7c5cfc" radius={[4, 4, 0, 0]} name="Engagements" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Top Tweets */}
            <div className="card">
                <div className="card-header">
                    <div className="card-title">Top Performing Tweets</div>
                </div>
                <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                                {["Tweet", "Impressions", "Likes", "Retweets", "Replies", "Virality"].map((h) => (
                                    <th key={h} style={{
                                        textAlign: "left", padding: "10px 12px",
                                        fontSize: 12, fontWeight: 600, color: "var(--text-muted)",
                                        textTransform: "uppercase", letterSpacing: "0.05em",
                                    }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {a.topTweets.map((t) => (
                                <tr key={t.id} style={{
                                    borderBottom: "1px solid var(--border-subtle)",
                                    transition: "background 0.15s",
                                }}>
                                    <td style={{ padding: "14px 12px", maxWidth: 300 }}>
                                        <div style={{
                                            fontSize: 13, overflow: "hidden", textOverflow: "ellipsis",
                                            display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as any,
                                        }}>
                                            {t.text}
                                        </div>
                                    </td>
                                    <td style={{ padding: "14px 12px", fontSize: 14, fontWeight: 600 }}>
                                        {t.publishedMetrics?.impressions?.toLocaleString()}
                                    </td>
                                    <td style={{ padding: "14px 12px", fontSize: 14 }}>
                                        {t.publishedMetrics?.likes?.toLocaleString()}
                                    </td>
                                    <td style={{ padding: "14px 12px", fontSize: 14 }}>
                                        {t.publishedMetrics?.retweets?.toLocaleString()}
                                    </td>
                                    <td style={{ padding: "14px 12px", fontSize: 14 }}>
                                        {t.publishedMetrics?.replies?.toLocaleString()}
                                    </td>
                                    <td style={{ padding: "14px 12px" }}>
                                        <ViralityBar score={t.viralityScore} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function MetricCard({ icon, label, value, delta, color }: {
    icon: React.ReactNode; label: string; value: string; delta: number; color: string;
}) {
    const pos = delta >= 0;
    return (
        <div className="metric-card">
            <div className="metric-label"><span style={{ color }}>{icon}</span>{label}</div>
            <div className="metric-value">{value}</div>
            <span className={`metric-change ${pos ? "positive" : "negative"}`}>
                {pos ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {Math.abs(delta * 100).toFixed(0)}%
            </span>
        </div>
    );
}

function ViralityBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const color = pct >= 80 ? "var(--success)" : pct >= 60 ? "var(--accent-primary)" : "var(--warning)";
    return (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 60, height: 6, background: "var(--bg-tertiary)", borderRadius: 3 }}>
                <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3 }} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, color }}>{pct}</span>
        </div>
    );
}

function fmt(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
}
