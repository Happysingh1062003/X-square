"use client";

import {
    Eye, Heart, Users, FileText, TrendingUp,
    ArrowUpRight, ArrowDownRight, Zap, Clock, Sparkles,
} from "lucide-react";
import { mockAnalytics, mockQueue, mockTrending } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";

export default function OverviewPage() {
    const { setActivePage } = useDashboardStore();
    const a = mockAnalytics;

    return (
        <div>
            {/* Metrics Row */}
            <div className="metrics-grid">
                <MetricCard
                    icon={<Eye size={16} />}
                    label="Impressions"
                    value={formatNumber(a.impressions)}
                    delta={a.impressionsDelta}
                    color="var(--info)"
                />
                <MetricCard
                    icon={<Heart size={16} />}
                    label="Engagement Rate"
                    value={`${(a.engagementRate * 100).toFixed(1)}%`}
                    delta={a.engagementDelta}
                    color="var(--accent-primary)"
                />
                <MetricCard
                    icon={<Users size={16} />}
                    label="Followers Gained"
                    value={`+${a.followersGained}`}
                    delta={a.followersDelta}
                    color="var(--success)"
                />
                <MetricCard
                    icon={<FileText size={16} />}
                    label="Tweets Published"
                    value={String(a.tweetsPublished)}
                    delta={a.tweetsDelta}
                    color="var(--warning)"
                />
            </div>

            {/* Quick Actions */}
            <div style={{
                display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
                gap: 16, marginBottom: 24,
            }}>
                <button
                    className="card"
                    onClick={() => setActivePage("generator")}
                    style={{
                        cursor: "pointer", display: "flex", alignItems: "center",
                        gap: 16, padding: "20px 24px", textAlign: "left", border: "1px solid var(--border-subtle)",
                    }}
                >
                    <div style={{
                        width: 44, height: 44, borderRadius: "var(--radius-md)",
                        background: "rgba(124, 92, 252, 0.15)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                        <Sparkles size={20} style={{ color: "var(--accent-primary)" }} />
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>Generate Content</div>
                        <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
                            AI-powered tweet & thread creation
                        </div>
                    </div>
                </button>

                <button
                    className="card"
                    onClick={() => setActivePage("content")}
                    style={{
                        cursor: "pointer", display: "flex", alignItems: "center",
                        gap: 16, padding: "20px 24px", textAlign: "left", border: "1px solid var(--border-subtle)",
                    }}
                >
                    <div style={{
                        width: 44, height: 44, borderRadius: "var(--radius-md)",
                        background: "rgba(245, 158, 11, 0.15)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                        <Clock size={20} style={{ color: "var(--warning)" }} />
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>Content Queue</div>
                        <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
                            {mockQueue.filter(q => q.status === "scheduled").length} posts scheduled
                        </div>
                    </div>
                </button>

                <button
                    className="card"
                    onClick={() => setActivePage("trends")}
                    style={{
                        cursor: "pointer", display: "flex", alignItems: "center",
                        gap: 16, padding: "20px 24px", textAlign: "left", border: "1px solid var(--border-subtle)",
                    }}
                >
                    <div style={{
                        width: 44, height: 44, borderRadius: "var(--radius-md)",
                        background: "rgba(34, 197, 94, 0.15)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                        <Zap size={20} style={{ color: "var(--success)" }} />
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>Trend Radar</div>
                        <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
                            {mockTrending.filter(t => t.status === "rising").length} rising topics
                        </div>
                    </div>
                </button>
            </div>

            {/* Upcoming & Top Performers */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {/* Upcoming Posts */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <div className="card-title">Upcoming Posts</div>
                            <div className="card-subtitle">Next 48 hours</div>
                        </div>
                        <button className="btn btn-ghost btn-sm" onClick={() => setActivePage("content")}>
                            View all
                        </button>
                    </div>
                    <div className="queue-list">
                        {mockQueue.filter(q => q.status === "scheduled").slice(0, 3).map((post) => (
                            <div key={post.id} className="queue-item" style={{ padding: "12px 16px" }}>
                                <div className="queue-item-time">
                                    {new Date(post.scheduledTime).toLocaleDateString("en-US", {
                                        month: "short", day: "numeric",
                                    })}{" "}
                                    {new Date(post.scheduledTime).toLocaleTimeString("en-US", {
                                        hour: "numeric", minute: "2-digit",
                                    })}
                                </div>
                                <div className="queue-item-content">
                                    <div className="queue-item-text" style={{
                                        overflow: "hidden", textOverflow: "ellipsis",
                                        display: "-webkit-box", WebkitLineClamp: 2,
                                        WebkitBoxOrient: "vertical",
                                    }}>
                                        {post.text}
                                    </div>
                                    <div className="queue-item-meta">
                                        <span className={`badge ${post.contentType === "thread" ? "badge-purple" : "badge-blue"}`}>
                                            {post.contentType === "thread" ? "🧵 Thread" : "Tweet"}
                                        </span>
                                        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                            Score: {(post.viralityScore * 100).toFixed(0)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Top Performers */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <div className="card-title">Top Performers</div>
                            <div className="card-subtitle">Last 7 days</div>
                        </div>
                        <button className="btn btn-ghost btn-sm" onClick={() => setActivePage("analytics")}>
                            View all
                        </button>
                    </div>
                    <div className="queue-list">
                        {a.topTweets.map((tweet) => (
                            <div key={tweet.id} className="queue-item" style={{ padding: "12px 16px" }}>
                                <div style={{
                                    width: 48, height: 48, borderRadius: "var(--radius-md)",
                                    background: `rgba(124, 92, 252, ${tweet.viralityScore * 0.3})`,
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    flexShrink: 0, fontSize: 14, fontWeight: 700,
                                    color: "var(--accent-primary)",
                                }}>
                                    {(tweet.viralityScore * 100).toFixed(0)}
                                </div>
                                <div className="queue-item-content">
                                    <div className="queue-item-text" style={{
                                        overflow: "hidden", textOverflow: "ellipsis",
                                        display: "-webkit-box", WebkitLineClamp: 2,
                                        WebkitBoxOrient: "vertical", fontSize: 13,
                                    }}>
                                        {tweet.text}
                                    </div>
                                    <div className="queue-item-meta" style={{ gap: 16 }}>
                                        <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                                            ❤️ {tweet.publishedMetrics?.likes?.toLocaleString()}
                                        </span>
                                        <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                                            🔁 {tweet.publishedMetrics?.retweets?.toLocaleString()}
                                        </span>
                                        <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                                            👁️ {tweet.publishedMetrics?.impressions?.toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function MetricCard({
    icon, label, value, delta, color,
}: {
    icon: React.ReactNode; label: string; value: string; delta: number; color: string;
}) {
    const isPositive = delta >= 0;
    return (
        <div className="metric-card">
            <div className="metric-label">
                <span style={{ color }}>{icon}</span>
                {label}
            </div>
            <div className="metric-value">{value}</div>
            <span className={`metric-change ${isPositive ? "positive" : "negative"}`}>
                {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {Math.abs(delta * 100).toFixed(0)}%
            </span>
        </div>
    );
}

function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
}
