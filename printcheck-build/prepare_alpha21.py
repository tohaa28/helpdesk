#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

# Alpha21 is reproducible from the canonical signed alpha20 generator.
subprocess.run([sys.executable, str(pb / "prepare_alpha20.py"), str(repo)], check=True)

src20 = repo / ".printcheck-alpha20"
src21 = repo / ".printcheck-alpha21"
if src21.exists():
    shutil.rmtree(src21)
shutil.copytree(src20, src21)

# part03 is split into exact halves after CI detected a one-character transport mutation.
part_names = [
    "pc340a21.b64.part00",
    "pc340a21.b64.part01",
    "pc340a21.b64.part02",
    "pc340a21.b64.part03a",
    "pc340a21.b64.part03b",
    "pc340a21.b64.part04",
    "pc340a21.b64.part05",
]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha21 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 32836
expected_encoded_sha256 = "d11d7ab37077fc3aaad7445bcb776ae8019ab4d16be8c95e88380807684b7c98"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha21 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha21 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "e5da0522349a4a51bf0b9da0081994894e3090d74fa78ae72bf80c13db79c956"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha21 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha21.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
        cwd=src21,
        check=True,
    )
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src21.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha21 patch rejects: " + ", ".join(str(p.relative_to(src21)) for p in rejects))

build_gradle = (src21 / "app/build.gradle").read_text(encoding="utf-8")
main = (src21 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src21 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
result = (src21 / "app/src/main/java/ru/printcheck/android/ResultView.java").read_text(encoding="utf-8")
zoom = (src21 / "app/src/main/java/ru/printcheck/android/ZoomImageView.java").read_text(encoding="utf-8")
art = src21 / "app/src/main/java/ru/printcheck/android/ArtworkDiffLogic.java"
reg = src21 / "app/src/main/java/ru/printcheck/android/RegistrationLogic.java"

required = {
    "versionCode 340021": "versionCode 340021" in build_gradle,
    "versionName alpha21": "versionName '3.4.0-alpha21'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,
    "artwork diff helper": art.is_file() and "isAdded" in art.read_text(encoding="utf-8"),
    "uniform registration helper": reg.is_file() and "estimateUniformScale" in reg.read_text(encoding="utf-8"),
    "selected application v3": "selected_application_template_primary_v3" in main,
    "uniform field anchor": "uniform_field_scale_anchor_v1" in main,
    "local field registration": "local_field_registration_v1" in main and "local_registration_refined" in geom,
    "background aware diff": "ArtworkDiffLogic.isAdded" in geom and "background-aware-local-registration" in geom,
    "artwork evidence": "artwork_file" in geom and "saveArtworkEvidence" in geom,
    "fullscreen viewer": "Theme_Black_NoTitleBar_Fullscreen" in result and "SYSTEM_UI_FLAG_IMMERSIVE_STICKY" in result,
    "double tap zoom": "onDoubleTap" in zoom and "maxScale=8f" in zoom,
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha21 generated source invariant failure: " + ", ".join(bad))

if (src21 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists():
    raise RuntimeError("ApplicationFieldMapper must remain removed in alpha21")

signing = src21 / "signing/printcheck-alpha-test.p12"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha21 tree")
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha21 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha21 source")
print("source:", src21)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
