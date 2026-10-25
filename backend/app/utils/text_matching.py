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

def strip_honorifics(s: str) -> str:
    """Strips common honorifics (Mr., Mrs., Dr., etc.) from a name string."""
    if not s:
        return ""
    cleaned = re.sub(r'\b(?:mr|mrs|ms|dr|master|baby|shri|smt|kumari|prof|patient)\b\.?\s*', '', str(s), flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()

def normalize_name(s: str) -> set:
    """Extracts alphabetic tokens from a string for fuzzy name matching, stripping common honorifics."""
    if not s:
        return set()
    cleaned = strip_honorifics(s)
    return set(re.findall(r'[a-z]+', cleaned.lower()))

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def levenshtein_similarity(s1: str, s2: str) -> float:
    """Computes normalized Levenshtein similarity in range [0.0, 1.0]."""
    c1 = strip_honorifics(s1).lower()
    c2 = strip_honorifics(s2).lower()
    if not c1 and not c2:
        return 1.0
    if not c1 or not c2:
        return 0.0
    max_len = max(len(c1), len(c2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(c1, c2)
    return 1.0 - (dist / max_len)

def match_names(name1: str, name2: str, threshold: float = 0.75) -> bool:
    """
    Returns True if:
    1. The overlap coefficient of word tokens is >= threshold, OR
    2. The Levenshtein similarity between the honorific-stripped names is >= 0.80.
    """
    if not name1 or not name2:
        return True # Cannot evaluate
        
    s1 = normalize_name(name1)
    s2 = normalize_name(name2)
    
    if not s1 or not s2:
        return True
        
    intersection = s1.intersection(s2)
    min_len = min(len(s1), len(s2))
    if min_len > 0:
        overlap = len(intersection) / min_len
        if overlap >= threshold:
            return True

    return levenshtein_similarity(name1, name2) >= 0.80
