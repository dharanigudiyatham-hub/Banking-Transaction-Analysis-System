-- Run this in the Supabase SQL Editor if you use Supabase Postgres.
-- Set DATABASE_URL in Vercel to your Supabase Postgres connection string (server-side only).
create table if not exists customers (
  id bigserial primary key,
  name text not null,
  email text not null unique,
  created_at timestamptz not null default now()
);
create table if not exists accounts (
  id bigserial primary key,
  account_number text not null unique,
  name text not null,
  account_type text not null check (account_type in ('Savings','Checking','Fixed Deposit')),
  opening_balance numeric(14,2) not null default 0 check (opening_balance >= 0),
  customer_id bigint not null references customers(id) on delete cascade,
  created_at timestamptz not null default now()
);
create table if not exists transactions (
  id bigserial primary key,
  reference text not null unique,
  account_id bigint not null references accounts(id) on delete cascade,
  txn_type text not null check (txn_type in ('Deposit','Withdrawal','Transfer')),
  amount numeric(14,2) not null check (amount > 0),
  description text not null,
  txn_date date not null default current_date,
  created_at timestamptz not null default now()
);
create index if not exists idx_transactions_date on transactions(txn_date desc);
create index if not exists idx_transactions_account on transactions(account_id);
