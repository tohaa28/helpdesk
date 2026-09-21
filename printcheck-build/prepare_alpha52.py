#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
subprocess.run([sys.executable,str(repo/'printcheck-build/prepare_alpha51.py'),str(repo)],check=True)
src=repo/'.printcheck-alpha52'
if src.exists(): shutil.rmtree(src)
shutil.copytree(repo/'.printcheck-alpha51',src)
patch=gzip.decompress(base64.b64decode((repo/'printcheck-build/alpha52_patch.b64').read_bytes(),validate=True))
assert hashlib.sha256(patch).hexdigest()=='afa830a44c30cadfcd57f140bf0230b7e2f7a922d402b38dedf70265cc8f164a'
p=repo/'.alpha52.patch';p.write_bytes(patch)
subprocess.run(['patch','-p1','--batch','--forward','-i',str(p)],cwd=src,check=True)
p.unlink()
assert not list(src.rglob('*.rej'))
subprocess.run([sys.executable,str(src/'tests/audit_alpha52.py')],check=True)
print('Prepared PrintCheck alpha52 audit fixes')
