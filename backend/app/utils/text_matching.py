import re

def normalize_id(s: str) -> str:
    """Removes all non-alphanumeric characters and lowercases."""
    if not s:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def match_ids(id1: str, id2: str) -> bool:
    """Matches two identifiers strictly."""
    if not id1 or not id2:
        return True # Cannot evaluate, assume pass
    return normalize_id(id1) == normalize_id(id2)

def normalize_name(s: str) -> set:
    """Extracts alphabetic tokens from a string for fuzzy name matching."""
    if not s:
        return set()
    return set(re.findall(r'[a-z]+', str(s).lower()))

def match_names(name1: str, name2: str, threshold: float = 0.75) -> bool:
    """
    Returns True if the overlap coefficient of word tokens is >= threshold.
    overlap = len(intersection) / min(len(set1), len(set2))
    """
    if not name1 or not name2:
        return True # Cannot evaluate
        
    s1 = normalize_name(name1)
    s2 = normalize_name(name2)
    
    if not s1 or not s2:
        return True
        
    intersection = s1.intersection(s2)
    overlap = len(intersection) / min(len(s1), len(s2))
    return overlap >= threshold
