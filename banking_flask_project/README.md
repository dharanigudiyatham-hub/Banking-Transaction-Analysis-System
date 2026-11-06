# LedgerLens — Banking Transaction Analysis (Flask)

A Flask-based educational banking transaction analysis dashboard. It includes a dashboard, account summaries, transaction CRUD, cash-flow charts, search/type filtering, validation, and simple rule-based review flags. It uses synthetic data only and is not connected to any real bank.

## Run locally on Windows PowerShell

1. Install Python 3.10+ from https://www.python.org/downloads/ and select **Add Python to PATH**.
2. Extract the ZIP and open PowerShell in the `banking_flask_project` folder.
3. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again. Then open http://127.0.0.1:5000 . Local mode automatically creates a SQLite database and synthetic example data.

## Deploy to Vercel (Flask/Python)

- Import this folder/repository into Vercel. The root must contain `vercel.json`, `requirements.txt`, `app.py`, and `api/index.py`.
- The included `vercel.json` explicitly uses the Vercel Python runtime and routes requests to `api/index.py`.
- Configure a `DATABASE_URL` environment variable pointing to your Supabase Postgres connection string. Use the Supabase **pooler** connection string if recommended by your project/network; do not commit it to GitHub. Set `FLASK_SECRET_KEY` to a long random value.
- Run `supabase/schema.sql` in Supabase SQL Editor before using a Supabase database.
- Redeploy after setting environment variables.

**Important persistence note:** local SQLite is suitable for local demos. Vercel's filesystem is ephemeral, so use Supabase Postgres for persistent hosted data. This simple student demo uses server-side database credentials; never expose the database connection string in frontend code or commit it to source control. Add proper user authentication/authorization before using non-demo or personal data.

## Features

- Dashboard cards for deposits, withdrawals, transaction count, and simulated balance
- Monthly deposit/withdrawal chart and transaction mix chart
- Create/list/delete transactions with validation and balance check for withdrawals
- Create accounts and view calculated balances
- Search/filter transactions
- Review flags for withdrawals of at least ₹2,000 and any transaction of at least ₹5,000
- Optional Pandas/NumPy/Matplotlib analysis script in `analysis/`

## Optional data analysis

```powershell
pip install pandas numpy matplotlib
python analysis/analyze_transactions.py
```

All data and balances are fictional demonstration data.
