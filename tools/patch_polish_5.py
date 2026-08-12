from pathlib import Path

p=Path('decision.md')
s=p.read_text(encoding='utf-8')
p.write_text(s.rstrip()+'\n',encoding='utf-8')
