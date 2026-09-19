#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

# Reproduce the exact canonical alpha19 source first.
subprocess.run([sys.executable, str(pb / "prepare_alpha19.py"), str(repo)], check=True)

src19 = repo / ".printcheck-alpha19"
src20 = repo / ".printcheck-alpha20"
if src20.exists():
    shutil.rmtree(src20)
shutil.copytree(src19, src20)

part_names = [f"pc340a20.b64.part{i:02d}" for i in range(8)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha20 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 41588
expected_encoded_sha256 = "abf3b7c5f6fc847dc41ffe7d7ad7aae2f254379ba736802f9c6d57f629742f93"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha20 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha20 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "c896959f4fed7afa63fcc77f1fd9f8fc9f4d5e3e2da44a8686cd2b51bfd8648f"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha20 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha20.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
        cwd=src20,
        check=True,
    )
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src20.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha20 patch rejects: " + ", ".join(str(p.relative_to(src20)) for p in rejects))

# CI run 35454434785 exposed one syntax-only parenthesis loss in the patch source.
# Keep this deterministic post-patch repair explicit and audited so the generated source is reproducible.
main_path = src20 / "app/src/main/java/ru/printcheck/android/MainActivity.java"
main_text = main_path.read_text(encoding="utf-8")
bad_fragment = '.put("template_fragment_detected",(layoutApp!=null&&"selected-field-anchor".equals(layoutApp.matchMethod))||(layoutCtor!=null&&("same-page-partial-template".equals(layoutCtor.matchMethod)||"preserved-colored-field".equals(layoutCtor.matchMethod)));'
good_fragment = '.put("template_fragment_detected",(layoutApp!=null&&"selected-field-anchor".equals(layoutApp.matchMethod))||(layoutCtor!=null&&("same-page-partial-template".equals(layoutCtor.matchMethod)||"preserved-colored-field".equals(layoutCtor.matchMethod))));'
if bad_fragment not in main_text:
    raise RuntimeError("alpha20 expected syntax repair fragment not found")
main_path.write_text(main_text.replace(bad_fragment, good_fragment, 1), encoding="utf-8")

build_gradle = (src20 / "app/build.gradle").read_text(encoding="utf-8")
field_logic = (src20 / "app/src/main/java/ru/printcheck/android/ConstructorFieldLogic.java").read_text(encoding="utf-8")
partial = (src20 / "app/src/main/java/ru/printcheck/android/PartialTemplateLogic.java").read_text(encoding="utf-8")
main = (src20 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src20 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")

required = {
    "versionCode 340020": "versionCode 340020" in build_gradle,
    "versionName alpha20": "versionName '3.4.0-alpha20'" in build_gradle,
    "selected application primary marker": "selected_application_template_primary_v2" in main,
    "selected field identity size": "selectedFieldIdentitySizeMm" in partial,
    "application raster real source": "SOURCE_APPLICATION_RASTER" in field_logic,
    "reference neighborhood subtraction": "matchesReferenceNeighborhood" in geom,
    "artwork mask evidence": "drawArtworkMask" in geom,
    "selected application analyzer": "analyzeApplicationField" in geom,
    "preserved selected field alignment": "recoverAlignmentFromApplicationField" in main,
    "constructor fallback retained": "constructor_vector_fallback_v2" in main,
    "no dominant artwork background removal": "colorDistance2(lc,layoutBg)<=bgThreshold" not in geom.replace(" ", ""),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha20 generated source invariant failure: " + ", ".join(bad))

if (src20 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists():
    raise RuntimeError("ApplicationFieldMapper must remain removed in alpha20")

print("Prepared canonical PrintCheck 3.4.0-alpha20 source")
print("source:", src20)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
