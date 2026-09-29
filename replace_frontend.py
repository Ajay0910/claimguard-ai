import os

d = r'C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\frontend'
for root, dirs, files in os.walk(d):
    if 'node_modules' in dirs:
        dirs.remove('node_modules')
    if '.git' in dirs:
        dirs.remove('.git')
        
    for f in files:
        if f.endswith(('.js', '.jsx', '.mjs', '.md', '.json', '.html')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    content = file.read()
                except UnicodeDecodeError:
                    continue
            
            new_content = content.replace('Violation', 'Conflict').replace('violation', 'conflict').replace('VIOLATION', 'CONFLICT')
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
