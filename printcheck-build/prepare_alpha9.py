#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, io, re, shutil, subprocess, sys, tarfile, zipfile

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
build = repo / '.printcheck-alpha9'
work = repo / '.printcheck-alpha9-work'
for p in (build, work):
    if p.exists(): shutil.rmtree(p)
    p.mkdir(parents=True)

pb = repo / 'printcheck-build'

def cat_b64(pattern: str) -> bytes:
    parts = sorted(pb.glob(pattern))
    if not parts:
        raise RuntimeError(f'No files for {pattern}')
    raw = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
    return base64.b64decode(raw)

def run(*args, cwd=None, check=True):
    print('+', ' '.join(map(str,args)), flush=True)
    return subprocess.run([str(x) for x in args], cwd=cwd, check=check)

def apply_patch(encoded_name: str, strip: int, strict=True):
    data = base64.b64decode((pb / encoded_name).read_bytes().replace(b'\n',b'').replace(b'\r',b''))
    patch_data = gzip.decompress(data)
    proc = subprocess.run(['patch','--batch',f'-p{strip}'], cwd=src, input=patch_data)
    if strict and proc.returncode != 0:
        raise RuntimeError(f'Patch failed: {encoded_name}')

source_zip = cat_b64('source.b64.part*')
with zipfile.ZipFile(io.BytesIO(source_zip)) as z:
    z.extractall(work)
src = work / 'printcheck_slim'
if not src.is_dir():
    raise RuntimeError('printcheck_slim not restored')

for script in ['patch_alpha2.py','patch_alpha3.py','patch_alpha4.py','fix_alpha4_escape.py','patch_alpha5.py']:
    run(sys.executable, pb / script, src)
with tarfile.open(fileobj=io.BytesIO(cat_b64('visual_overlay_3201.b64.part*')), mode='r:gz') as t:
    t.extractall(src)
run(sys.executable, pb / 'patch_alpha3202.py', src)

for pattern, strip in [('pc330a1.b64.part*',1),('pc330a2.small*',1)]:
    pdata = gzip.decompress(cat_b64(pattern))
    subprocess.run(['patch','--batch',f'-p{strip}'], cwd=src, input=pdata)

for pattern in ['pc340_overlay.b64.part*','pc340a2_overlay.b64.part*','pc340a3_overlay.b64.part*','pc340a4_overlay.b64.part*']:
    with tarfile.open(fileobj=io.BytesIO(cat_b64(pattern)), mode='r:gz') as t:
        t.extractall(src)

pdata = gzip.decompress(cat_b64('pc340a5.patch.b64.part*'))
if subprocess.run(['patch','--batch','-p1'], cwd=src, input=pdata).returncode != 0:
    raise RuntimeError('alpha5 patch failed')
for name in ['NativeAuth.java','LoginFormParser.java']:
    p = src / 'app/src/main/java/ru/printcheck/android' / name
    if p.exists(): p.unlink()

pdata = gzip.decompress(cat_b64('pc340a6v2.patch.b64.part*'))
subprocess.run(['patch','--batch','-p2'], cwd=src, input=pdata)
for p in src.rglob('*.rej'): p.unlink()
run(sys.executable, pb / 'fix_alpha6_helpers.py', src)

apply_patch('pc340a7.patch.gz.b64', 1, True)
apply_patch('pc340a8.patch.gz.b64', 1, True)
apply_patch('pc340a9.patch.gz.b64', 2, True)

gradle = src / 'app/build.gradle'
s = gradle.read_text(encoding='utf-8')
s = re.sub(r'\n\s*signingConfigs\s*\{\s*debug\s*\{.*?\n\s*\}\s*\n\s*\}\s*', '\n    ', s, flags=re.S)
gradle.write_text(s, encoding='utf-8')

if "versionName '3.4.0-alpha9'" not in s or 'versionCode 340009' not in s:
    raise RuntimeError('alpha9 version verification failed')
if not (src / 'app/src/main/java/ru/printcheck/android/OrderQueueParser.java').is_file():
    raise RuntimeError('OrderQueueParser missing')

shutil.copytree(src, build, dirs_exist_ok=True, ignore=shutil.ignore_patterns('build','*.keystore','*.rej','*.orig'))
print('Prepared', build)
