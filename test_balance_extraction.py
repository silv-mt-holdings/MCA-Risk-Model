"""
Test balance extraction from bank statement PDF
"""

from parsing.bank_statement_parser import BankStatementParser

parser = BankStatementParser()

# Read the PDF
pdf_path = r'C:\Users\gpark\OneDrive\Desktop\Bank 5209 - Oct 2025.pdf'
with open(pdf_path, 'rb') as f:
    content = f.read()

# Parse it
print('Parsing bank statement for balance extraction...\n')
result = parser.parse(content, 'Bank 5209 - Oct 2025.pdf')

print(f'{"="*70}')
print('BALANCE INFORMATION EXTRACTED')
print(f'{"="*70}\n')

# Check metadata for balance info
if 'balance_info' in result.metadata:
    balance_info = result.metadata['balance_info']
    print(f'Beginning Balance:      ${balance_info.get("beginning_balance", 0):>12,.2f}')
    print(f'Ending Balance:         ${balance_info.get("ending_balance", 0):>12,.2f}')
    print(f'Average Daily Balance:  ${balance_info.get("average_daily_balance", 0):>12,.2f}')
else:
    print('[!] No balance_info found in metadata')

print(f'\n{"="*70}')
print('SUMMARY VERIFICATION')
print(f'{"="*70}\n')

if result.summary:
    print(f'Summary ADB:            ${result.summary.average_daily_balance:>12,.2f}')
    print(f'Period Start:           {result.summary.period_start}')
    print(f'Period End:             {result.summary.period_end}')
    print(f'Total Deposits:         ${result.summary.total_deposits_90d:>12,.2f}')
    print(f'Total Withdrawals:      ${result.summary.total_withdrawals_90d:>12,.2f}')
    print(f'Net Cash Flow:          ${result.summary.net_cash_flow:>12,.2f}')

print(f'\n{"="*70}\n')
