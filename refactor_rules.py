import os
import re

def refactor_rules():
    rules_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend\app\rules"
    
    # 1. We will create a helper in __init__.py
    init_path = os.path.join(rules_dir, "__init__.py")
    with open(init_path, 'r') as f:
        init_content = f.read()
    if 'def get_val' not in init_content:
        init_content += """\n
def get_val(obj, attr, default=None):
    val = getattr(obj, attr, default)
    if hasattr(val, 'value'):
        return val.value
    return val
"""
        with open(init_path, 'w') as f:
            f.write(init_content)
    
    # 2. Iterate over all files and replace getattr with get_val, and inject import
    for filename in os.listdir(rules_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(rules_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Inject import if needed
            if 'getattr' in content and 'from . import get_val' not in content:
                content = "from . import get_val\n" + content
                
            # Replace getattr(obj, 'attr', default) with get_val(obj, 'attr', default)
            # Regex handles getattr(x, 'y') and getattr(x, 'y', z)
            content = re.sub(r"getattr\(([^,]+),\s*([^,)]+)(?:,\s*([^)]+))?\)", 
                             lambda m: f"get_val({m.group(1)}, {m.group(2)}" + (f", {m.group(3)})" if m.group(3) else ")"), 
                             content)
                             
            with open(filepath, 'w') as f:
                f.write(content)

if __name__ == "__main__":
    refactor_rules()
