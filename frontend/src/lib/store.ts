import { create } from 'zustand';

interface DashboardState {
    // Sidebar
    sidebarOpen: boolean;
    activePage: string;
    toggleSidebar: () => void;
    setActivePage: (page: string) => void;

    // Generator
    generatorTopic: string;
    generatorStyle: string;
    generatorNiche: string;
    generatorContentType: 'single_tweet' | 'thread' | 'reply';
    selectedVariantId: string | null;
    isGenerating: boolean;
    setGeneratorTopic: (topic: string) => void;
    setGeneratorStyle: (style: string) => void;
    setGeneratorNiche: (niche: string) => void;
    setGeneratorContentType: (type: 'single_tweet' | 'thread' | 'reply') => void;
    setSelectedVariant: (id: string | null) => void;
    setIsGenerating: (val: boolean) => void;

    // Analytics
    analyticsPeriod: '24h' | '7d' | '30d' | '90d';
    setAnalyticsPeriod: (period: '24h' | '7d' | '30d' | '90d') => void;

    // Trends
    trendCategory: string;
    setTrendCategory: (cat: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
    sidebarOpen: true,
    activePage: 'overview',
    toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    setActivePage: (page) => set({ activePage: page }),

    generatorTopic: '',
    generatorStyle: 'authoritative',
    generatorNiche: 'AI',
    generatorContentType: 'single_tweet',
    selectedVariantId: null,
    isGenerating: false,
    setGeneratorTopic: (topic) => set({ generatorTopic: topic }),
    setGeneratorStyle: (style) => set({ generatorStyle: style }),
    setGeneratorNiche: (niche) => set({ generatorNiche: niche }),
    setGeneratorContentType: (type) => set({ generatorContentType: type }),
    setSelectedVariant: (id) => set({ selectedVariantId: id }),
    setIsGenerating: (val) => set({ isGenerating: val }),

    analyticsPeriod: '7d',
    setAnalyticsPeriod: (period) => set({ analyticsPeriod: period }),

    trendCategory: 'all',
    setTrendCategory: (cat) => set({ trendCategory: cat }),
}));
