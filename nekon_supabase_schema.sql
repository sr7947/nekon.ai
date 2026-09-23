-- =============================================================================
-- nekon.ai — Supabase Database Schema
-- Run this in your Supabase SQL Editor to create tables for nekon.ai
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. News Articles Table (Source 1: AI Leader Blogs)
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    company_name TEXT NOT NULL, -- OpenAI, Anthropic, Google AI, DeepSeek, etc.
    category TEXT DEFAULT 'AI Release', -- Model Launch, Research, Infrastructure
    source_url TEXT NOT NULL UNIQUE,
    published_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'approved', -- pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tweet Posts Table (Source 2: X / Twitter Handles)
CREATE TABLE IF NOT EXISTS tweet_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    handle TEXT NOT NULL, -- @sama, @elonmusk, @claudeai, @karpathy, etc.
    author_name TEXT NOT NULL,
    tweet_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    tweet_url TEXT NOT NULL UNIQUE,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'approved', -- pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Leaderboard Rankings Table (Source 3: Artificial Analysis, DeepSWE, OpenRouter)
CREATE TABLE IF NOT EXISTS leaderboard_ranks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rank_position INT NOT NULL,
    model_name TEXT NOT NULL,
    provider TEXT NOT NULL, -- OpenAI, Anthropic, Google, DeepSeek, Meta
    score NUMERIC(5,2) NOT NULL,
    category TEXT NOT NULL, -- 'intelligence', 'coding_agents', 'deepswe', 'openrouter'
    source_name TEXT NOT NULL, -- 'Artificial Analysis', 'DeepSWE Datacurve', 'OpenRouter'
    last_synced TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Pending Approvals Queue Table (For Telegram Human-in-the-Loop)
CREATE TABLE IF NOT EXISTS pending_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL, -- 'news' or 'tweet'
    payload JSONB NOT NULL,
    telegram_message_id INT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Supabase Realtime for instant UI sync
ALTER PUBLICATION supabase_realtime ADD TABLE news_articles;
ALTER PUBLICATION supabase_realtime ADD TABLE tweet_posts;
ALTER PUBLICATION supabase_realtime ADD TABLE leaderboard_ranks;

-- Enable Row Level Security (RLS)
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tweet_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_ranks ENABLE ROW LEVEL SECURITY;

-- Allow public read access to approved news, tweets, and leaderboard ranks
CREATE POLICY "Public Read Approved News" ON news_articles FOR SELECT USING (status = 'approved');
CREATE POLICY "Public Read Approved Tweets" ON tweet_posts FOR SELECT USING (status = 'approved');
CREATE POLICY "Public Read Leaderboards" ON leaderboard_ranks FOR SELECT USING (true);
