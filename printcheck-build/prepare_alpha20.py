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

# All alpha20+ CI APKs use one persistent NON-PRODUCTION signing identity.
# This allows Android to install later alpha builds as updates instead of requiring uninstall.
# The key is intentionally limited to internal alpha builds and must never be reused as a production release key.
signing_b64_path = pb / "NON_PRODUCTION_ALPHA_SIGNING.p12.b64"
if not signing_b64_path.is_file():
    raise RuntimeError("persistent alpha signing material is missing")
signing_encoded = signing_b64_path.read_bytes().replace(b"\n", b"").replace(b"\r", b"")
expected_signing_b64_sha256 = "098c0b74d82bb794cf063a526b20f48365f2948915baef6275151ae69d8f2fb1"
if hashlib.sha256(signing_encoded).hexdigest() != expected_signing_b64_sha256:
    raise RuntimeError("persistent alpha signing base64 sha256 mismatch")
signing_bytes = base64.b64decode(signing_encoded, validate=True)
expected_signing_p12_sha256 = "153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10"
if hashlib.sha256(signing_bytes).hexdigest() != expected_signing_p12_sha256:
    raise RuntimeError("persistent alpha signing p12 sha256 mismatch")
signing_dir = src20 / "signing"
signing_dir.mkdir(parents=True, exist_ok=True)
(signing_dir / "printcheck-alpha-test.p12").write_bytes(signing_bytes)
(signing_dir / "README.txt").write_text(
    "PrintCheck alpha builds from GitHub CI use a persistent NON-PRODUCTION test signing identity.\n"
    "Certificate SHA-256: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11\n"
    "Purpose: permit in-place Android updates between alpha20 and later alpha test builds.\n"
    "The private signing file is excluded from packaged source ZIPs and must not be used for production releases.\n",
    encoding="utf-8",
)

gradle_path = src20 / "app/build.gradle"
gradle_text = gradle_path.read_text(encoding="utf-8")
signing_marker = "alphaPersistent"
if signing_marker not in gradle_text:
    signing_config = '''
    // Persistent NON-PRODUCTION signing identity for install-over-update alpha builds.
    signingConfigs {
        alphaPersistent {
            storeFile file("$rootDir/signing/printcheck-alpha-test.p12")
            storePassword 'PrintCheckAlpha2026!'
            keyAlias 'printcheck-alpha'
            keyPassword 'PrintCheckAlpha2026!'
            enableV1Signing true
            enableV2Signing true
        }
    }

'''
    gradle_text = gradle_text.replace("    testOptions {", signing_config + "    testOptions {", 1)
    gradle_text = gradle_text.replace(
        "        debug { minifyEnabled false }",
        "        debug {\n            minifyEnabled false\n            signingConfig signingConfigs.alphaPersistent\n        }",
        1,
    )
    gradle_path.write_text(gradle_text, encoding="utf-8")

build_gradle = (src20 / "app/build.gradle").read_text(encoding="utf-8")
field_logic = (src20 / "app/src/main/java/ru/printcheck/android/ConstructorFieldLogic.java").read_text(encoding="utf-8")
partial = (src20 / "app/src/main/java/ru/printcheck/android/PartialTemplateLogic.java").read_text(encoding="utf-8")
main = (src20 / "app/src/main/java/ru/printcheck/android/MainActivity.java").read_text(encoding="utf-8")
geom = (src20 / "app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java").read_text(encoding="utf-8")

required = {
    "versionCode 340020": "versionCode 340020" in build_gradle,
    "versionName alpha20": "versionName '3.4.0-alpha20'" in build_gradle,
    "persistent alpha signing config": "alphaPersistent" in build_gradle and "printcheck-alpha-test.p12" in build_gradle,
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
