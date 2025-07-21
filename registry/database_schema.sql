-- 🦾 XMRT Agent Registry Database Schema
-- Extends existing Supabase setup with multi-persona management tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Personas Table
CREATE TABLE IF NOT EXISTS agent_personas (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('executive', 'technical', 'community', 'compliance', 'coordinator')),
    personality_traits JSONB DEFAULT '{}',
    communication_style VARCHAR(100) DEFAULT 'professional',
    expertise_areas TEXT[] DEFAULT '{}',
    authority_level INTEGER DEFAULT 5 CHECK (authority_level >= 1 AND authority_level <= 10),
    social_accounts JSONB DEFAULT '{}',
    contact_info JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'maintenance')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Task Assignments Table
CREATE TABLE IF NOT EXISTS agent_task_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent_personas(agent_id) ON DELETE CASCADE,
    task_type VARCHAR(100),
    task_description TEXT,
    task_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result_data JSONB DEFAULT '{}'
);

-- Agent Coordination Sessions Table
CREATE TABLE IF NOT EXISTS agent_coordination_sessions (
    coordination_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(100) NOT NULL,
    participants UUID[] NOT NULL,
    session_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    outcome JSONB DEFAULT '{}'
);

-- Agent Social Media Accounts Table
CREATE TABLE IF NOT EXISTS agent_social_accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent_personas(agent_id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(100),
    account_handle VARCHAR(100),
    credentials_encrypted TEXT, -- Encrypted API keys/tokens
    account_status VARCHAR(20) DEFAULT 'active',
    verification_status VARCHAR(20) DEFAULT 'unverified',
    follower_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Communication Channels Table
CREATE TABLE IF NOT EXISTS agent_communication_channels (
    channel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent_personas(agent_id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'whatsapp', 'telegram', 'discord', 'slack')),
    channel_identifier VARCHAR(255) NOT NULL, -- email address, phone number, etc.
    credentials_encrypted TEXT, -- Encrypted credentials
    channel_status VARCHAR(20) DEFAULT 'active',
    last_message_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Performance Metrics Table
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent_personas(agent_id) ON DELETE CASCADE,
    metric_date DATE DEFAULT CURRENT_DATE,
    tasks_assigned INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    response_time_avg INTERVAL,
    success_rate DECIMAL(5,2),
    user_satisfaction_score DECIMAL(3,2),
    social_engagement_score INTEGER DEFAULT 0,
    compliance_violations INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Decision History Table
CREATE TABLE IF NOT EXISTS agent_decision_history (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agent_personas(agent_id) ON DELETE CASCADE,
    decision_context JSONB NOT NULL,
    decision_made JSONB NOT NULL,
    reasoning TEXT,
    confidence_score DECIMAL(3,2),
    outcome_status VARCHAR(50),
    outcome_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_personas_role ON agent_personas(role);
CREATE INDEX IF NOT EXISTS idx_agent_personas_status ON agent_personas(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_id ON agent_task_assignments(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_task_assignments(status);
CREATE INDEX IF NOT EXISTS idx_agent_coordination_participants ON agent_coordination_sessions USING GIN(participants);
CREATE INDEX IF NOT EXISTS idx_agent_social_platform ON agent_social_accounts(platform);
CREATE INDEX IF NOT EXISTS idx_agent_communication_type ON agent_communication_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_date ON agent_performance_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_id ON agent_decision_history(agent_id);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_personas_updated_at 
    BEFORE UPDATE ON agent_personas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_social_accounts_updated_at 
    BEFORE UPDATE ON agent_social_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_communication_channels_updated_at 
    BEFORE UPDATE ON agent_communication_channels 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW agent_registry_overview AS
SELECT 
    ap.agent_id,
    ap.name,
    ap.role,
    ap.status,
    ap.authority_level,
    ap.created_at,
    COUNT(ata.assignment_id) as total_tasks,
    COUNT(CASE WHEN ata.status = 'completed' THEN 1 END) as completed_tasks,
    AVG(CASE WHEN apm.success_rate IS NOT NULL THEN apm.success_rate END) as avg_success_rate
FROM agent_personas ap
LEFT JOIN agent_task_assignments ata ON ap.agent_id = ata.agent_id
LEFT JOIN agent_performance_metrics apm ON ap.agent_id = apm.agent_id
GROUP BY ap.agent_id, ap.name, ap.role, ap.status, ap.authority_level, ap.created_at;

CREATE OR REPLACE VIEW active_agent_summary AS
SELECT 
    role,
    COUNT(*) as agent_count,
    AVG(authority_level) as avg_authority_level,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
FROM agent_personas
GROUP BY role;

-- Row Level Security (RLS) policies
ALTER TABLE agent_personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_task_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_coordination_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_communication_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_decision_history ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (customize based on your authentication setup)
CREATE POLICY "Enable all operations for service role" ON agent_personas
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_task_assignments
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_coordination_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_social_accounts
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_communication_channels
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_performance_metrics
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON agent_decision_history
    FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions to your application user
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Insert sample configuration data
INSERT INTO agent_personas (name, role, personality_traits, communication_style, expertise_areas, authority_level, social_accounts, contact_info) 
VALUES 
(
    'Alexandra Executive', 
    'executive',
    '{"leadership": 9, "decisiveness": 8, "strategic_thinking": 9, "communication": 8}',
    'authoritative_yet_approachable',
    ARRAY['governance', 'strategy', 'public_speaking', 'dao_operations'],
    9,
    '{"twitter": "@AlexXMRTExec", "discord": "Alexandra#EXEC"}',
    '{"email": "alexandra.exec@xmrt.dao"}'
),
(
    'Marcus Technical', 
    'technical',
    '{"analytical": 9, "precision": 9, "innovation": 8, "patience": 7}',
    'technical_but_clear',
    ARRAY['blockchain', 'smart_contracts', 'mining', 'security'],
    8,
    '{"twitter": "@MarcusXMRTTech", "github": "MarcusXMRTDev"}',
    '{"email": "marcus.tech@xmrt.dao"}'
),
(
    'Sofia Community', 
    'community',
    '{"empathy": 9, "enthusiasm": 8, "patience": 9, "creativity": 8}',
    'warm_and_engaging',
    ARRAY['community_building', 'social_media', 'events', 'education'],
    7,
    '{"twitter": "@SofiaXMRTComm", "discord": "Sofia#COMM"}',
    '{"email": "sofia.community@xmrt.dao"}'
),
(
    'David Compliance', 
    'compliance',
    '{"attention_to_detail": 9, "cautiousness": 8, "reliability": 9, "thoroughness": 9}',
    'precise_and_formal',
    ARRAY['regulatory_compliance', 'legal_analysis', 'risk_assessment'],
    8,
    '{"linkedin": "DavidXMRTCompliance"}',
    '{"email": "david.compliance@xmrt.dao"}'
)
ON CONFLICT (agent_id) DO NOTHING;

-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW agent_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM agent_personas WHERE status = 'active') as active_agents,
    (SELECT COUNT(*) FROM agent_task_assignments WHERE status = 'in_progress') as active_tasks,
    (SELECT COUNT(*) FROM agent_coordination_sessions WHERE status = 'active') as active_sessions,
    (SELECT COUNT(*) FROM agent_social_accounts WHERE account_status = 'active') as active_social_accounts,
    (SELECT AVG(success_rate) FROM agent_performance_metrics WHERE metric_date >= CURRENT_DATE - INTERVAL '7 days') as avg_success_rate_7d;

-- Refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_agent_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW agent_dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- Schedule regular refresh (adjust according to your needs)
-- This would typically be set up as a cron job or scheduled task
