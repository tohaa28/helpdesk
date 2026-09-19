#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

# Alpha19 is deliberately reproducible from the exact canonical alpha18 generator.
subprocess.run([sys.executable, str(pb / "prepare_alpha18.py"), str(repo)], check=True)

src18 = repo / ".printcheck-alpha18"
src19 = repo / ".printcheck-alpha19"
if src19.exists():
    shutil.rmtree(src19)
shutil.copytree(src18, src19)

part_names = [f"pc340a19.b64.part{i:02d}" for i in range(5)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha19 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 28556
expected_encoded_sha256 = "f97340de8e07b76c68965b011b45b42fedfb26698d046c49792eaa98c1305439"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha19 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha19 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "cfd6f131a1a91a081c614209313f52d09b41ca8757a838d14467241fd76e9b34"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha19 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha19.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
        cwd=src19,
        check=True,
    )
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src19.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha19 patch rejects: " + ", ".join(str(p.relative_to(src19)) for p in rejects))

# Fail early if the generated tree does not express the canonical alpha19 rules.
build_gradle = (src19 / "app/build.gradle").read_text(encoding="utf-8")
field_logic = (src19 / "app/src/main/java/ru/printcheck/android/ConstructorFieldLogic.java").read_text(encoding="utf-8")
main = (src19 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src19 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")

required = {
    "version 340019": "versionCode 340019" in build_gradle,
    "version alpha19": "versionName '3.4.0-alpha19'" in build_gradle,
    "colored field threshold": "MIN_COLOR_HIGHLIGHT_SCORE" in field_logic,
    "colored field fallback": "preserved-colored-field" in main,
    "no synthetic field invariant": "synthetic" in main.lower() or "синтет" in main.lower(),
    "color diagnostics": "field_highlight_rgb" in geom,
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha19 generated source invariant failure: " + ", ".join(bad))

print("Prepared canonical PrintCheck 3.4.0-alpha19 source")
print("source:", src19)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
