"""
Bank-Specific Statement Templates

Provides parsing templates for different banks to handle format variations.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BankTemplate:
    """
    Bank-specific parsing template.

    Attributes:
        bank_name: Name of the bank
        detection_patterns: Regex patterns to detect this bank
        transaction_pattern: Regex for parsing transactions
        date_formats: List of datetime format strings
        balance_patterns: Dict of balance field patterns
        header_skip_lines: Number of header lines to skip
        footer_markers: Patterns indicating end of transactions
    """
    bank_name: str
    detection_patterns: List[str]
    transaction_pattern: str
    date_formats: List[str]
    balance_patterns: Dict[str, str]
    header_skip_lines: int = 0
    footer_markers: List[str] = None

    def __post_init__(self):
        if self.footer_markers is None:
            self.footer_markers = []


# =============================================================================
# BANK OF AMERICA TEMPLATE
# =============================================================================

BANK_OF_AMERICA = BankTemplate(
    bank_name="Bank of America",
    detection_patterns=[
        r'Bank of America',
        r'bankofamerica\.com',
        r'Business Advantage',
        r'BKOFAMERICA'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[^\$]*\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[^\$]*\$([\d,]+\.?\d*)',
        'average_daily': r'Average (?:ledger|daily) balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'Page \d+ of \d+',
        r'See the big picture',
        r'Please see the Important Messages',
    ]
)


# =============================================================================
# CHASE BANK TEMPLATE
# =============================================================================

CHASE = BankTemplate(
    bank_name="Chase",
    detection_patterns=[
        r'Chase',
        r'chase\.com',
        r'JPMorgan Chase',
        r'JP Morgan'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\$?[\d,]+\.?\d{2})',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
        '%m/%d',  # Chase often uses MM/DD without year
    ],
    balance_patterns={
        'beginning': r'Beginning balance[:\s]+\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[:\s]+\$([\d,]+\.?\d*)',
        'average_daily': r'Average (?:collected|ledger) balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'Questions\?',
        r'Member FDIC',
    ]
)


# =============================================================================
# WELLS FARGO TEMPLATE
# =============================================================================

WELLS_FARGO = BankTemplate(
    bank_name="Wells Fargo",
    detection_patterns=[
        r'Wells Fargo',
        r'wellsfargo\.com',
        r'WELLS FARGO BANK'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\$?[\d,]+\.?\d{2})',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
        '%m/%d',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[:\s]+\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[:\s]+\$([\d,]+\.?\d*)',
        'average_daily': r'Average (?:ledger|available) balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'wellsfargo\.com',
        r'Page \d+ of \d+',
    ]
)


# =============================================================================
# US BANK TEMPLATE
# =============================================================================

US_BANK = BankTemplate(
    bank_name="US Bank",
    detection_patterns=[
        r'U\.?S\.? Bank',
        r'usbank\.com',
        r'US BANK NATIONAL'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([-]?\$?[\d,]+\.?\d{2})',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[:\s]+\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[:\s]+\$([\d,]+\.?\d*)',
        'average_daily': r'Average ledger balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'Member FDIC',
    ]
)


# =============================================================================
# PNC BANK TEMPLATE
# =============================================================================

PNC = BankTemplate(
    bank_name="PNC",
    detection_patterns=[
        r'PNC Bank',
        r'pnc\.com',
        r'PNC BANK'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\$?[\d,]+\.?\d{2})',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
        '%m/%d',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[:\s]+\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[:\s]+\$([\d,]+\.?\d*)',
        'average_daily': r'Average (?:ledger|collected) balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'Member FDIC',
        r'pnc\.com',
    ]
)


# =============================================================================
# CITIBANK TEMPLATE
# =============================================================================

CITIBANK = BankTemplate(
    bank_name="Citibank",
    detection_patterns=[
        r'Citibank',
        r'citi\.com',
        r'CITIBANK'
    ],
    transaction_pattern=r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([-]?\$?[\d,]+\.?\d{2})',
    date_formats=[
        '%m/%d/%Y',
        '%m/%d/%y',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[:\s]+\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[:\s]+\$([\d,]+\.?\d*)',
        'average_daily': r'Average ledger balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[
        r'Member FDIC',
        r'citi\.com',
    ]
)


# =============================================================================
# GENERIC TEMPLATE (FALLBACK)
# =============================================================================

GENERIC = BankTemplate(
    bank_name="Generic",
    detection_patterns=[],  # No detection, used as fallback
    transaction_pattern=r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
    date_formats=[
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%m/%d/%y',
        '%m-%d-%y',
        '%Y-%m-%d',
        '%m/%d',
        '%m-%d',
    ],
    balance_patterns={
        'beginning': r'Beginning balance[^\$]*\$([\d,]+\.?\d*)',
        'ending': r'Ending balance[^\$]*\$([\d,]+\.?\d*)',
        'average_daily': r'Average (?:ledger|daily|collected|available) balance[:\s]+\$([\d,]+\.?\d*)',
    },
    footer_markers=[]
)


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

ALL_TEMPLATES = [
    BANK_OF_AMERICA,
    CHASE,
    WELLS_FARGO,
    US_BANK,
    PNC,
    CITIBANK,
]


def detect_bank(text: str) -> BankTemplate:
    """
    Auto-detect bank from statement text.

    Args:
        text: Statement text (usually first 2000 chars)

    Returns:
        BankTemplate for detected bank, or GENERIC if unknown
    """
    text_upper = text.upper()

    for template in ALL_TEMPLATES:
        for pattern in template.detection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return template

    # Fallback to generic
    return GENERIC


def get_template(bank_name: str) -> Optional[BankTemplate]:
    """
    Get template by bank name.

    Args:
        bank_name: Bank name (case-insensitive)

    Returns:
        BankTemplate if found, None otherwise
    """
    bank_upper = bank_name.upper()

    for template in ALL_TEMPLATES:
        if template.bank_name.upper() == bank_upper:
            return template

    return None


def list_supported_banks() -> List[str]:
    """
    Get list of supported bank names.

    Returns:
        List of bank names
    """
    return [t.bank_name for t in ALL_TEMPLATES]
