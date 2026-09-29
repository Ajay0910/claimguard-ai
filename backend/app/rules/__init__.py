# Init file for rules
def get_val(obj, attr, default=None):
    val = getattr(obj, attr, default)
    if val is None:
        val = default
    if hasattr(val, 'value'):
        return val.value
    return val

from .engine import RuleEngine
from .appeal_evaluator import AppealEvaluator
from .rule_registry import register_rule, get_all_rules, get_rule
from ..schemas.appeal_evaluation import AppealEvaluationResult

__all__ = [
    "RuleEngine",
    "AppealEvaluator",
    "AppealEvaluationResult",
    "register_rule",
    "get_all_rules",
    "get_rule",
    "get_val"
]
