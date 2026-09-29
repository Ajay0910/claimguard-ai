from typing import List, Dict, Any
from collections import deque

class RuleDependencyGraph:
    def __init__(self, rules: List[Dict[str, Any]], policy=None):
        self.rules = {r["name"]: r.copy() for r in rules}
        self.adj_list = {r["name"]: [] for r in rules}
        self.in_degree = {r["name"]: 0 for r in rules}
        self.conflicts = []
        
        if policy and hasattr(policy, "deduction_order_clause") and policy.deduction_order_clause:
            from app.rules import get_val
            clause = str(get_val(policy, "deduction_order_clause", "")).upper()
            
            # Simple keyword precedence logic
            order = []
            if "PROPORTIONATE" in clause: order.append((clause.find("PROPORTIONATE"), "Proportionate Deduction Rule"))
            if "DEDUCTIBLE" in clause: order.append((clause.find("DEDUCTIBLE"), "Deductible Rule"))
            if "CO-PAY" in clause or "COPAY" in clause: 
                idx = clause.find("CO-PAY") if "CO-PAY" in clause else clause.find("COPAY")
                order.append((idx, "Co-Pay Rule"))
            
            if len(order) > 1:
                # If clause uses "AFTER" or "THEN", the order in text is usually the logical order.
                # However, if it says "X applies after Y", Y comes before X in text. 
                # Let's assume standard wording is "Y then X" or just list them in sequence.
                # For safety, if we find "AFTER", we'll reverse the relationship if needed, 
                # but standard list sorting is usually best for "Deductible, then Copay".
                order.sort()
                
                # Clear static inter-dependencies for these 3 rules
                deduction_rules = ["Co-Pay Rule", "Deductible Rule", "Proportionate Deduction Rule"]
                for r in deduction_rules:
                    if r in self.rules:
                        self.rules[r]["depends_on"] = [d for d in self.rules[r].get("depends_on", []) if d not in deduction_rules]
                
                # Apply dynamic dependencies
                for i in range(len(order) - 1):
                    prev_rule = order[i][1]
                    next_rule = order[i+1][1]
                    if next_rule in self.rules and prev_rule in self.rules:
                        self.rules[next_rule].setdefault("depends_on", []).append(prev_rule)
                        
        self._build_graph()

    def _build_graph(self):
        # Identify rules with missing dependencies
        unresolvable = set()
        for r_name, r_meta in self.rules.items():
            for prereq in r_meta.get("depends_on", []):
                if prereq not in self.rules:
                    unresolvable.add(r_name)
                    # We log it but do NOT add it to self.conflicts if we want it to degrade gracefully.
                    # Or we can add it to a separate list. Let's just drop it silently or log to a different property.
        
        # Propagate unresolvability to dependents
        while unresolvable:
            bad_rule = unresolvable.pop()
            if bad_rule in self.rules:
                del self.rules[bad_rule]
                for other_name, other_meta in list(self.rules.items()):
                    if bad_rule in other_meta.get("depends_on", []):
                        unresolvable.add(other_name)
                        
        # Check mutual exclusivity
        for r_name, r_meta in list(self.rules.items()):
            for mutex in r_meta.get("mutually_exclusive_with", []):
                if mutex in self.rules:
                    self.conflicts.append(f"Mutually exclusive conflict: '{r_name}' and '{mutex}' are both applicable.")
                    
        # Rebuild structures for valid rules
        self.adj_list = {r: [] for r in self.rules}
        self.in_degree = {r: 0 for r in self.rules}
        
        # Build directed edges
        for r_name, r_meta in self.rules.items():
            for prereq in r_meta.get("depends_on", []):
                self.adj_list[prereq].append(r_name)
                self.in_degree[r_name] += 1

    def get_execution_order(self) -> List[Dict[str, Any]]:
        """
        Returns a topologically sorted list of rule metadata for the resolvable rules.
        Raises ValueError if cyclic dependencies or mutual exclusions are detected.
        """
        if self.conflicts:
            raise ValueError("Dependency Graph Conflicts:\n" + "\n".join(self.conflicts))
            
        queue = deque([node for node in self.in_degree if self.in_degree[node] == 0])
        ordered_names = []
        
        while queue:
            node = queue.popleft()
            ordered_names.append(node)
            
            for neighbor in self.adj_list[node]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(ordered_names) != len(self.rules):
            raise ValueError("Dependency Graph Conflict: Cyclic dependency detected between rules.")
            
        return [self.rules[name] for name in ordered_names]
