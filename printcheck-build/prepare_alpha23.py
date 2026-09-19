#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

subprocess.run([sys.executable, str(pb / "prepare_alpha22.py"), str(repo)], check=True)

src22 = repo / ".printcheck-alpha22"
src23 = repo / ".printcheck-alpha23"
if src23.exists():
    shutil.rmtree(src23)
shutil.copytree(src22, src23)

part_names = [
    "pc340a23.b64.part00",
    "pc340a23.b64.part01",
    "pc340a23.b64.part02",
    "pc340a23.b64.part03a",
    "pc340a23.b64.part03b",
]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha23 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 18796
expected_encoded_sha256 = "01d9f64368b4f54cfa068b37b9e19d088a0b894f21f3065a7144eaa5d59b39c1"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha23 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha23 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "3a4eb46682094245aa525ece86b37a8a5610f371f161b0605314ddc4c9eef421"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha23 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha23.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)], cwd=src23, check=True)
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src23.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha23 patch rejects: " + ", ".join(str(p.relative_to(src23)) for p in rejects))

build_gradle = (src23 / "app/build.gradle").read_text(encoding="utf-8")
main = (src23 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src23 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
logic = (src23 / "app/src/main/java/ru/printcheck/android/AnalysisResolutionLogic.java").read_text(encoding="utf-8")

required = {
    "versionCode 340023": "versionCode 340023" in build_gradle,
    "versionName alpha23": "versionName '3.4.0-alpha23'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle,
    "performance marker": "highres_artwork_roi_v2_performance" in main,
    "registration cache": "collectRegistrationSamples" in geom,
    "coarse to fine": "int step=dpi>=300?Math.max(2,dpi/180):1" in geom,
    "bulk rows": "layout.getPixels(lrow" in geom and "b.getPixels(row" in geom,
    "720 target": "ARTWORK_TARGET_DPI = 720" in geom,
    "4M budget": "MAX_ARTWORK_PIXELS = 4_000_000L" in geom,
    "small reuse": "smallElementHeuristicsFromHiRes" in geom,
    "tight small crop": '"crop_source",cropSource' in geom,
    "small feature helper": "chooseSmallFeatureDpi" in logic and "sufficientForRules" in logic,
    "timing diagnostics": all(x in geom for x in ["timing_coarse_render_ms","timing_artwork_highres_ms","timing_small_elements_ms","timing_geometry_total_ms"]),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha23 generated source invariant failure: " + ", ".join(bad))

signing = src23 / "signing/printcheck-alpha-test.p12"
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if not signing.is_file() or hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha23 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha23 source")
print("source:", src23)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
