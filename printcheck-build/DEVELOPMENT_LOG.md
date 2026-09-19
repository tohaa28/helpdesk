# PrintCheck — DEVELOPMENT LOG

Purpose: permanent, Git-backed engineering journal. Every meaningful PrintCheck change must be recorded here so a new chat can continue without reconstructing decisions.

## Logging protocol — STRICT

For every implementation batch record:
- date;
- version/branch;
- user requirement being implemented;
- files/classes changed;
- behavior before;
- behavior after;
- architectural decisions and rejected alternatives;
- tests/invariants added or changed;
- build/run IDs and artifact hashes when available;
- known limitations and exact next step.

Do not keep implementation-critical knowledge only in chat.

---

## 2026-09-19 — alpha18 baseline recovered

Baseline release:
- version: 3.4.0-alpha18
- successful source commit: b645fd5077b64a053e926efbaf7fdedf30c0cdde
- successful Actions run: 35448700332
- artifact: PrintCheck_Android_3.4.0-alpha18_BUILD
- APK SHA-256: 61642079af67bd4dc85551d6e2a429b68152910f07ae5b8b4ed243db8f7b89fd
- source ZIP SHA-256: 00852094e3af6a217004f3768ff1023fb884b7a6fbec0152191d61af27fae2af

Key alpha18 work:
- synthetic order-size field construction removed;
- real PDF vector path candidates introduced;
- ConstructorVectorInspector implemented using pdfbox-android;
- order dimensions demoted to supporting evidence/scaling;
- asymmetric layout-minus-constructor artwork residual implemented;
- CDR/AI/EPS/ZIP constructor sources preserved, but CDR parsing not implemented;
- alpha7 positive/negative morphology retained;
- ApplicationFieldMapper removed;
- detailed field/alignment/residual diagnostics added;
- manual fallback used instead of inventing geometry.

Known baseline limitation:
RasterMatcher still fundamentally assumes translation / same-scale registration. General uniform-scale and rotation registration are not yet implemented.

---

## 2026-09-19 — canonical user workflow redefined for alpha19

User confirmed the checking algorithm:

1. Read order page and obtain articles, application types and application places.
2. Download customer layouts and templates/constructors in PDF and CDR.
3. Find the customer-selected application field inside the template. The field is always highlighted by color.
4. Compare template with customer layout and verify that the artwork is positioned correctly relative to that field.
   - If most of the customer's retained template is missing but the target field is still preserved, this is NOT an error.
5. Check the detected customer artwork against technical requirements for the exact application method selected by the customer.
6. Produce a short, structured report with clear human-readable visual evidence.

Consequences:
- field color in the template becomes the primary field-identification signal;
- generic rectangle scoring becomes secondary/fallback only;
- order dimensions must never create geometry;
- whole-template survival/coverage must not be a blocking correctness criterion;
- template service content must be excluded from artwork checks;
- PDF and CDR relations must remain tied to exact article/item/template relations;
- CDR must remain preserved now and should become a real parsed source in a later implementation step;
- designer-first report remains mandatory.

Documentation continuity requirement added:
Every meaningful code change, decision, test, build result and limitation must be written to Git in this log and canonical handoff.

---

## 2026-09-19 — alpha19 started

Branch:
- printcheck-build-3.4.0-alpha19

Starting objective:
- make colored-field detection the primary source of production field geometry;
- tolerate heavily deleted templates when the target field remains;
- preserve alpha18 real-vector/no-synthetic guarantees;
- keep technical checking scoped to detected customer artwork;
- improve diagnostics so the report explains which colored field was selected and why.

Initial engineering plan:
1. Inspect alpha18 ConstructorVectorInspector/ConstructorFieldLogic/MainActivity/GeometryAnalyzer.
2. Add explicit color metadata and colored-field candidate logic.
3. Change selection priority from generic geometry score to color-highlight evidence, while keeping real-path requirement.
4. Remove whole-template coverage as a blocking success condition.
5. Add invariants/tests for:
   - colored field wins over plausible uncolored rectangle;
   - partial template with target field preserved is accepted;
   - missing target field => manual review, never synthetic fallback;
   - order dimensions remain supporting evidence only;
   - template text/graphics outside artwork do not become artwork errors.
6. Update version to 3.4.0-alpha19 everywhere.
7. Build in CI, collect APK/source/hashes, record exact results here.


---

## 2026-09-19 — alpha19 implementation batch: colored-field primary geometry

Implemented locally and encoded into the reproducible alpha18→alpha19 patch:
- app version changed to versionCode 340019 / versionName 3.4.0-alpha19;
- ConstructorFieldLogic now requires real color evidence for automatic field selection;
- uncolored rectangles cannot auto-select only because dimensions/residual fit;
- generic chromatic highlighting is supported, not only red;
- field diagnostics expose highlight RGB, role and color score;
- ConstructorVectorInspector can inspect all PDF pages for colored-field anchors;
- MainActivity adds preserved-colored-field registration fallback;
- a mostly deleted customer-retained template is valid when the selected colored field remains and provides a reliable anchor;
- old whole-template 55% retained-coverage success threshold removed as a blocking rule;
- deleted constructor/template content is diagnostic-only, not an artwork or confidence penalty;
- GeometryAnalyzer keeps asymmetric artwork extraction: customer layout minus constructor/template;
- designer-facing label changed to “Цветное поле шаблона”;
- CDR preservation retained but CDR parsing is still not implemented;
- alpha7 positive/negative small-element morphology retained.

Tests:
- core tests: 52/52 passed;
- alpha19 source audit: 15/15 passed;
- patch reapplied successfully to a fresh exact alpha18 source tree and both test sets passed again.

Reproducibility:
- decoded alpha19 patch length: 92255 bytes;
- decoded patch SHA-256: cfd6f131a1a91a081c614209313f52d09b41ca8757a838d14467241fd76e9b34;
- base64 transport length: 28556;
- base64 transport SHA-256: f97340de8e07b76c68965b011b45b42fedfb26698d046c49792eaa98c1305439;
- generator: printcheck-build/prepare_alpha19.py;
- manifest: printcheck-build/ALPHA19_MANIFEST.txt.

CI history:
- run 35452196424 at source 83e05f4107ebe8f637ed694faf3dfe00843f37f6 failed before source generation because the original 6000-character part03 was stored as 5999 characters in Git;
- failure was correctly caught by the transport-length invariant before any patch/build step;
- repair strategy: keep the damaged part03 only as historical evidence, create exact part03a + part03b at 3000 characters each, and make prepare_alpha19.py use those instead;
- second recorded failure run 35452229659 used source 14b8bc4460d0149ffc08501b5afad5c68b7c3579, which predates the transport repair and is therefore not a valid post-fix build result.

Known limitations after this batch:
- CDR is saved_not_parsed;
- general uniform-scale/rotation registration is still not implemented;
- effects/gradients/transparency still need stricter spatial scoping to isolated artwork; live-font scoping is already artwork-specific.

Next gate:
- obtain a successful Android CI compile/build from a commit containing the repaired transport generator;
- collect APK/source/hash artifact;
- then validate real order 7966463 and save diagnostics.


---

## 2026-09-19 — alpha19 final successful build checkpoint

First fully successful alpha19 Android build:
- source commit: 4ff838665155d50ea7767bf1ad0b20ffe7ed6a9b
- Actions run: 35452353767
- result: success
- all prepare/invariant/audit/core/Gradle/package/hash/upload steps passed.

CI maintenance performed after that success:
- alpha19 workflow was changed so documentation-only updates to PRINTCHECK_HANDOFF.md, DEVELOPMENT_LOG.md and ALPHA19_MANIFEST.txt do not trigger Android rebuilds;
- purpose: mandatory detailed logging must not create build races or waste rebuilds.

Final authoritative alpha19 build after the workflow cleanup:
- source commit: 1b4d84a0194e48870da8772e51444571817e52b0
- Actions run: 35452512452
- status: success
- artifact name: PrintCheck_Android_3.4.0-alpha19_BUILD
- artifact ID: 10587615583
- GitHub artifact digest: sha256:6103b1ea801e4564d69635366b923eaa8f62e0c3ec9080f93274c724e5a38fd3
- artifact expiry reported by GitHub: 2026-09-26T15:41:23Z
- APK SHA-256: 4a8b71597045897d3b4bbe612580222c44c9db19ad30818a245508e74c932caf
- source ZIP SHA-256: d134a776d8b9b165728705b0ea1fe3f05c82f46af942001cbce001552487199f
- SHA file independent SHA-256: 9507b81c91d8c40265e5910c139472eb08aa6fb7d7e0e47456e5b2676717562d

Independent artifact verification after download:
- APK unzip integrity check: no errors;
- APK hash independently recomputed and matched CI;
- source ZIP hash independently recomputed and matched CI;
- source ZIP contains versionCode 340019 / versionName 3.4.0-alpha19;
- source ZIP contains ConstructorVectorInspector and ConstructorFieldLogic;
- source ZIP does not contain ApplicationFieldMapper;
- source ZIP exposes MIN_COLOR_HIGHLIGHT_SCORE, preserved-colored-field, field_highlight_rgb and “Цветное поле шаблона”;
- audit_alpha19.py from the packaged source: 15/15 passed;
- packaged-source core tests: 52/52 passed.

Authoritative current limitations:
- CDR is preserved but saved_not_parsed;
- general uniform-scale/rotation registration is not implemented; current registration is still mainly translation/same-scale plus colored-field translation anchor;
- effects/gradients/transparency still need spatial scoping strictly to isolated customer artwork;
- real fixture validation of selected application/place → intended colored field is still required.

Next development action:
- run alpha19 on control order 7966463;
- save/export diagnostics;
- inspect selected colored field, alignment and residual artwork for every position;
- correct real failures without synthetic geometry fallback.


---

## 2026-09-19 — alpha20 started from real diagnostics 7920509

Branch:
- printcheck-build-3.4.0-alpha20

User-reported problem:
- alpha19 detection of the actual application/artwork is unsatisfactory.

Diagnostic basis:
- PrintCheck_diagnostics_7920509_3.4.0-alpha19.zip supplied by the user.
- Analysis was performed against the downloaded layouts, full constructors, order-specific selected-application PDFs, result.json, report.txt and matching trace.

Root causes found — do not lose these:

1. The order-specific selected-application PDF is already the strongest reference for the exact selected field.
   In the supplied fixture its red/color-highlighted field directly corresponds to the customer-selected application/place.
   For several positions the layout→selected-application alignment was already strong while layout→full-constructor was absent, but alpha19 still blocked geometry because it treated full-constructor registration as a prerequisite.

   Observed examples from the diagnostic:
   - 17488.30 / A2: selected-application alignment about 0.971 coverage / 0.983 score, yet geometry was refused because layout→constructor was missing.
   - 17893.30 / UV3: selected-application alignment about 0.731 / 0.844, geometry refused for the same reason.
   - 19727.02 / LM1: selected-application alignment about 0.911 / 0.948, geometry refused.
   - 30114.30 / UV-DTF2: selected-application alignment about 0.968 / 0.982, geometry refused.

2. Artwork extraction incorrectly removed a dominant customer artwork color.
   alpha19 GeometryAnalyzer treated the dominant layout color inside the field as substrate/background.
   On 15637 this discarded the large black part of the actual artwork and retained mainly letters/details.
   This is architecturally wrong: customer artwork may legitimately fill most or all of a field with one solid color.

3. Field identity size incorrectly preferred a wider placement zone over the selected application size.
   For 25900.61 / A0 the selected application is 5×0.5 cm = 50×5 mm while the order text also contains a wider field/placement zone 10×0.5 cm = 100×5 mm.
   alpha19 searched/scored against 100×5 mm. The selected application size must identify the intended highlighted field first; the wider placement zone remains a constraint, never geometry.

4. Full-constructor subtraction can contaminate the residual with service/template differences.
   The order-specific selected-application template is a cleaner subtraction reference because it already represents the exact application/place selected by the customer.

Architectural correction for alpha20:
- promote the exact selected-application PDF to PRIMARY field and artwork reference;
- detect its actual color-highlighted field and use real observed geometry;
- register layout directly to that selected template;
- if normal registration fails, allow recovery by a preserved matching colored field;
- subtract selected-application template from customer layout inside the selected field;
- do NOT discard the dominant layout color;
- suppress only actual matching template content / local antialiasing residue;
- keep the full constructor as supporting/fallback evidence;
- selected application size is identity evidence before broader placement-zone dimensions;
- dimensions still never synthesize coordinates;
- retain alpha7 small-positive/small-negative morphology and font-in-artwork scoping.

Planned/implemented source areas:
- PartialTemplateLogic: selectedFieldIdentitySizeMm priority.
- ConstructorFieldLogic: selected-application PDF/raster as real reference-field sources.
- ConstructorVectorInspector: source-role aware inspection.
- GeometryAnalyzer: selected-application field detector, selected-template subtraction, reference-neighborhood antialias suppression, actual artwork-mask evidence.
- MainActivity: selected-application primary path + preserved-field alignment fallback; constructor fallback retained.
- ResultView/preflight: source-neutral wording and selected-template field treated as a real field.
- tests: selected-size-vs-placement-zone regression, real selected-application field source, alpha20 invariants.

Local gate before CI:
- core tests: 54/54 passed;
- alpha20 source audit: 17/17 passed.

Next:
- package alpha19→alpha20 reproducible patch in Git;
- run full Android CI compile/build;
- collect APK/source/hash artifact;
- then rerun the SAME order 7920509 and compare field selection and artwork masks position-by-position.


### CI attempt 1 — syntax-only failure and deterministic repair

- source commit: bf9076bb9594adedba70e3011f822c4f59394b86
- Actions run: 35454434785
- prepare source: PASS
- alpha20 invariants: PASS
- alpha20 audit: PASS
- core tests: PASS
- Android compile: FAIL

Compiler cause:
- MainActivity.java line 291 had one missing closing parenthesis in the new template_fragment_detected expression.
- This was not a logic/test failure; Gradle javac stopped on syntax before packaging.

Repair:
- local javac syntax check confirmed the line-291 parse error disappears after adding the missing parenthesis;
- Android-symbol errors outside Gradle are expected in that standalone javac check;
- reproducibility is preserved by an explicit deterministic post-patch repair inside printcheck-build/prepare_alpha20.py;
- repair commit: c02713b2e46af7dd91428d71d2077715bcbe9d2e.
- the repair is intentionally visible rather than silently modifying generated source.

Next gate:
- rerun full CI from the repair commit and require Android compile + artifact packaging to pass.


### Persistent Android update signing added — user requirement

User requirement:
- installing a new PrintCheck test build must update the existing app instead of requiring uninstall/reinstall.

Android requirements verified for our project:
- applicationId remains `ru.printcheck.android`;
- every later build must have a strictly larger versionCode;
- all update-compatible APKs must use the same signing certificate.

Problem with prior alpha builds:
- CI used the default Gradle debug signing identity;
- hosted CI runners can generate different debug keys;
- therefore a later APK can be rejected by Android as signed by a different certificate.

Alpha20+ solution:
- a dedicated persistent NON-PRODUCTION alpha signing identity was created;
- base64 transport stored in Git at `printcheck-build/NON_PRODUCTION_ALPHA_SIGNING.p12.b64`;
- prepare_alpha20.py verifies both transport SHA and decoded PKCS12 SHA before use;
- generated source receives `signing/printcheck-alpha-test.p12`;
- app/build.gradle gets signingConfig `alphaPersistent`;
- the debug APK is signed with that persistent identity;
- packaged source ZIP explicitly excludes *.p12 so the binary private key is not copied into the user-facing source archive;
- the signing material remains Git-backed only for internal alpha continuity.

Persistent alpha certificate:
- alias: printcheck-alpha
- certificate SHA-256 fingerprint: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11
- PKCS12 SHA-256: 153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10
- base64 transport SHA-256: 098c0b74d82bb794cf063a526b20f48365f2948915baef6275151ae69d8f2fb1
- certificate validity: 2026-09-19 through 2054-02-04.

Important transition rule:
- alpha19 was already distributed with the older temporary/default debug signing path;
- its private signing identity is not preserved;
- therefore alpha19 -> first persistent-signed alpha20 may require ONE final uninstall/reinstall;
- after a persistent-signed alpha20 is installed, alpha21/alpha22/etc. must install as normal Android updates, preserving app data, provided applicationId is unchanged and versionCode increases.

Security boundary:
- this persistent key is explicitly a NON-PRODUCTION alpha/test key;
- never use this key for a public/production release;
- before production distribution, establish a separate protected production signing identity and migration/distribution strategy.

CI continuity hardening:
- alpha20 workflow now refuses to write .ci/alpha20-result.txt when the run source SHA is no longer the current branch HEAD;
- this prevents an older concurrent run from overwriting the result of a newer build.


### Alpha20 successful signed Android build — update-compatible baseline

Successful build:
- source commit: 6a000b08878cee7cc82c59003758eb3f8d1e58f5
- Actions run: 35455256258
- status: success
- artifact: PrintCheck_Android_3.4.0-alpha20_BUILD
- artifact ID: 10588296469
- GitHub artifact digest: sha256:9c3e9b7ee24ec53e6eb937458e618c1814af5487cbd9e8a974accfddf9451390
- artifact expiry: 2026-09-26T16:33:40Z

Independent artifact verification:
- APK SHA-256: 712d7931a67c624f6582ee9e3c6dbf33a7bf6c3048c56866b0eb874f5668128e
- source ZIP SHA-256: 98b0d953480377e5ddb6bcc266e25ced8e5e0fe54c7ce99ee47c38e2b60881ba
- SHA file SHA-256: f5848f8e1545950e157824756646a9d9ed5fe79b4ee203c7b6989c663dd3e448
- APK ZIP integrity: PASS
- signer owner: CN=PrintCheck Alpha Test, OU=Development, O=PrintCheck, L=Test, ST=Test, C=RU
- signer SHA-256: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11
- signer algorithm: SHA384withRSA / 3072-bit RSA
- signer validity: 2026-09-19 through 2054-02-04
- packaged source contains alphaPersistent signing config and signing/README.txt;
- packaged source intentionally does NOT contain the private *.p12 file.

This successful alpha20 APK is the canonical install-over-update baseline for all subsequent alpha builds.

Transition:
- an already installed alpha19 may require one final uninstall before installing this alpha20 because alpha19 was produced before persistent signing was introduced;
- after this signed alpha20 is installed, all later distributed alpha APKs must retain applicationId ru.printcheck.android, use this same test signer, and increase versionCode so Android treats them as updates and preserves app data.


---

## 2026-09-19 — alpha21: stronger artwork detection + phone fullscreen evidence

Branch:
- printcheck-build-3.4.0-alpha21

User requirements:
- improve the methods for determining the actual customer application/artwork on the product;
- result images are too small and must open clearly fullscreen on a phone;
- alpha21 must install over the persistent-signed alpha20 without uninstalling;
- every change remains fully documented in Git.

Detection changes:
1. Added ArtworkDiffLogic as a pure-Java classifier for changed pixels.
   - unchanged template pixels are not artwork;
   - a customer color added onto template/background remains artwork even if the same color exists in a nearby technical line;
   - a template feature deleted by the designer is not artwork;
   - small local displacement of a real template feature can be suppressed as registration/rasterization residue.
2. GeometryAnalyzer uses selected-template subtraction v3:
   - engine marker: template-reference-subtraction-v3-local-registration;
   - actual diff marker: layout-minus-selected-template-v3-background-aware-local-registration.
3. Added local registration refinement around the real selected color field.
   - searches a small neighborhood around the global registration;
   - scores stable template/color features around the production field;
   - records refined/baseline score, inliers, samples and registration scale.
   - purpose: 1–3 px global raster offset should no longer turn template/service edges into fake artwork.
4. Added RegistrationLogic for safe field-anchor uniform-scale estimation.
   - uniform scaling is permitted as a registration recovery mechanism;
   - significant X/Y anisotropy is rejected;
   - non-uniform warp remains forbidden.
5. Models.Occurrence now carries scale and rotationDeg.
   - alpha21 uses scale;
   - general rotation registration is NOT yet implemented, rotationDeg remains 0 in current paths.
6. Preserved selected-field and constructor-field recovery can use uniform-scale+translation, not translation only.
7. Artwork physical dimensions are adjusted for registration scale.
8. For scaled registration, the old high-resolution small-element morphology is conservatively marked manual until that analyzer becomes fully scale-aware; no false automatic result is preferred over an incorrect one.
9. New isolated evidence image:
   - geometry JSON key: artwork_file;
   - image contains the detected customer artwork by itself plus target-field/artwork bounds;
   - designer can immediately inspect whether PrintCheck isolated the right object.

Phone/UI changes:
- visual previews in ResultView increased substantially;
- detected artwork evidence is displayed first as “Найденное нанесение”;
- tapping evidence opens a true fullscreen Dialog using Theme_Black_NoTitleBar_Fullscreen;
- immersive navigation/status-bar hiding;
- pinch zoom retained;
- max zoom increased to 8×;
- double tap toggles quick zoom;
- panning retained;
- fullscreen image decoding is sized for the actual screen and bitmap resources are recycled on dismiss.

Regression tests before CI:
- core tests: 60/60 passed;
- alpha21 source audit: 20/20 passed;
- added dedicated tests for:
  * uniform scale accepted;
  * non-uniform scale rejected;
  * solid artwork on plain field retained;
  * deleted template line not artwork;
  * same-color nearby technical line does not erase new customer artwork;
  * shifted real template feature is suppressed.

Reproducible patch:
- alpha20 -> alpha21 decoded patch length: 99589 bytes;
- decoded patch SHA-256: e5da0522349a4a51bf0b9da0081994894e3090d74fa78ae72bf80c13db79c956;
- base64/gzip transport length: 32836;
- transport SHA-256: d11d7ab37077fc3aaad7445bcb776ae8019ab4d16be8c95e88380807684b7c98;
- chunks: pc340a21.b64.part00..part05;
- generator: printcheck-build/prepare_alpha21.py.

Signing/update contract:
- applicationId stays ru.printcheck.android;
- versionCode becomes 340021;
- versionName becomes 3.4.0-alpha21;
- alphaPersistent signer from alpha20 is inherited and generator verifies exact PKCS12 SHA;
- CI additionally verifies the built APK certificate fingerprint with apksigner before upload.

Known limitations at this checkpoint:
- general rotation registration is still not implemented;
- CDR remains preserved but saved_not_parsed;
- scale-aware high-resolution positive/negative morphology still needs follow-up;
- real improvement on order 7920509 must be validated with an alpha21 diagnostic ZIP; local logic tests do not substitute for that real fixture.

Next gate:
- successful GitHub Android build;
- independent artifact/signature/hash verification;
- rerun order 7920509 and compare isolated artwork images position by position.


### Alpha21 CI attempt 1 — transport integrity failure

- source commit: 9759af9ae34da4080c733c5fbb9a3559b5668ee2
- Actions run: 35458553556
- failure step: Prepare canonical alpha21 source
- alpha20 reconstruction completed successfully.
- alpha21 patch was NOT applied because transport SHA did not match.
- observed transport SHA: b1bc3a70dcc574dcff6bc520d5d7552c5cea6481848364d1b47594e7a15dce42
- expected transport SHA: d11d7ab37077fc3aaad7445bcb776ae8019ab4d16be8c95e88380807684b7c98

Diagnosis:
- all transport chunk lengths were correct;
- Git blob hashes matched local originals for part00, part01, part02, part04, part05;
- only part03 differed despite identical length, proving a same-length one-character mutation during text transport.

Repair:
- original damaged Git part03 retained only as historical evidence;
- exact local part03 split into part03a + part03b, 2750 chars each;
- local Git blob SHA part03a: a814f61cc6e539af3ccd83d9c041661d7f1d2ab1;
- local Git blob SHA part03b: ebf3c411a3266f144a2471364b46b5ab2ab60a79;
- prepare_alpha21.py changed to use the two exact halves;
- repair source commit: cc825eb3f11a07fa1da657367354fe47f72f229e.

No application logic changed in this repair.


### Alpha21 final CI attempt 1 — Android compile API mismatch

- source commit: 8446193b39884f20742262ce6a97d8e15359e747
- Actions run: 35458799060
- canonical source generation: PASS
- alpha21 invariants: PASS
- alpha21 audit: PASS
- core tests: PASS (60/60)
- Android compile: FAIL

Compiler cause:
- GeometryAnalyzer.java high-resolution small-element path still called detectArtworkInField with the old alpha20 parameter list.
- alpha21 changed the method to receive RegistrationRefinement and ColorEstimate objects.
- only this high-resolution call-site remained unsynchronised.

Repair:
- high-resolution path now creates an identity RegistrationRefinement for the already-cropped aligned bitmaps and passes ColorEstimate objects directly;
- prepare_alpha21.py performs the repair deterministically after patch application;
- generator now has an invariant that rejects any remaining legacy detectArtworkInField(l,r,0,0...) call;
- local core tests remain 60/60 and audit remains 20/20 after repair;
- repair commit: 887d718784180167db3817cbd524bae2c067ab91.

No user-facing detection rule was weakened to make the build pass.


### Alpha21 final CI attempt 2 — escaped-newline generator bug

- source commit: 88bab90687b7c6da1ddc60c1817c1f2a161c634c
- Actions run: 35458974434
- canonical source generation: PASS
- invariants: PASS
- audit: PASS
- core tests: PASS (60/60)
- Android compile: FAIL

Cause:
- deterministic high-resolution API repair emitted the two Java statements separated by a literal backslash+n sequence instead of a real newline;
- javac correctly rejected the illegal '\\' character.

Repair:
- prepare_alpha21.py now emits a real newline;
- generator invariant additionally rejects the literal "\\n            MaskResult hi=" sequence in GeometryAnalyzer;
- repair commit: ccdab6592aa5ced74bc436ed6ea29aa290f5cff3.

Application detection logic itself is unchanged by this repair.


### Alpha21 successful final signed Android build

Canonical successful build:
- versionName: 3.4.0-alpha21
- versionCode: 340021
- applicationId: ru.printcheck.android
- source commit: 0ea3f268bdf965b9fb299b9ad875e7f58a35c352
- GitHub Actions run: 35459832052
- job: 105941624239
- status: success
- artifact name: PrintCheck_Android_3.4.0-alpha21_FINAL2_BUILD
- artifact ID: 10589092459
- artifact digest: sha256:c012abcb19c6e77ca73f1f6e8a299dc02d82fc84bf22ccf4302bd03a958f0290
- artifact expires: 2026-09-26T18:02:45Z

All final workflow gates passed:
- canonical alpha21 source generation;
- alpha21 source invariants;
- alpha21 audit;
- core tests;
- Android Gradle build;
- persistent signer verification;
- source packaging;
- artifact upload.

Independent downloaded-artifact verification:
- APK SHA-256: d80340c44e396fcc551a301b46970df0a60866b48a6a3c6a149af1414539725f
- source ZIP SHA-256: 48b975a6f7f3c8ea08bdc3327c0d49f40b784d5caa54fb0221269c00c978f84b
- signer file SHA-256: 2c3e07a2474567ca66c91af647fb06010e04a82b2b96aa1f534b17eb8feb1854
- SHA file SHA-256: 3b415438a64b111a46c47812c4159fe7f418daf5e63d869943d92cd9a3cfb049
- APK ZIP integrity: PASS
- source ZIP integrity: PASS
- packaged app/build.gradle confirms ru.printcheck.android / 340021 / 3.4.0-alpha21
- private *.p12 is absent from packaged source ZIP
- ArtworkDiffLogic.java present
- RegistrationLogic.java present
- signer DN: CN=PrintCheck Alpha Test, OU=Development, O=PrintCheck, L=Test, ST=Test, C=RU
- signer SHA-256: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Update compatibility:
- alpha21 uses the exact same persistent non-production alpha signer as alpha20;
- versionCode increased from 340020 to 340021;
- applicationId remains unchanged;
- therefore Android should install alpha21 directly over persistent-signed alpha20 without uninstalling and preserve app data.

Real-world validation still required:
- rerun control order 7920509;
- inspect the new isolated “Найденное нанесение” evidence for every position;
- export diagnostics and compare alpha20/alpha21 field registration and artwork masks.


---

## 2026-09-19 — alpha22: high-resolution ROI artwork detection

Trigger:
User reported that preview/result images are too low resolution and suspected this also causes artwork-detection errors. User uploaded:
- PrintCheck_diagnostics_7920509_3.4.0-alpha21.zip

Diagnostic findings from alpha21, order 7920509:
- article 15637: coarse geometry DPI 100; field about 127×127 px (32.26×32.26 mm).
- article 17488.30: 90 dpi; field about 143×54 px (40.36×15.24 mm).
- article 19727.02: 100 dpi; field about 143×64 px (36.33×16.26 mm).
- article 30114.30: 79 dpi; field about 156×172 px (50.16×55.30 mm).
- article 15423.10: 69 dpi; field about 550×267 px (202.46×98.29 mm).
- article 17893.30: 65 dpi; field about 321×474 px (125.44×185.23 mm).
- article 25900.61: no geometry object was produced at all; its failure is not explained by DPI alone and remains a separate mapping/alignment issue.

Root cause:
- RasterPdfIndexer.commonDpi intentionally capped global page rendering near 2200 px on the longest page dimension.
- GeometryAnalyzer then reused that same 65–100 dpi raster for the primary layout-minus-template artwork segmentation.
- Small-element analysis later rerendered crops at much higher DPI, so alpha21 could be inspecting fine detail after the primary artwork region had already been selected from a coarse mask.
- At 65–100 dpi, 0.2–0.3 mm lines are around 0.5–1.2 pixels wide, so anti-aliasing/registration error can dominate the signal.

Alpha22 architecture:
1. Keep low-cost global page matching at adaptive coarse DPI for page/constructor discovery.
2. Once a real selected colour field is known, render only that field plus ~5 mm margin from layout and selected reference PDF.
3. High-resolution artwork ROI target: up to 900 dpi.
4. Minimum target: 300 dpi when it fits the memory budget.
5. Per-ROI pixel budget: 8,000,000 pixels per bitmap; DPI is reduced adaptively for physically large fields rather than rendering the entire PDF page at huge resolution.
6. Re-run local registration inside the high-resolution ROI.
7. Run background-aware template subtraction on the high-resolution ROI.
8. Project the final high-res mask back into coarse page coordinates only for legacy overlay/font-scope integration.
9. Physical artwork width/height/position are measured from the high-resolution mask, not the coarse projection.
10. Isolated artwork evidence image is generated directly from the high-resolution ROI.
11. Evidence saving no longer upscales a low-resolution source; maximum output edge is 3200 px, but source detail is preserved rather than invented.
12. result.json now exposes:
   - coarse_geometry_dpi
   - artwork_analysis_dpi
   - artwork_analysis_mode
   - artwork_analysis_target_dpi
   - artwork_analysis_roi_width_px / height_px
   - artwork_highres_pixels/raw_pixels/components
   - high-res local-registration score/offset
   - artwork.measurement_dpi

Why not render all pages at 600–900 dpi:
- several constructor/application pages are physically very large;
- whole-page rendering at that resolution can exceed tens or hundreds of megapixels and cause Android OOM;
- ROI rendering gives high physical detail where it matters without sacrificing phone stability.

Local verification before Git CI:
- CoreTests: 63/63 passed.
- alpha22 audit: 17/17 passed.
- Added pure-Java AnalysisResolutionLogic tests:
  * small field rises close to 900 dpi;
  * large field remains within 8M-pixel budget and stays >=300 dpi when feasible;
  * chosen analysis DPI never drops below coarse DPI.

Reproducibility:
- alpha21 -> alpha22 patch bytes: 39762
- patch SHA-256: abdaa0f05855ab76730e0ba34a461b59845da84f4fbbf0d8552bd0f090eeb687
- gzip/base64 transport length: 15680
- transport SHA-256: c4c7dd906543b3ab9a37b71dd5f8790f572d1c4f21f3c96b6b27a5297eb945a6
- chunks: pc340a22.b64.part00..part02
- generator: printcheck-build/prepare_alpha22.py

Version/update contract:
- versionName 3.4.0-alpha22
- versionCode 340022
- applicationId ru.printcheck.android
- persistent alpha signer from alpha20/alpha21 must remain unchanged.

Required validation after build:
- rerun order 7920509;
- verify artwork_analysis_dpi is substantially higher than coarse_geometry_dpi;
- compare “Найденное нанесение” against alpha21 for every article;
- investigate 25900.61 separately if it still has no geometry.


### Alpha22 successful final signed Android build

Canonical successful build:
- versionName: 3.4.0-alpha22
- versionCode: 340022
- applicationId: ru.printcheck.android
- source commit: f5c7ca5ae083d85731c8d16e3e941c2d316a50d2
- GitHub Actions run: 35461116755
- job: 105945044808
- status: success
- artifact name: PrintCheck_Android_3.4.0-alpha22_FINAL_BUILD
- artifact ID: 10589449659
- artifact digest: sha256:c57cdaedfae59dc19709e78d1a01ebc4a2e522a9a48ba1d433deb399635f4f59
- artifact expires: 2026-09-26T18:26:37Z

All gates passed:
- canonical alpha22 source generation;
- alpha22 source invariants;
- alpha22 audit 17/17;
- core tests 63/63;
- Android Gradle build;
- persistent signer verification;
- source packaging;
- artifact upload.

Downloaded artifact verification:
- APK SHA-256: 2dfee546036afc18dd88ddd386f93f5693a11116f3ee9d3266fc206574c855af
- source ZIP SHA-256: b514fd73df4c4e9893125b105ab1a19c5dfded1b0f299d8d1feca93df68aa5f0
- signer TXT SHA-256: 2c3e07a2474567ca66c91af647fb06010e04a82b2b96aa1f534b17eb8feb1854
- SHA file SHA-256: 016e0abd73e69ae4c602b916a5525aef5da63d81ff5c247674b1b0993c198e9b
- signer SHA-256: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11
- packaged app/build.gradle confirms ru.printcheck.android / 340022 / 3.4.0-alpha22.

Update compatibility:
alpha22 is signed by the exact same persistent test certificate as alpha20 and alpha21 and should install directly over alpha21 without removing the app.

Primary real-world acceptance test:
rerun order 7920509 and confirm result.json reports highres-roi-v1 with artwork_analysis_dpi around:
- 15637: up to 900 dpi
- 17488.30: up to 900 dpi
- 19727.02: up to 900 dpi
- 30114.30: up to 900 dpi
- 15423.10: about 500 dpi under current ROI budget
- 17893.30: about 470 dpi under current ROI budget
Actual values depend on the final ROI/margins and clipping.

Separate unresolved case:
25900.61 had no geometry in alpha21; if it remains missing in alpha22, treat as a mapping/alignment issue rather than a resolution issue.


---

## 2026-09-19 — alpha23: performance recovery after alpha22 high-res ROI

User report:
- alpha22 takes several tens of minutes for one order.

Root causes found in alpha22 source:
1. High-res artwork ROI was rendered at up to 900 dpi / 8M px per bitmap.
2. Local high-res registration evaluated every pixel offset in a ~0.8 mm search radius. At high DPI this means thousands of candidate offsets.
3. Every candidate rescanned the reference support area and used many Bitmap.getPixel() calls.
4. Artwork subtraction itself used per-pixel getPixel() in the hot loop.
5. Small-element analysis rerendered layout + reference again at 600–2400 dpi and repeated template subtraction, even when the existing high-res artwork mask already had enough physical resolution.
6. Evidence extraction again read artwork pixels one-by-one.

Alpha23 optimization:
- main artwork target DPI: 720 instead of 900;
- main artwork bitmap budget: 4M instead of 8M pixels;
- ROI margin: 3.5 mm instead of 5 mm;
- registration support pixels are collected once per field and capped at 12,000 representative samples;
- registration translation search is coarse-to-fine instead of exhaustive per-pixel over the full radius;
- background estimation and artwork subtraction use bulk Bitmap.getPixels row reads;
- no per-pixel temporary row-array allocation in neighborhood matching;
- small-element morphology reuses the existing artwork high-res mask whenever that mask provides >=4 px across the smallest active rule;
- only genuinely finer rules trigger a second render;
- second render target is ~6 px/rule, capped at 1600 dpi instead of 10 px/rule / 2400 dpi;
- second render is cropped around the detected artwork bbox, not the entire production field, with 2.5M-pixel budget;
- evidence image extraction uses bulk row reads;
- stage timings are emitted in result.json:
  timing_coarse_render_ms
  timing_artwork_highres_ms
  timing_small_elements_ms
  timing_geometry_total_ms

Quality constraints retained:
- global matching remains coarse only;
- authoritative artwork detection still uses dedicated high-res ROI;
- minimum artwork ROI target remains 300 dpi when feasible;
- selected-template subtraction/background-aware logic unchanged;
- no synthetic field geometry;
- alpha7 positive/negative morphology retained;
- full-screen evidence retained.

Local reproducibility gates:
- clean alpha22 + alpha23 patch: PASS, no rejects;
- core tests: 66/66 PASS;
- alpha23 audit: 23/23 PASS.

Patch:
- decoded bytes: 56788
- patch SHA-256: 3a4eb46682094245aa525ece86b37a8a5610f371f161b0605314ddc4c9eef421
- transport chars: 18796
- transport SHA-256: 01d9f64368b4f54cfa068b37b9e19d088a0b894f21f3065a7144eaa5d59b39c1
- final transport part03 split into exact halves after same-length API mutation was detected; Git blob SHAs verified.

Version/update:
- versionName 3.4.0-alpha23
- versionCode 340023
- applicationId unchanged
- persistent signer unchanged.

Acceptance criteria:
- order 7920509 must no longer require tens of minutes;
- diagnostics must expose per-stage timings so any remaining hotspot can be measured on-device;
- artwork detection quality must not regress to alpha21 coarse-DPI behavior.


---

## 2026-09-19 — alpha23: performance recovery after alpha22 high-res ROI

User report:
- alpha22 takes several tens of minutes for one order.

Root causes found in alpha22 source:
1. High-res artwork ROI was rendered at up to 900 dpi / 8M px per bitmap.
2. Local high-res registration evaluated every pixel offset in a ~0.8 mm search radius. At high DPI this means thousands of candidate offsets.
3. Every candidate rescanned the reference support area and used many Bitmap.getPixel() calls.
4. Artwork subtraction itself used per-pixel getPixel() in the hot loop.
5. Small-element analysis rerendered layout + reference again at 600–2400 dpi and repeated template subtraction, even when the existing high-res artwork mask already had enough physical resolution.
6. Evidence extraction again read artwork pixels one-by-one.

Alpha23 optimization:
- main artwork target DPI: 720 instead of 900;
- main artwork bitmap budget: 4M instead of 8M pixels;
- ROI margin: 3.5 mm instead of 5 mm;
- registration support pixels are collected once per field and capped at 12,000 representative samples;
- registration translation search is coarse-to-fine instead of exhaustive per-pixel over the full radius;
- background estimation and artwork subtraction use bulk Bitmap.getPixels row reads;
- no per-pixel temporary row-array allocation in neighborhood matching;
- small-element morphology reuses the existing artwork high-res mask whenever that mask provides >=4 px across the smallest active rule;
- only genuinely finer rules trigger a second render;
- second render target is ~6 px/rule, capped at 1600 dpi instead of 10 px/rule / 2400 dpi;
- second render is cropped around the detected artwork bbox, not the entire production field, with 2.5M-pixel budget;
- evidence image extraction uses bulk row reads;
- stage timings are emitted in result.json:
  timing_coarse_render_ms
  timing_artwork_highres_ms
  timing_small_elements_ms
  timing_geometry_total_ms

Quality constraints retained:
- global matching remains coarse only;
- authoritative artwork detection still uses dedicated high-res ROI;
- minimum artwork ROI target remains 300 dpi when feasible;
- selected-template subtraction/background-aware logic unchanged;
- no synthetic field geometry;
- alpha7 positive/negative morphology retained;
- full-screen evidence retained.

Local reproducibility gates:
- clean alpha22 + alpha23 patch: PASS, no rejects;
- core tests: 66/66 PASS;
- alpha23 audit: 23/23 PASS.

Patch:
- decoded bytes: 56788
- patch SHA-256: 3a4eb46682094245aa525ece86b37a8a5610f371f161b0605314ddc4c9eef421
- transport chars: 18796
- transport SHA-256: 01d9f64368b4f54cfa068b37b9e19d088a0b894f21f3065a7144eaa5d59b39c1
- final transport part03 split into exact halves after same-length API mutation was detected; Git blob SHAs verified.

Version/update:
- versionName 3.4.0-alpha23
- versionCode 340023
- applicationId unchanged
- persistent signer unchanged.

Acceptance criteria:
- order 7920509 must no longer require tens of minutes;
- diagnostics must expose per-stage timings so any remaining hotspot can be measured on-device;
- artwork detection quality must not regress to alpha21 coarse-DPI behavior.


### Alpha23 successful final signed Android build

Canonical build:
- versionName: 3.4.0-alpha23
- versionCode: 340023
- applicationId: ru.printcheck.android
- source commit: 85ec610f83247ae3246238a736e87e8baf948883
- GitHub Actions run: 35464170600
- job: 105953218866
- status: success
- artifact: PrintCheck_Android_3.4.0-alpha23_FINAL_BUILD
- artifact ID: 10590573476
- artifact digest: sha256:42971990950361310b32b5819d5ea904deccedbe90dab8879e0a687cbf18316e
- artifact expires: 2026-09-26T19:24:16Z

Final gates:
- prepare_alpha23: PASS
- source invariants: PASS
- alpha23 audit: 23/23 PASS
- core tests: 66/66 PASS
- Android Gradle build: PASS
- persistent signer verification: PASS
- artifact upload: PASS

Downloaded-artifact verification:
- APK SHA-256: 2afac3b7a11cc75f375abd35e29f0ae99bc4af81c08e65f48957b3e490b0710c
- source ZIP SHA-256: b5fed7c7ac9085862d4b44bb6cbfbe375ada0c711eab5e5e12d4ce4743c339d8
- SHA file SHA-256: 632c94a0d3e9ea074b69ec0eb9016d2b44f45dfd2b9ba54833e5d39b5fd96bb5
- signer TXT SHA-256: 2c3e07a2474567ca66c91af647fb06010e04a82b2b96aa1f534b17eb8feb1854
- APK ZIP integrity: PASS
- source ZIP integrity: PASS
- packaged build.gradle confirms ru.printcheck.android / 340023 / 3.4.0-alpha23
- packaged source contains no private .p12
- signer SHA-256: 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Update compatibility:
alpha23 is signed with the exact persistent alpha20-alpha22 test signer, retains applicationId, and increments versionCode, so it should install over alpha22 without uninstall/data loss.

Performance validation requirement:
- rerun order 7920509;
- record total wall-clock order time;
- export diagnostics;
- inspect timing_coarse_render_ms / timing_artwork_highres_ms / timing_small_elements_ms / timing_geometry_total_ms per item;
- do not claim a numeric speed-up until the on-device run is measured.
