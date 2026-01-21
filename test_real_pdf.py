"""
Test real PDF bank statement parsing
"""

from parsing.bank_statement_parser import BankStatementParser

parser = BankStatementParser()

# Read the PDF
pdf_path = r'C:\Users\gpark\OneDrive\Desktop\Bank 5209 - Oct 2025.pdf'
with open(pdf_path, 'rb') as f:
    content = f.read()

# Parse it
print('Parsing bank statement...')
result = parser.parse(content, 'Bank 5209 - Oct 2025.pdf')

# Display results
print(f'\n{"="*70}')
print('PARSING RESULTS')
print(f'{"="*70}\n')

print(f'Transactions Found: {len(result.transactions)}')
print(f'MCA Positions Detected: {len(result.mca_positions)}')
print(f'Errors: {len(result.errors)}')
print(f'Warnings: {len(result.warnings)}')

if result.errors:
    print(f'\nErrors:')
    for error in result.errors:
        print(f'  [X] {error}')

if result.warnings:
    print(f'\nWarnings:')
    for warning in result.warnings:
        print(f'  [!] {warning}')

if result.summary:
    print(f'\n{"="*70}')
    print('SUMMARY')
    print(f'{"="*70}\n')
    print(f'True Revenue (90d): ${result.summary.true_revenue_90d:,.2f}')
    print(f'Monthly True Revenue: ${result.summary.monthly_true_revenue:,.2f}')
    print(f'Average Daily Balance: ${result.summary.average_daily_balance:,.2f}')
    print(f'NSF Count: {result.summary.nsf_count}')
    print(f'Negative Days: {result.summary.negative_days}')

if result.mca_positions:
    print(f'\n{"="*70}')
    print('MCA POSITIONS')
    print(f'{"="*70}\n')
    for pos in result.mca_positions:
        print(f'  - {pos.mca_name}: ${pos.payment_amount:,.2f}/payment')

if result.transactions:
    print(f'\n{"="*70}')
    print('SAMPLE TRANSACTIONS (first 10)')
    print(f'{"="*70}\n')
    for txn in result.transactions[:10]:
        print(f'{txn.date} | {txn.description[:40]:40s} | ${txn.amount:>10,.2f} | {txn.revenue_type.value}')
