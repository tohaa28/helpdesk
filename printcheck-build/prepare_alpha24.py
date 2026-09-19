#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

# Alpha24 is reproducible from the canonical signed alpha23 source.
subprocess.run([sys.executable, str(pb / "prepare_alpha23.py"), str(repo)], check=True)

src23 = repo / ".printcheck-alpha23"
src24 = repo / ".printcheck-alpha24"
if src24.exists():
    shutil.rmtree(src24)
shutil.copytree(src23, src24)

part_names = [f"pc340a24.b64.part{i:02d}" for i in range(6)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha24 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 28048
expected_encoded_sha256 = "ed38fdaa5c3d64553da3e03225900356369fd412b3681d7547783cf87b8de758"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha24 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha24 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "069eef2c43a73fb3eb4d6bc93d98df7a9e4e433510058f9e221b0f261425c853"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha24 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha24.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)], cwd=src24, check=True)
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src24.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha24 patch rejects: " + ", ".join(str(p.relative_to(src24)) for p in rejects))

build_gradle = (src24 / "app/build.gradle").read_text(encoding="utf-8")
main = (src24 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src24 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
small = (src24 / "app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java").read_text(encoding="utf-8")
ruler_path = src24 / "app/src/main/java/ru/printcheck/android/MeasurementCalibrationLogic.java"
ruler = ruler_path.read_text(encoding="utf-8") if ruler_path.is_file() else ""

required = {
    "versionCode 340024": "versionCode 340024" in build_gradle,
    "versionName alpha24": "versionName '3.4.0-alpha24'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,

    "compact auth button": "new LinearLayout.LayoutParams(dp(70),dp(30))" in main,
    "auth top right marker": "auth_top_right_v1" in main,
    "auth toggles": 'value?"Выход":"Вход"' in main,
    "logout DOM detection": 'a[href*=\\\"/logout\\\"]' in main,
    "cookie logout": "removeAllCookies" in main,
    "hidden persisted-session check": "web.loadUrl(LOGIN_URL);" in main,

    "ruler class": ruler_path.is_file() and "class MeasurementCalibrationLogic" in ruler,
    "ruler disagreement guard": "MAX_ORDER_VECTOR_DISAGREEMENT = 0.12" in ruler,
    "ruler anisotropy guard": "MAX_AXIS_ANISOTROPY = 0.055" in ruler,
    "measurement sequence": "field->reference-ruler->artwork-size->small-elements" in geom,
    "reference ruler json": "reference_ruler" in geom and "rulerJson" in geom,
    "calibrated morphology": "analyzeCalibrated" in geom and "analyzeCalibrated" in small,
    "ruler overlay": "drawReferenceRuler" in geom and "Эталон" in geom,
    "ruler marker style": "component_circles_v4_reference_ruler" in geom,

    "authoritative reference": "artwork_reference_authoritative" in geom,
    "selected template authoritative": '"selected-application-template".equals(referenceRole)||selected.applicationAgreement>=.55' in geom,
    "constructor fallback guarded": "authoritativeArtworkReference" in geom and "small element" not in "",
    "manual preflight fallback": 'geo.optBoolean("artwork_reference_authoritative",false)' in main,

    "alpha23 performance retained": "ARTWORK_TARGET_DPI = 720" in geom and "MAX_ARTWORK_PIXELS = 4_000_000L" in geom and "collectRegistrationSamples" in geom,
    "no synthetic field mapper": not (src24 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists(),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha24 generated source invariant failure: " + ", ".join(bad))

signing = src24 / "signing/printcheck-alpha-test.p12"
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha24 tree")
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha24 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha24 source")
print("source:", src24)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
