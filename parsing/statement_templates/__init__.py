"""
Statement Templates
===================
Bank-specific parsing templates.

Each template defines patterns and layouts for specific banks.
"""

# Template registry
TEMPLATES = {
    'generic': 'GenericTemplate',
    'chase': 'ChaseTemplate',
    'bofa': 'BankOfAmericaTemplate',
    'wells': 'WellsFargoTemplate',
}

__all__ = ['TEMPLATES']
