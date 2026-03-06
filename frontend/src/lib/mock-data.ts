// Mock data for frontend development before backend is live

export interface Tweet {
  id: string;
  text: string;
  scheduledTime: string;
  status: 'draft' | 'scheduled' | 'published' | 'failed';
  contentType: 'single_tweet' | 'thread' | 'reply';
  predictedEngagement: number;
  viralityScore: number;
  publishedMetrics?: {
    impressions: number;
    likes: number;
    retweets: number;
    replies: number;
    bookmarks: number;
  };
}

export interface AnalyticsData {
  period: string;
  impressions: number;
  impressionsDelta: number;
  engagements: number;
  engagementRate: number;
  engagementDelta: number;
  followersGained: number;
  followersDelta: number;
  tweetsPublished: number;
  tweetsDelta: number;
  hourlyEngagement: { hour: number; count: number }[];
  dailyMetrics: { date: string; impressions: number; engagements: number; followers: number }[];
  topTweets: Tweet[];
}

export interface TrendingTopic {
  id: string;
  topic: string;
  score: number;
  velocity: number;
  category: string;
  tweetVolume: number;
  status: 'rising' | 'peaking' | 'declining';
}

export interface GeneratedVariant {
  id: string;
  text: string;
  hookType: string;
  charCount: number;
  estimatedEngagement: 'high' | 'medium' | 'low';
  reasoning: string;
}

// ---- Mock Data ----

export const mockQueue: Tweet[] = [
  {
    id: 'q1', status: 'scheduled', contentType: 'single_tweet',
    text: 'Most AI startups will fail.\n\nNot because the tech is bad.\nBut because they\'re solving problems that don\'t exist.\n\nThe 1% who win? They find the pain first.',
    scheduledTime: '2026-03-07T15:00:00Z', predictedEngagement: 0.045, viralityScore: 0.72,
  },
  {
    id: 'q2', status: 'scheduled', contentType: 'thread',
    text: 'I spent 6 months studying the top 1% of SaaS founders.\n\nThey all do ONE thing differently that nobody talks about.\n\n🧵👇',
    scheduledTime: '2026-03-07T18:30:00Z', predictedEngagement: 0.062, viralityScore: 0.85,
  },
  {
    id: 'q3', status: 'scheduled', contentType: 'single_tweet',
    text: 'The best growth hack isn\'t a hack at all.\n\nIt\'s consistently showing up with valuable content for 12 months straight.\n\nNo shortcuts. No tricks. Just reps.',
    scheduledTime: '2026-03-08T14:00:00Z', predictedEngagement: 0.038, viralityScore: 0.58,
  },
  {
    id: 'q4', status: 'draft', contentType: 'single_tweet',
    text: 'Your product doesn\'t need more features.\n\nIt needs fewer features that work exceptionally well.',
    scheduledTime: '', predictedEngagement: 0.029, viralityScore: 0.42,
  },
  {
    id: 'q5', status: 'scheduled', contentType: 'single_tweet',
    text: 'I reviewed 200 AI startup pitch decks.\n\n3 patterns separated funded from forgotten:\n\n→ Specific user, not "everyone"\n→ Measurable ROI, not "efficiency"\n→ Existing workflow, not new behavior',
    scheduledTime: '2026-03-08T16:00:00Z', predictedEngagement: 0.051, viralityScore: 0.78,
  },
];

export const mockAnalytics: AnalyticsData = {
  period: '7d',
  impressions: 245_320,
  impressionsDelta: 0.12,
  engagements: 8_430,
  engagementRate: 0.0344,
  engagementDelta: 0.08,
  followersGained: 127,
  followersDelta: 0.23,
  tweetsPublished: 18,
  tweetsDelta: -0.1,
  hourlyEngagement: Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    count: Math.round(
      200 + 300 * Math.exp(-0.5 * Math.pow((h - 15) / 4, 2)) + Math.random() * 80
    ),
  })),
  dailyMetrics: [
    { date: 'Mar 1', impressions: 32000, engagements: 1100, followers: 18 },
    { date: 'Mar 2', impressions: 28500, engagements: 980, followers: 12 },
    { date: 'Mar 3', impressions: 41200, engagements: 1520, followers: 24 },
    { date: 'Mar 4', impressions: 35800, engagements: 1240, followers: 19 },
    { date: 'Mar 5', impressions: 38400, engagements: 1380, followers: 22 },
    { date: 'Mar 6', impressions: 45200, engagements: 1650, followers: 28 },
    { date: 'Mar 7', impressions: 24220, engagements: 560, followers: 4 },
  ],
  topTweets: [
    {
      id: 't1', status: 'published', contentType: 'thread',
      text: 'I spent 6 months studying 200 SaaS founders.\n\nHere\'s the #1 pattern that separates the winners 🧵',
      scheduledTime: '2026-03-03T15:00:00Z', predictedEngagement: 0.062, viralityScore: 0.91,
      publishedMetrics: { impressions: 45200, likes: 892, retweets: 234, replies: 156, bookmarks: 312 },
    },
    {
      id: 't2', status: 'published', contentType: 'single_tweet',
      text: 'Unpopular opinion: Most "AI-powered" products are just wrappers around GPT with a nice UI.\n\nThe real moat is proprietary data, not the model.',
      scheduledTime: '2026-03-05T14:00:00Z', predictedEngagement: 0.054, viralityScore: 0.84,
      publishedMetrics: { impressions: 38400, likes: 634, retweets: 187, replies: 98, bookmarks: 201 },
    },
  ],
};

export const mockTrending: TrendingTopic[] = [
  { id: 'tr1', topic: 'AI Agents', score: 0.92, velocity: 3.4, category: 'AI', tweetVolume: 12400, status: 'rising' },
  { id: 'tr2', topic: 'Vibe Coding', score: 0.87, velocity: 4.1, category: 'Dev', tweetVolume: 8900, status: 'rising' },
  { id: 'tr3', topic: 'MCP Protocol', score: 0.81, velocity: 2.8, category: 'AI', tweetVolume: 5600, status: 'rising' },
  { id: 'tr4', topic: 'Open Source LLMs', score: 0.78, velocity: 1.9, category: 'AI', tweetVolume: 15200, status: 'peaking' },
  { id: 'tr5', topic: 'Creator Economy', score: 0.71, velocity: 1.2, category: 'Business', tweetVolume: 9800, status: 'peaking' },
  { id: 'tr6', topic: 'Indie SaaS', score: 0.65, velocity: 0.8, category: 'SaaS', tweetVolume: 4200, status: 'declining' },
  { id: 'tr7', topic: 'RAG Pipelines', score: 0.82, velocity: 2.5, category: 'AI', tweetVolume: 3800, status: 'rising' },
  { id: 'tr8', topic: 'Y Combinator W26', score: 0.74, velocity: 3.8, category: 'Startups', tweetVolume: 7100, status: 'rising' },
  { id: 'tr9', topic: 'Micro SaaS', score: 0.59, velocity: 0.5, category: 'SaaS', tweetVolume: 2800, status: 'declining' },
];

export const mockVariants: GeneratedVariant[] = [
  {
    id: 'v1', hookType: 'contrarian', charCount: 189, estimatedEngagement: 'high',
    text: 'Most AI startups will fail.\n\nNot because the tech is bad.\nBut because they\'re solving problems that don\'t exist.\n\nThe 1% who win? They find the pain first, then apply AI.',
    reasoning: 'Contrarian take with clear structure — challenges common belief while providing an actionable insight.',
  },
  {
    id: 'v2', hookType: 'question', charCount: 168, estimatedEngagement: 'high',
    text: 'What if 90% of AI products could be replaced by a well-designed spreadsheet?\n\nThe best AI companies know this.\n\nThat\'s why they focus on the 10% that can\'t.',
    reasoning: 'Provocative question that stops the scroll — forces reader to reconsider assumptions.',
  },
  {
    id: 'v3', hookType: 'story', charCount: 212, estimatedEngagement: 'medium',
    text: 'I reviewed 200 AI startup pitch decks last quarter.\n\n3 patterns separated funded from forgotten:\n\n→ Specific user, not "everyone"\n→ Measurable ROI, not "efficiency"\n→ Existing workflow, not new behavior',
    reasoning: 'Personal authority + concrete framework = high save rate.',
  },
];
