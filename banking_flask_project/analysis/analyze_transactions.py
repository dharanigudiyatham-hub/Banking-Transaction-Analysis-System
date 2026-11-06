"""Optional analysis of the synthetic transaction CSV using Pandas, NumPy and Matplotlib."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

source = Path(__file__).with_name('sample_transactions.csv')
df = pd.read_csv(source, parse_dates=['date'])
print('Transaction count:', len(df))
print('Total amount:', round(float(np.sum(df['amount'])), 2))
print('\nTotals by type:')
print(df.groupby('type')['amount'].agg(['count','sum']).round(2))
df['review_flag'] = (df['amount'] >= 5000) | ((df['type'] == 'Withdrawal') & (df['amount'] >= 2000))
print('\nFlagged for manual review:')
print(df.loc[df.review_flag, ['reference','date','type','amount','description']].to_string(index=False))
monthly = df.assign(month=df['date'].dt.to_period('M').astype(str)).pivot_table(index='month', columns='type', values='amount', aggfunc='sum', fill_value=0)
monthly.plot(kind='bar', figsize=(9,5), title='Monthly Transaction Amounts')
plt.ylabel('Amount'); plt.tight_layout(); plt.savefig(Path(__file__).with_name('monthly_transactions.png'), dpi=140)
print('\nSaved monthly_transactions.png')
