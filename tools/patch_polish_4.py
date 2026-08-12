from pathlib import Path
p=Path('backend/_test_editorial_c_home.py')
s=p.read_text(encoding='utf-8')
s=s.replace('assert "day,day+6" in text\n','assert "todayDay,todayDay+6" in text\n')
p.write_text(s,encoding='utf-8')
