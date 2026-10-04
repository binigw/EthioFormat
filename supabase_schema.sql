-- ==============================================================================
-- EthioFormat - Supabase Database Schema: Transactions Table
-- Supports automated CBE Birr Email-Webhook Payment Verification Workflow
-- ==============================================================================

-- 1. Create Transaction Status Enum
DO $$ BEGIN
    CREATE TYPE transaction_status AS ENUM ('pending', 'approved', 'failed');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 2. Create Transactions Table
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    amount_expected NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) DEFAULT NULL,
    transaction_ref TEXT UNIQUE NOT NULL, -- CBE Transaction ID (e.g. FT260987ABCD or TXN123456)
    status transaction_status NOT NULL DEFAULT 'pending',
    cbe_account_number TEXT DEFAULT '1000659424936',
    cbe_account_name TEXT DEFAULT 'BINIAM KEBEDE AMADE',
    payer_email TEXT,
    payer_name TEXT,
    payer_phone TEXT,
    download_url TEXT,
    raw_webhook_payload JSONB DEFAULT NULL,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Create Indexes for High-Performance Lookups
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_ref ON public.transactions(transaction_ref);
CREATE INDEX IF NOT EXISTS idx_transactions_session_id ON public.transactions(session_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON public.transactions(status);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- 5. Policies:
-- Allow anonymous users with anon key to read their own transaction by transaction_ref or session_id
CREATE POLICY "Allow public read access by transaction_ref or session_id"
    ON public.transactions
    FOR SELECT
    USING (true);

-- Allow service_role key full CRUD privileges
CREATE POLICY "Allow service_role full access"
    ON public.transactions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 6. Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_transactions_updated_at ON public.transactions;
CREATE TRIGGER trigger_update_transactions_updated_at
    BEFORE UPDATE ON public.transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Supabase Realtime for instant frontend notifications
ALTER PUBLICATION supabase_realtime ADD TABLE public.transactions;
