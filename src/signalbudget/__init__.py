"""SignalBudget v1 package."""

__version__ = "1.0.0"

from signalbudget.configurations import enumerate_source_configurations
from signalbudget.contracts import validate_detfuzz_result
from signalbudget.costing import estimate_monthly_source_costs
from signalbudget.loaders import load_catalog_bundle
from signalbudget.pareto import analyze_pareto
from signalbudget.tradeoffs import build_tradeoff_report

__all__ = [
    "__version__",
    "analyze_pareto",
    "build_tradeoff_report",
    "enumerate_source_configurations",
    "estimate_monthly_source_costs",
    "load_catalog_bundle",
    "validate_detfuzz_result",
]
