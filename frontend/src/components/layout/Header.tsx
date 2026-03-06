"use client";

import { Bell, Search, Plus } from "lucide-react";

interface HeaderProps {
    title: string;
}

export default function Header({ title }: HeaderProps) {
    return (
        <header className="header">
            <h1 className="header-title">{title}</h1>
            <div className="header-actions">
                <div style={{
                    position: "relative", display: "flex", alignItems: "center",
                }}>
                    <Search
                        size={16}
                        style={{
                            position: "absolute", left: 12,
                            color: "var(--text-tertiary)",
                        }}
                    />
                    <input
                        className="input"
                        placeholder="Search content, trends..."
                        style={{
                            width: 240, paddingLeft: 36, height: 36,
                            fontSize: 13, background: "var(--bg-glass)",
                        }}
                    />
                </div>
                <button className="btn btn-ghost btn-icon" style={{ position: "relative" }}>
                    <Bell size={18} />
                    <span style={{
                        position: "absolute", top: 6, right: 6,
                        width: 7, height: 7, borderRadius: "50%",
                        background: "var(--danger)",
                    }} />
                </button>
                <button className="btn btn-primary btn-sm">
                    <Plus size={16} />
                    New Post
                </button>
                <div style={{
                    width: 34, height: 34, borderRadius: "50%",
                    background: "var(--gradient-primary)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 13, fontWeight: 700, cursor: "pointer",
                }}>
                    JD
                </div>
            </div>
        </header>
    );
}
