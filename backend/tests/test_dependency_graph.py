import pytest
from app.engine.dependency_graph import RuleDependencyGraph

def test_valid_topological_sort():
    rules = [
        {"name": "RuleA", "depends_on": []},
        {"name": "RuleB", "depends_on": ["RuleA"]},
        {"name": "RuleC", "depends_on": ["RuleB"]},
    ]
    graph = RuleDependencyGraph(rules)
    order = graph.get_execution_order()
    names = [r["name"] for r in order]
    assert names == ["RuleA", "RuleB", "RuleC"]

def test_missing_dependency():
    rules = [
        {"name": "RuleA", "depends_on": ["MissingRule"]},
        {"name": "RuleB", "depends_on": []},
    ]
    graph = RuleDependencyGraph(rules)
    order = graph.get_execution_order()
    names = [r["name"] for r in order]
    assert names == ["RuleB"]
    assert len(graph.conflicts) == 0

def test_circular_dependency():
    rules = [
        {"name": "RuleA", "depends_on": ["RuleB"]},
        {"name": "RuleB", "depends_on": ["RuleA"]},
    ]
    graph = RuleDependencyGraph(rules)
    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        graph.get_execution_order()

def test_mutual_exclusivity():
    rules = [
        {"name": "RuleA", "mutually_exclusive_with": ["RuleB"]},
        {"name": "RuleB", "mutually_exclusive_with": ["RuleA"]},
    ]
    graph = RuleDependencyGraph(rules)
    with pytest.raises(ValueError, match="Mutually exclusive conflict"):
        graph.get_execution_order()
