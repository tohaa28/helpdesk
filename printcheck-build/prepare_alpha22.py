#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

# Reconstruct the exact signed alpha21 source first.
subprocess.run([sys.executable, str(pb / "prepare_alpha21.py"), str(repo)], check=True)

src21 = repo / ".printcheck-alpha21"
src22 = repo / ".printcheck-alpha22"
if src22.exists():
    shutil.rmtree(src22)
shutil.copytree(src21, src22)

part_names = [f"pc340a22.b64.part{i:02d}" for i in range(3)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha22 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 15680
expected_encoded_sha256 = "c4c7dd906543b3ab9a37b71dd5f8790f572d1c4f21f3c96b6b27a5297eb945a6"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha22 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha22 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "abdaa0f05855ab76730e0ba34a461b59845da84f4fbbf0d8552bd0f090eeb687"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha22 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha22.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
        cwd=src22,
        check=True,
    )
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src22.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha22 patch rejects: " + ", ".join(str(p.relative_to(src22)) for p in rejects))

build_gradle = (src22 / "app/build.gradle").read_text(encoding="utf-8")
main = (src22 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src22 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
res = (src22 / "app/src/main/java/ru/printcheck/android/AnalysisResolutionLogic.java").read_text(encoding="utf-8")

required = {
    "versionCode 340022": "versionCode 340022" in build_gradle,
    "versionName alpha22": "versionName '3.4.0-alpha22'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,
    "highres marker": "highres_artwork_roi_v1" in main,
    "highres ROI": "analyzeArtworkHighRes" in geom,
    "target 900": "ARTWORK_TARGET_DPI = 900" in geom,
    "minimum 300": "ARTWORK_MIN_DPI = 300" in geom,
    "8M budget": "MAX_ARTWORK_PIXELS = 8_000_000L" in geom,
    "coarse dpi diagnostics": "coarse_geometry_dpi" in geom,
    "analysis dpi diagnostics": "artwork_analysis_dpi" in geom,
    "highres measurement": "measurement_dpi" in geom,
    "v4 subtraction": "layout-minus-selected-template-v4-highres-roi-background-aware" in geom,
    "highres evidence": "saveArtworkEvidence(hi.layout,hi.layoutField,hi.art,mask)" in geom,
    "no fake upscale": "Math.min(1f,Math.min(3200f/sw,3200f/sh))" in geom,
    "resolution helper": "chooseArtworkDpi" in res,
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha22 generated source invariant failure: " + ", ".join(bad))

if (src22 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists():
    raise RuntimeError("ApplicationFieldMapper must remain removed in alpha22")

signing = src22 / "signing/printcheck-alpha-test.p12"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha22 tree")
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha22 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha22 source")
print("source:", src22)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
