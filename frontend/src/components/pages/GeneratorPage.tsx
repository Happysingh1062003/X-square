"use client";

import { Sparkles, Send, RotateCw, Check, Copy } from "lucide-react";
import { useState } from "react";
import { mockVariants, type GeneratedVariant } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";

export default function GeneratorPage() {
    const {
        generatorTopic, setGeneratorTopic,
        generatorStyle, setGeneratorStyle,
        generatorNiche, setGeneratorNiche,
        generatorContentType, setGeneratorContentType,
        selectedVariantId, setSelectedVariant,
        isGenerating, setIsGenerating,
    } = useDashboardStore();

    const [variants, setVariants] = useState<GeneratedVariant[]>(mockVariants);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setSelectedVariant(null);
        // Simulate API call
        await new Promise((r) => setTimeout(r, 2000));
        setVariants(mockVariants);
        setIsGenerating(false);
    };

    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    return (
        <div className="generator-layout">
            {/* Left: Form */}
            <div>
                <div className="card">
                    <div className="card-header">
                        <div className="card-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <Sparkles size={18} style={{ color: "var(--accent-primary)" }} />
                            AI Content Generator
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label">Topic / Idea</label>
                        <textarea
                            className="input"
                            placeholder="What do you want to tweet about? E.g., 'Why most SaaS startups fail in year one'"
                            value={generatorTopic}
                            onChange={(e) => setGeneratorTopic(e.target.value)}
                            rows={3}
                        />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <div className="input-group">
                            <label className="input-label">Content Type</label>
                            <select
                                className="input select"
                                value={generatorContentType}
                                onChange={(e) => setGeneratorContentType(e.target.value as any)}
                            >
                                <option value="single_tweet">Single Tweet</option>
                                <option value="thread">Thread</option>
                                <option value="reply">Reply</option>
                            </select>
                        </div>

                        <div className="input-group">
                            <label className="input-label">Style</label>
                            <select
                                className="input select"
                                value={generatorStyle}
                                onChange={(e) => setGeneratorStyle(e.target.value)}
                            >
                                <option value="authoritative">Authoritative</option>
                                <option value="conversational">Conversational</option>
                                <option value="provocative">Provocative</option>
                                <option value="educational">Educational</option>
                                <option value="storytelling">Storytelling</option>
                            </select>
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label">Niche</label>
                        <select
                            className="input select"
                            value={generatorNiche}
                            onChange={(e) => setGeneratorNiche(e.target.value)}
                        >
                            <option value="AI">AI & Machine Learning</option>
                            <option value="SaaS">SaaS</option>
                            <option value="Finance">Finance</option>
                            <option value="Startups">Startups</option>
                            <option value="Web3">Web3</option>
                            <option value="Productivity">Productivity</option>
                        </select>
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handleGenerate}
                        disabled={isGenerating || !generatorTopic}
                        style={{ width: "100%", marginTop: 8, padding: "12px 20px" }}
                    >
                        {isGenerating ? (
                            <>
                                <RotateCw size={16} style={{ animation: "spin 1s linear infinite" }} />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Sparkles size={16} />
                                Generate Variants
                            </>
                        )}
                    </button>
                </div>

                {/* Tips */}
                <div className="card" style={{ marginTop: 16 }}>
                    <div className="card-title" style={{ fontSize: 14 }}>💡 Pro Tips</div>
                    <ul style={{
                        marginTop: 12, fontSize: 13, color: "var(--text-secondary)",
                        lineHeight: 1.8, paddingLeft: 16,
                    }}>
                        <li>Be specific — &quot;AI agent frameworks&quot; beats &quot;AI&quot;</li>
                        <li>Include a contrarian angle for higher engagement</li>
                        <li>Threads perform best posted at 8 AM or 8 PM your audience&apos;s time</li>
                        <li>Your top hooks use story and contrarian formats</li>
                    </ul>
                </div>
            </div>

            {/* Right: Variants */}
            <div>
                <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    marginBottom: 16,
                }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600 }}>
                        Generated Variants
                        {variants.length > 0 && (
                            <span style={{ color: "var(--text-muted)", fontWeight: 400, marginLeft: 8 }}>
                                ({variants.length})
                            </span>
                        )}
                    </h3>
                    {selectedVariantId && (
                        <button className="btn btn-primary btn-sm">
                            <Send size={14} /> Add to Queue
                        </button>
                    )}
                </div>

                {isGenerating ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="skeleton" style={{ height: 140, borderRadius: "var(--radius-md)" }} />
                        ))}
                    </div>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {variants.map((v) => (
                            <div
                                key={v.id}
                                className={`variant-card ${selectedVariantId === v.id ? "selected" : ""}`}
                                onClick={() => setSelectedVariant(v.id)}
                            >
                                <div style={{
                                    display: "flex", justifyContent: "space-between",
                                    marginBottom: 8,
                                }}>
                                    <span className="badge badge-purple">{v.hookType}</span>
                                    <span className={`badge ${v.estimatedEngagement === "high" ? "badge-green" :
                                            v.estimatedEngagement === "medium" ? "badge-yellow" : "badge-red"
                                        }`}>
                                        {v.estimatedEngagement} potential
                                    </span>
                                </div>
                                <div className="variant-text">{v.text}</div>
                                <div className="variant-meta">
                                    <span className="variant-chars">{v.charCount} chars</span>
                                    <div style={{ display: "flex", gap: 4 }}>
                                        <button
                                            className="btn btn-ghost btn-sm"
                                            onClick={(e) => { e.stopPropagation(); handleCopy(v.text, v.id); }}
                                        >
                                            {copiedId === v.id ? <Check size={14} /> : <Copy size={14} />}
                                            {copiedId === v.id ? "Copied!" : "Copy"}
                                        </button>
                                    </div>
                                </div>
                                <div style={{
                                    marginTop: 8, paddingTop: 8,
                                    borderTop: "1px solid var(--border-subtle)",
                                    fontSize: 12, color: "var(--text-tertiary)", fontStyle: "italic",
                                }}>
                                    {v.reasoning}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
