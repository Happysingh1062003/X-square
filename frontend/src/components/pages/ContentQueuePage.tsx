"use client";

import { Calendar, Edit3, Trash2, MoreVertical, GripVertical } from "lucide-react";
import { mockQueue } from "@/lib/mock-data";

export default function ContentQueuePage() {
    const scheduled = mockQueue.filter((p) => p.status === "scheduled");
    const drafts = mockQueue.filter((p) => p.status === "draft");

    return (
        <div>
            {/* Stats Bar */}
            <div style={{
                display: "flex", gap: 24, marginBottom: 24,
                padding: "16px 24px", background: "var(--bg-card)",
                borderRadius: "var(--radius-lg)", border: "1px solid var(--border-subtle)",
            }}>
                <StatItem label="Scheduled" value={scheduled.length} color="var(--info)" />
                <StatItem label="Drafts" value={drafts.length} color="var(--warning)" />
                <StatItem label="Published Today" value={2} color="var(--success)" />
                <StatItem label="Failed" value={0} color="var(--danger)" />
                <div style={{ flex: 1 }} />
                <button className="btn btn-primary btn-sm">
                    <Calendar size={14} /> Schedule Post
                </button>
            </div>

            {/* Queue */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <div>
                        <div className="card-title">Scheduled Posts</div>
                        <div className="card-subtitle">Drag to reorder priority</div>
                    </div>
                </div>
                <div className="queue-list">
                    {scheduled.map((post) => (
                        <div key={post.id} className="queue-item">
                            <div style={{
                                cursor: "grab", color: "var(--text-muted)",
                                display: "flex", alignItems: "center", paddingTop: 2,
                            }}>
                                <GripVertical size={16} />
                            </div>
                            <div className="queue-item-time">
                                <div style={{ fontWeight: 600, fontSize: 13 }}>
                                    {new Date(post.scheduledTime).toLocaleDateString("en-US", {
                                        weekday: "short", month: "short", day: "numeric",
                                    })}
                                </div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                    {new Date(post.scheduledTime).toLocaleTimeString("en-US", {
                                        hour: "numeric", minute: "2-digit",
                                    })}
                                </div>
                            </div>
                            <div className="queue-item-content">
                                <div className="queue-item-text">{post.text}</div>
                                <div className="queue-item-meta">
                                    <span className={`badge ${post.contentType === "thread" ? "badge-purple" : "badge-blue"
                                        }`}>
                                        {post.contentType === "thread" ? "🧵 Thread" : "Tweet"}
                                    </span>
                                    <ViralityBadge score={post.viralityScore} />
                                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                        Est. ER: {(post.predictedEngagement * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                            <div className="queue-item-actions" style={{ opacity: 1, gap: 4 }}>
                                <button className="btn btn-ghost btn-icon btn-sm">
                                    <Edit3 size={14} />
                                </button>
                                <button className="btn btn-ghost btn-icon btn-sm">
                                    <Trash2 size={14} style={{ color: "var(--danger)" }} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Drafts */}
            {drafts.length > 0 && (
                <div className="card">
                    <div className="card-header">
                        <div>
                            <div className="card-title">Drafts</div>
                            <div className="card-subtitle">Unscheduled content</div>
                        </div>
                    </div>
                    <div className="queue-list">
                        {drafts.map((post) => (
                            <div key={post.id} className="queue-item">
                                <div className="queue-item-content">
                                    <div className="queue-item-text">{post.text}</div>
                                    <div className="queue-item-meta">
                                        <span className="badge badge-yellow">Draft</span>
                                        <ViralityBadge score={post.viralityScore} />
                                    </div>
                                </div>
                                <button className="btn btn-secondary btn-sm">Schedule</button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function StatItem({ label, value, color }: { label: string; value: number; color: string }) {
    return (
        <div>
            <div style={{ fontSize: 12, color: "var(--text-tertiary)", marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
        </div>
    );
}

function ViralityBadge({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const cls = pct >= 75 ? "badge-green" : pct >= 50 ? "badge-yellow" : "badge-red";
    return <span className={`badge ${cls}`}>⚡ {pct}</span>;
}
