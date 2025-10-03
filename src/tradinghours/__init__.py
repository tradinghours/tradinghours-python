"""TradingHours Library"""

__version__ = "0.5.1"

from .config import main_config as _main_config

if _main_config.get("internal", "mode") == "package":
    from .currency import Currency
    from .market import Market