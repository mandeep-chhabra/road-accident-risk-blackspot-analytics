"""
Formatting Helpers for Numbers, Percentages, and Metric Cards.
"""

def format_int(value) -> str:
    """Format integer with thousands separator."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "N/A"


def format_pct(value, decimals: int = 2) -> str:
    """Format decimal or percentage as percentage string."""
    try:
        val = float(value)
        # If already on 0-100 scale
        if val > 1.0 or val < -1.0:
            return f"{val:.{decimals}f}%"
        return f"{val * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_float(value, decimals: int = 2) -> str:
    """Format floating point number with specified decimal precision."""
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"


def format_delta(value, decimals: int = 2, invert_color: bool = False) -> str:
    """Format delta string with sign."""
    try:
        val = float(value)
        sign = "+" if val > 0 else ""
        return f"{sign}{val:.{decimals}f}%"
    except (ValueError, TypeError):
        return ""

