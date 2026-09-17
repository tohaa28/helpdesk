from pathlib import Path
import sys
p=Path(sys.argv[1])/'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java'
s=p.read_text()
old=r'replaceAll("\.pdf$",'
new=r'replaceAll("\\.pdf$",'
if old not in s:
    raise SystemExit('alpha4 escape target not found')
p.write_text(s.replace(old,new))
print('alpha4 regex escape fixed')
