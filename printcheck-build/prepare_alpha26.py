#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

subprocess.run([sys.executable, str(pb / "prepare_alpha25.py"), str(repo)], check=True)

src25 = repo / ".printcheck-alpha25"
src26 = repo / ".printcheck-alpha26"
if src26.exists():
    shutil.rmtree(src26)
shutil.copytree(src25, src26)

part_names = [f"pc340a26.b64.part{i:02d}" for i in range(4)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha26 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 19152
expected_encoded_sha256 = "dac56b123f63aa394c392aacdb8178c6efe39891430d833557608728cc85cbe5"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha26 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha26 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "e118395e92f605d46b41dc8c4683b8325efed02787bbcc76007070b0d8ab1fc3"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha26 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha26.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)], cwd=src26, check=True)
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src26.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha26 patch rejects: " + ", ".join(str(p.relative_to(src26)) for p in rejects))

build_gradle = (src26 / "app/build.gradle").read_text(encoding="utf-8")
main = (src26 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src26 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
small = (src26 / "app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java").read_text(encoding="utf-8")
color = (src26 / "app/src/main/java/ru/printcheck/android/ArtworkColorLayerLogic.java").read_text(encoding="utf-8")

required = {
    "versionCode 340026": "versionCode 340026" in build_gradle,
    "versionName alpha26": "versionName '3.4.0-alpha26'" in build_gradle,
    "application id retained": "applicationId 'ru.printcheck.android'" in build_gradle,
    "persistent signer retained": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,

    "solid reconstruction mode": 'mode="visible-color-solids-v2-seeded-components"' in color,
    "exclusive owner map": "int[] owner" in color and "out.owner" in color,
    "cross color contact map": "crossColorContact" in color,
    "seed supported reconstruction": "seed" in color and "reconstructedPixels" in color,

    "medial gap mode": 'out.mode="per-color-medial-gap-v2-intersection-safe"' in small,
    "positive other-color guard": "distanceToOtherColour" in small,
    "negative same-color": "negativeSameColor" in small,
    "other colors are barriers": "globalOwner[i]>0&&globalOwner[i]!=layerId" in small,
    "gap midpoint": 'g.x=(x+(n%w))*.5' in small and 'g.y=(y+(n/w))*.5' in small,

    "owner used by geometry": "analyzeColorLayers(colors.layers,colors.owner" in geom,
    "intersection excluded json": '"cross_color_intersections_excluded",true' in geom,
    "feature center json": '"center_x"' in geom and '"center_y"' in geom,
    "feature kind json": '"feature_kind"' in geom,
    "centered marker style": "centered_features_v6_intersection_safe_reference_ruler" in geom,
    "fixed centered circles": "float radius=18f" in geom and "b.centerX" in geom and "b.centerY" in geom,
    "new technical marker": "small_elements_per_color_medial_v3" in main and "intersection_safe_v1" in main and "centered_issue_markers_v1" in main,

    "ruler retained": "reference_ruler" in geom,
    "performance retained": "ARTWORK_TARGET_DPI = 720" in geom and "MAX_ARTWORK_PIXELS = 4_000_000L" in geom and "collectRegistrationSamples" in geom,
    "no synthetic field mapper": not (src26 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists(),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha26 generated source invariant failure: " + ", ".join(bad))

signing = src26 / "signing/printcheck-alpha-test.p12"
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha26 tree")
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha26 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha26 source")
print("source:", src26)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
