#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pb = repo / "printcheck-build"

subprocess.run([sys.executable, str(pb / "prepare_alpha27.py"), str(repo)], check=True)

src27 = repo / ".printcheck-alpha27"
src28 = repo / ".printcheck-alpha28"
if src28.exists():
    shutil.rmtree(src28)
shutil.copytree(src27, src28)

parts = [pb / f"pc340a28.b64.part{i:02d}" for i in range(3)]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError("alpha28 base64 parts missing: " + ", ".join(missing))

encoded = b"".join(p.read_bytes().replace(b"\n", b"").replace(b"\r", b"") for p in parts)
expected_encoded_len = 15964
expected_encoded_sha256 = "fe4cc95bc69fb15233fcbeee779bdf360b1b6a9fdcd3e1004f9ce75ece3a7a6e"
if len(encoded) != expected_encoded_len:
    raise RuntimeError(f"alpha28 base64 length mismatch: {len(encoded)} != {expected_encoded_len}")
encoded_sha = hashlib.sha256(encoded).hexdigest()
if encoded_sha != expected_encoded_sha256:
    raise RuntimeError(f"alpha28 base64 sha256 mismatch: {encoded_sha}")

patch_bytes = gzip.decompress(base64.b64decode(encoded, validate=True))
expected_patch_sha256 = "a8d5c115247c2e8d563b743b0c9ff53bb0e721e56c8e224569da63353bf22ef1"
patch_sha = hashlib.sha256(patch_bytes).hexdigest()
if patch_sha != expected_patch_sha256:
    raise RuntimeError(f"alpha28 patch sha256 mismatch: {patch_sha}")

patch_path = repo / ".alpha28.patch"
patch_path.write_bytes(patch_bytes)
try:
    subprocess.run(["patch", "-p4", "--batch", "--forward", "-i", str(patch_path)], cwd=src28, check=True)
finally:
    patch_path.unlink(missing_ok=True)

rejects = list(src28.rglob("*.rej"))
if rejects:
    raise RuntimeError("alpha28 patch rejects: " + ", ".join(str(p.relative_to(src28)) for p in rejects))

# Android Gravity has no BASELINE constant. Keep the title/version on one row and
# center them vertically; this preserves the requested compact inline version.
main_path = src28 / "app/src/main/java/ru/printcheck/android/MainActivity.java"
main_text = main_path.read_text(encoding="utf-8")
bad_gravity = "brandLine.setGravity(Gravity.BASELINE)"
if main_text.count(bad_gravity) != 1:
    raise RuntimeError(f"alpha28 expected one brand-line BASELINE anchor, found {main_text.count(bad_gravity)}")
main_path.write_text(main_text.replace(bad_gravity, "brandLine.setGravity(Gravity.CENTER_VERTICAL)", 1), encoding="utf-8")

build = (src28 / "app/build.gradle").read_text(encoding="utf-8")
main = (src28 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
result = (src28 / "app/src/main/java/ru/printcheck/android/ResultView.java").read_text(encoding="utf-8")
geom = (src28 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")
small = (src28 / "app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java").read_text(encoding="utf-8")

required = {
    "versionCode 340028": "versionCode 340028" in build,
    "versionName alpha28": "versionName '3.4.0-alpha28'" in build,
    "application id retained": "applicationId 'ru.printcheck.android'" in build,
    "persistent signer retained": "alphaPersistent" in build and "printcheck-alpha-test.p12" in build,

    "brand line": "brandLine.setOrientation(LinearLayout.HORIZONTAL)" in main and "brandLine.setGravity(Gravity.CENTER_VERTICAL)" in main and "Gravity.BASELINE" not in main,
    "small inline version": "TextView version=text(BuildConfig.VERSION_NAME,10)" in main and "brandLine.addView(version)" in main,
    "queue button renamed": 'actionButton("Заказы ожидающие проверку"' in main,
    "queue dialog renamed": 'setTitle("Заказы ожидающие проверку · "+orders.size())' in main,
    "queue button full width": "controlCard.addView(ordersButton,queueLp)" in main,

    "tree toggle": "class TreeToggle" in result,
    "order tree": 'treeNode(a,"Заказ №"+result.optString("order")' in result,
    "article tree": 'treeNode(a,"Арт. "+article' in result,
    "brief checklist": 'treeNode(a,"Краткий чеклист"' in result,
    "detailed checklist": 'treeNode(a,"Подробный чеклист"' in result,
    "brief checks": "addBriefChecks" in result and "shortStatus" in result,
    "lazy details": "Runnable loadDetails=()->populateDetailedChecklist" in result and "if(show&&firstOpen!=null&&!n.loaded)" in result,
    "single order expanded": "buildOrderTree(a,runDir,orderReport,result,technicalReport,true)" in result,
    "batch order collapsed": "buildOrderTree(a,e.runDir,e.reportFile,e.result,e.technicalReport,false)" in result,
    "order report nested": 'order.body.addView(reportAction(a,orderReport,"PDF-отчёт заказа")' in result,
    "article report nested": 'briefNode.body.addView(reportAction(a,rf,"PDF-отчёт артикула")' in result,

    "alpha27 markers retained": "rule_diameter_circles_v7_no_center_dot_reference_ruler" in geom and 'marker_center_symbol",false' in geom,
    "alpha26 geometry retained": "per-color-medial-gap-v2-intersection-safe" in small and "distanceToOtherColour" in small and "negativeSameColor" in small,
    "reference ruler retained": "reference_ruler" in geom,
    "performance retained": "ARTWORK_TARGET_DPI = 720" in geom and "MAX_ARTWORK_PIXELS = 4_000_000L" in geom,
    "no synthetic mapper": not (src28 / "app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java").exists(),
}
bad = [name for name, ok in required.items() if not ok]
if bad:
    raise RuntimeError("alpha28 generated source invariant failure: " + ", ".join(bad))

signing = src28 / "signing/printcheck-alpha-test.p12"
expected_signing_sha = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if not signing.is_file():
    raise RuntimeError("persistent alpha signing key missing from generated alpha28 tree")
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError("alpha28 signing identity changed unexpectedly")

print("Prepared canonical PrintCheck 3.4.0-alpha28 source")
print("source:", src28)
print("patch_sha256:", patch_sha)
print("transport_sha256:", encoded_sha)
print("signing_sha256:", expected_signing_sha)
