from pathlib import Path
import ast,json,subprocess,re
root=Path(__file__).resolve().parents[1]
files=[p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','__pycache__','.venv','staging','node_modules'))]
for p in files:
    if p.suffix=='.py': ast.parse(p.read_text(),filename=str(p))
    elif p.suffix=='.json': json.loads(p.read_text())
    elif p.suffix=='.sh': subprocess.run(['bash','-n',str(p)],check=True)
    elif p.suffix=='.js': subprocess.run(['node','--check',str(p)],check=True)
print(f'Source checks passed ({len(files)} files; only present sources).')
