#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

subprocess.run([sys.executable, str(pb / "prepare_alpha24.py"), str(repo)], check=True)

src24 = repo / ".printcheck-alpha24"
src25 = repo / ".printcheck-alpha25"
if src25.exists():
    shutil.rmtree(src25)
shutil.copytree(src24, src25)

part_names = [f"pc340a25.b64.part{i:02d}" for i in range(6)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha25 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 26568
expected_encoded_sha256 = "bf2b0f8185f1ae6d8b9985e213d81a68c148e113ad875cfd3cea7cd3c804818e"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha25 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha25 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "2138292cf7ac5256886d8e7ed47b71b7283318b8fc96d0f83c202bf34a4b234d"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha25 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha25.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)], cwd=src25, check=True)
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src25.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha25 patch rejects: " + ", ".join(str(p.relative_to(src25)) for p in rejects))

build_gradle = (src25 / "app/build.gradle").read_text(encoding="utf-8")
main = (src25 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src25 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
small = (src25 / "app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java").read_text(encoding="utf-8")
color_path = src25 / "app/src/main/java/ru/printcheck/android/ArtworkColorLayerLogic.java"
color = color_path.read_text(encoding="utf-8") if color_path.is_file() else ""
ruler = (src25 / "app/src/main/java/ru/printcheck/android/MeasurementCalibrationLogic.java").read_text(encoding="utf-8")

required = {
    "versionCode 340025": "versionCode 340025" in build_gradle,
    "versionName alpha25": "versionName '3.4.0-alpha25'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,

    "color helper exists": color_path.is_file(),
    "visible color separations": "visible-color-separations-v1-background-ray" in color,
    "per-color analyzer": "analyzeColorLayers" in small and "analyzeColorLayers" in geom,
    "same-color negative": "negativeSameColor" in small,
    "single objects": "singleObjects" in small,
    "cross-color gaps ignored": '"cross_color_negative_gaps_ignored",true' in geom,
    "color layers json": 'o.put("color_layers",layers)' in geom,
    "layer count json": '"color_layer_count"' in geom,
    "continuous-tone guard": "colors.layers.size()>8" in geom,
    "empty-layer guard": 'if(colors.layers.isEmpty())' in geom,
    "marker style v5": "component_circles_v5_per_color_reference_ruler" in geom,
    "single-element check": '"single_element"' in main and "singleObjects" in small and "minSingleMm" in small,

    "legacy binary morphology not used hi": "analyzeCalibrated(hi.mask" not in geom,
    "legacy binary morphology not used mask": "analyzeCalibrated(mask.mask" not in geom,

    "reference ruler retained": "reference_ruler" in geom and "MeasurementCalibrationLogic" in geom and "MAX_AXIS_ANISOTROPY = 0.055" in ruler,
    "constructor authority safety": "artwork_reference_authoritative" in geom and 'geo.optBoolean("artwork_reference_authoritative",false)' in main,

    "auth retained": 'value?"Выход":"Вход"' in main and "removeAllCookies" in main,
    "performance retained": "ARTWORK_TARGET_DPI = 720" in geom and "MAX_ARTWORK_PIXELS = 4_000_000L" in geom and "collectRegistrationSamples" in geom,
    "no synthetic field mapper": not (src25 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists(),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha25 generated source invariant failure: " + ", ".join(bad))

signing = src25 / "signing/printcheck-alpha-test.p12"
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha25 tree")
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha25 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha25 source")
print("source:", src25)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
