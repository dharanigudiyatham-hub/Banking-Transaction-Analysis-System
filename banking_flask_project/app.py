import os
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-for-deployment')

# Local development uses SQLite. Set DATABASE_URL to a Supabase Postgres connection string for deployment.
database_url = os.getenv('DATABASE_URL', 'sqlite:///banking_analysis.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
if database_url.startswith('postgresql://') and 'sslmode=' not in database_url:
    database_url += ('&' if '?' in database_url else '?') + 'sslmode=require'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default='Demo Customer')
    email = db.Column(db.String(180), nullable=False, unique=True, default='demo@example.com')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accounts = db.relationship('Account', backref='customer', cascade='all, delete-orphan')

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(40), nullable=False, default='Savings')
    opening_balance = db.Column(db.Float, nullable=False, default=0)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='account', cascade='all, delete-orphan')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(24), unique=True, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    txn_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(240), nullable=False, default='General transaction')
    txn_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_flagged(self):
        return self.txn_type == 'Withdrawal' and self.amount >= 2000 or self.amount >= 5000

    @property
    def flag_reason(self):
        if self.amount >= 5000: return 'High-value transaction (≥ ₹5,000)'
        if self.txn_type == 'Withdrawal' and self.amount >= 2000: return 'Large withdrawal (≥ ₹2,000)'
        return ''

with app.app_context():
    db.create_all()
    if Customer.query.count() == 0:
        c = Customer(name='Demo Customer', email='demo@example.com')
        db.session.add(c); db.session.flush()
        a1 = Account(account_number='**** 1234', name='Primary Savings', account_type='Savings', opening_balance=3420, customer_id=c.id)
        a2 = Account(account_number='**** 5678', name='Everyday Checking', account_type='Checking', opening_balance=1250, customer_id=c.id)
        a3 = Account(account_number='**** 9012', name='Fixed Deposit', account_type='Fixed Deposit', opening_balance=750, customer_id=c.id)
        db.session.add_all([a1, a2, a3]); db.session.flush()
        samples = [
            (a1,'Deposit',1200,'Salary credit',date(2026,8,24)), (a2,'Withdrawal',450,'ATM withdrawal',date(2026,8,23)),
            (a1,'Transfer',300,'Transfer to checking',date(2026,8,22)), (a3,'Deposit',2000,'FD renewal',date(2026,8,21)),
            (a2,'Withdrawal',120,'Online purchase',date(2026,8,20)), (a1,'Deposit',800,'Freelance payment',date(2026,8,19)),
            (a2,'Withdrawal',250,'Grocery store',date(2026,8,18)), (a1,'Withdrawal',2500,'Large cash withdrawal',date(2026,8,17)),
            (a2,'Transfer',3500,'Multiple transfer review',date(2026,8,16))]
        for i,(acct,typ,amt,desc,dt) in enumerate(samples,1):
            db.session.add(Transaction(reference=f'TXN{i:04d}',account_id=acct.id,txn_type=typ,amount=amt,description=desc,txn_date=dt))
        db.session.commit()

def account_balance(account):
    total = account.opening_balance
    for t in account.transactions:
        if t.txn_type == 'Deposit': total += t.amount
        elif t.txn_type == 'Withdrawal': total -= t.amount
    return total

def money(n): return float(n or 0)

@app.route('/')
def dashboard():
    accounts = Account.query.order_by(Account.id).all()
    transactions = Transaction.query.order_by(Transaction.txn_date.desc(), Transaction.id.desc()).all()
    deposits = sum(t.amount for t in transactions if t.txn_type == 'Deposit')
    withdrawals = sum(t.amount for t in transactions if t.txn_type == 'Withdrawal')
    balance = sum(account_balance(a) for a in accounts)
    flagged = [t for t in transactions if t.is_flagged]
    months = {}
    for t in transactions:
        key=t.txn_date.strftime('%b %Y')
        months.setdefault(key, {'deposits':0,'withdrawals':0})
        if t.txn_type == 'Deposit': months[key]['deposits'] += t.amount
        if t.txn_type == 'Withdrawal': months[key]['withdrawals'] += t.amount
    month_items=sorted(months.items(), key=lambda x: datetime.strptime(x[0],'%b %Y'))[-6:]
    type_totals={k:sum(t.amount for t in transactions if t.txn_type==k) for k in ['Deposit','Withdrawal','Transfer']}
    return render_template('index.html', accounts=accounts, transactions=transactions[:10], all_transactions=transactions,
        deposits=deposits, withdrawals=withdrawals, balance=balance, flagged=flagged,
        month_labels=[x[0] for x in month_items], month_deposits=[x[1]['deposits'] for x in month_items],
        month_withdrawals=[x[1]['withdrawals'] for x in month_items], type_labels=list(type_totals), type_values=list(type_totals.values()),
        account_balance=account_balance)

@app.route('/transactions')
def transactions_page():
    q=request.args.get('q','').strip(); kind=request.args.get('type','')
    query=Transaction.query.join(Account)
    if q: query=query.filter(db.or_(Transaction.reference.ilike(f'%{q}%'),Transaction.description.ilike(f'%{q}%'),Account.name.ilike(f'%{q}%')))
    if kind in ['Deposit','Withdrawal','Transfer']: query=query.filter(Transaction.txn_type==kind)
    transactions=query.order_by(Transaction.txn_date.desc(),Transaction.id.desc()).all()
    return render_template('transactions.html', transactions=transactions, accounts=Account.query.all(), q=q, kind=kind)

@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    try:
        account_id=int(request.form.get('account_id','0')); amount=float(request.form.get('amount','0'))
        kind=request.form.get('txn_type',''); desc=request.form.get('description','').strip()
        txn_date=datetime.strptime(request.form.get('txn_date',''),'%Y-%m-%d').date()
        if amount <= 0 or kind not in ['Deposit','Withdrawal','Transfer'] or not desc: raise ValueError('Enter a valid positive amount, type, description and date.')
        account=Account.query.get_or_404(account_id)
        if kind=='Withdrawal' and amount>account_balance(account): raise ValueError('Withdrawal exceeds the available simulated balance.')
        ref='TXN'+datetime.utcnow().strftime('%y%m%d%H%M%S%f')[-12:]
        db.session.add(Transaction(reference=ref,account_id=account.id,txn_type=kind,amount=amount,description=desc,txn_date=txn_date))
        db.session.commit(); flash('Transaction added successfully.','success')
    except (ValueError, InvalidOperation) as e:
        flash(str(e) or 'Please check the transaction details.','error')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/transactions/<int:txn_id>/delete', methods=['POST'])
def delete_transaction(txn_id):
    t=Transaction.query.get_or_404(txn_id); db.session.delete(t); db.session.commit(); flash('Transaction deleted.','success')
    return redirect(request.referrer or url_for('transactions_page'))

@app.route('/accounts')
def accounts_page():
    accounts=Account.query.order_by(Account.id).all()
    return render_template('accounts.html', accounts=accounts, account_balance=account_balance)

@app.route('/accounts/add', methods=['POST'])
def add_account():
    try:
        name=request.form.get('name','').strip(); kind=request.form.get('account_type','Savings'); opening=float(request.form.get('opening_balance','0'))
        if not name or opening < 0 or kind not in ['Savings','Checking','Fixed Deposit']: raise ValueError('Enter valid account details.')
        customer=Customer.query.first()
        account=Account(account_number='**** '+datetime.utcnow().strftime('%H%M%S'),name=name,account_type=kind,opening_balance=opening,customer_id=customer.id)
        db.session.add(account); db.session.commit(); flash('Account created.','success')
    except ValueError as e: flash(str(e),'error')
    return redirect(url_for('accounts_page'))

@app.route('/analytics')
def analytics_page():
    return redirect(url_for('dashboard')+'#analytics')

@app.route('/health')
def health(): return jsonify(status='ok', framework='Flask')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
