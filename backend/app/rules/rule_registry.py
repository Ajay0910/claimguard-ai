from typing import Callable, Dict, Any, List

_RULE_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register_rule(
    name: str, 
    description: str, 
    tier: int, 
    regulatory_citation: str = None,
    depends_on: List[str] = None,
    mutually_exclusive_with: List[str] = None,
    modifies_categories: List[str] = None,
    supported_policy_versions: List[str] = None
):
    def decorator(func: Callable):
        _RULE_REGISTRY[name] = {
            "name": name,
            "description": description,
            "tier": tier,
            "regulatory_citation": regulatory_citation,
            "depends_on": depends_on or [],
            "mutually_exclusive_with": mutually_exclusive_with or [],
            "modifies_categories": modifies_categories or [],
            "supported_policy_versions": supported_policy_versions or [],
            "function": func
        }
        return func
    return decorator

def get_all_rules() -> List[Dict[str, Any]]:
    return sorted(_RULE_REGISTRY.values(), key=lambda x: x["tier"])

def get_rule(name: str) -> Callable:
    return _RULE_REGISTRY.get(name, {}).get("function")

def get_rule_metadata(name: str) -> Dict[str, Any]:
    return _RULE_REGISTRY.get(name, {})
