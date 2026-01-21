"""
Test that Zelle/Venmo flags are being added correctly
"""

from parsing.bank_statement_parser import BankStatementParser

parser = BankStatementParser()

# Read the PDF
pdf_path = r'C:\Users\gpark\OneDrive\Desktop\Bank 5209 - Oct 2025.pdf'
with open(pdf_path, 'rb') as f:
    content = f.read()

# Parse it
print('Parsing bank statement...\n')
result = parser.parse(content, 'Bank 5209 - Oct 2025.pdf')

# Find Zelle transactions and check their flags
zelle_count = 0
flagged_count = 0

print(f'{"="*70}')
print('ZELLE/VENMO TRANSACTIONS WITH FLAGS')
print(f'{"="*70}\n')

for txn in result.transactions:
    if 'ZELLE' in txn.description.upper() or 'VENMO' in txn.description.upper():
        zelle_count += 1
        if 'P2P_REVIEW_REQUIRED' in txn.flags:
            flagged_count += 1
            flag_marker = '[FLAGGED]'
        else:
            flag_marker = '[NO FLAG]'

        print(f'{txn.date} | {txn.description[:50]:50s} | ${txn.amount:>10,.2f}')
        print(f'  Revenue Type: {txn.revenue_type.value}')
        print(f'  Flags: {txn.flags if txn.flags else "None"} {flag_marker}')
        print()

print(f'{"="*70}')
print(f'Total Zelle/Venmo transactions: {zelle_count}')
print(f'Flagged for review: {flagged_count}')
print(f'Success Rate: {flagged_count}/{zelle_count} = {100*flagged_count/zelle_count if zelle_count > 0 else 0:.0f}%')
print(f'{"="*70}\n')
