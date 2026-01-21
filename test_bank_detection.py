"""
Test bank detection and multi-bank parsing support
"""

from parsing.bank_statement_parser import BankStatementParser
from parsing.bank_templates import list_supported_banks

parser = BankStatementParser()

# Read the PDF
pdf_path = r'C:\Users\gpark\OneDrive\Desktop\Bank 5209 - Oct 2025.pdf'
with open(pdf_path, 'rb') as f:
    content = f.read()

# Parse it
print('Testing bank detection...\n')
result = parser.parse(content, 'Bank 5209 - Oct 2025.pdf')

print(f'{"="*70}')
print('BANK DETECTION RESULTS')
print(f'{"="*70}\n')

# Check detected bank
detected_bank = result.metadata.get('detected_bank', 'Unknown')
print(f'Detected Bank: {detected_bank}')
print(f'Parsing Success: {"YES" if result.success else "NO"}')
print(f'Transactions Extracted: {len(result.transactions)}')
print(f'Balance Extraction: {"YES" if result.summary.average_daily_balance > 0 else "NO"}')

print(f'\n{"="*70}')
print('SUPPORTED BANKS')
print(f'{"="*70}\n')

supported = list_supported_banks()
print(f'Total Banks Supported: {len(supported)}\n')

for i, bank in enumerate(supported, 1):
    marker = '*' if bank == detected_bank else ' '
    print(f'  {marker} {i}. {bank}')

print(f'\n{"="*70}')
print('TEMPLATE FEATURES USED')
print(f'{"="*70}\n')

if parser.detected_bank:
    template = parser.detected_bank
    print(f'Bank Name: {template.bank_name}')
    print(f'Transaction Pattern: {template.transaction_pattern[:60]}...')
    print(f'Date Formats: {", ".join(template.date_formats)}')
    print(f'Balance Patterns:')
    for key, pattern in template.balance_patterns.items():
        print(f'  - {key}: {pattern[:50]}...')

print(f'\n{"="*70}\n')
