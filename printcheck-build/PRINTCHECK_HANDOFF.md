# PrintCheck — canonical handoff and development protocol

Last updated: 2026-09-19
Repository: tohaa28/helpdesk
Current implementation line: Android 3.4.0-alpha29
Current development/build branch: printcheck-build-3.4.0-alpha29

## STRICT CONTINUITY RULE

This is the canonical Git-backed handoff for PrintCheck. It is intentionally detailed enough that a new chat must be able to continue development without asking the user to reconstruct earlier decisions.

For every meaningful PrintCheck change:
1. Change code/build infrastructure in Git.
2. Append DEVELOPMENT_LOG.md with what changed, why, files/classes affected, tests, failures/fixes, and exact next step.
3. Update this handoff when canonical behavior, architecture, requirements, build process, limitations, fixtures, or next steps change.
4. Update the version everywhere it is user-visible and in artifact names.
5. Record exact source commit, GitHub Actions run, artifact ID, and hashes for successful builds.
6. Do not keep implementation-critical knowledge only in chat.
7. Documentation-only commits are ignored by the alpha19 Android workflow so logging can continue without causing CI races.

A release/checkpoint is not complete until source invariants, tests, Android build, artifact collection, hashes, and documentation are all recorded.

## PRODUCT PURPOSE

PrintCheck checks customer artwork for each ordered item against:
- the exact order article/item;
- the exact application method selected by the customer;
- the exact application place selected by the customer;
- the corresponding template/constructor;
- the technical requirements for that selected application method.

The primary user is a technical designer. The result must therefore be short, structured, visual, and explainable, while detailed diagnostics remain exportable separately.

## CANONICAL CHECKING ALGORITHM — USER CONFIRMED 2026-09-19

### 1. Read the order page

For every ordered position obtain and preserve:
- article / SKU;
- base article when relevant;
- item_id and DOM/order relation when available;
- selected application code/name;
- selected application place;
- field/max-size metadata supplied by the order;
- relation to customer layouts;
- relation to article template/constructor;
- relation to the selected application-template/technical requirements.

Relationship priority:
1. “Шаблоны макетов” tab is authoritative for article ↔ constructor because article and constructor are shown side-by-side.
2. Selected applications block is authoritative for the customer's selected application.
3. DOM item IDs and explicit order relations.
4. Base article grouping.
5. URL/article fallback.
6. Filename matching is diagnostic/final fallback only.

Login remains website-only. Do not reintroduce embedded/direct application authentication.

### 2. Download source files

Download and preserve:
- customer layout files;
- template/constructor PDF;
- template/constructor CDR;
- available supporting AI/EPS/ZIP links/files;
- source URL, article/item relation, role, format, and hashes/diagnostics.

PDF and CDR must remain tied to the exact article/item/template relation from the order page.

Current implementation preserves CDR but does not parse it yet. CDR status is explicitly saved_not_parsed; PDF remains the active geometric source.

### 3. Find the selected application field in the template

The target application field exists in the template and is always highlighted by color.

Canonical rules:
- the field must come from real template geometry;
- color highlighting is the primary automatic identification signal;
- do not construct a synthetic rectangle from order width/height;
- do not choose an arbitrary uncolored rectangle just because its dimensions look plausible;
- order dimensions may only verify candidate identity and infer physical scale;
- selected application-template may only provide supporting evidence, never final geometry;
- if a real colored field cannot be identified confidently, return manual review instead of guessing.

Alpha19 supports a generic chromatic highlight signal rather than hard-coding only red.

### 4. Register customer layout to the correct template

Compare the customer layout with the correct full template and establish the position of the artwork relative to the target colored field.

Partial template deletion is explicitly allowed.

If the designer/customer removed most of the template but the target colored field is still present, this is NOT an error. Whole-template retained percentage must never be a blocking condition.

Alpha19 has two registration paths:
- existing template/raster registration for compatible same-scale geometry;
- preserved-colored-field fallback, which pairs the retained colored field in the customer layout with the colored field in the full template and derives translation from that anchor.

Deleted constructor/template content is diagnostic-only and must not be interpreted as customer artwork.

Non-uniform warp is not desired/accepted.

### 5. Isolate actual customer artwork

After registration, separate customer artwork from template service graphics.

Canonical direction:
customer artwork = layout foreground minus matching constructor/template foreground.

Template service content is not customer artwork:
- colored field boundary/fill;
- product outlines;
- guides;
- dashed field frames;
- labels;
- technical lines;
- other constructor/template graphics.

A constructor part deleted by the customer is not artwork.

If no stable added artwork remains after subtraction, do not fabricate artwork; return manual review.

### 6. Check only actual artwork against the selected technology requirements

Apply technical rules belonging to the exact application method selected by the customer.

Relevant checks include, where applicable:
- live fonts;
- gradients;
- transparency;
- prohibited effects;
- maximum dimensions;
- minimum positive elements;
- minimum negative elements / knockouts;
- minimum element/letter sizes;
- raster resolution;
- ink/CMYK/technology-specific constraints;
- protective field/bleed and other method-specific rules.

Strict font rule:
live fonts are forbidden only in the actual customer artwork. Text in the template/constructor/service labels/outside the application must not create a font error.

Current limitation to preserve in future work:
live-font scoping is artwork-specific, but effects/gradients/transparency still need stronger spatial scoping to the isolated artwork. Do not falsely claim this is fully solved in alpha19.

Alpha7 positive/negative small-element morphology and its visual markers are trusted behavior and must be preserved.

### 7. Produce a designer-first report

For each item show a compact readable summary:
- article;
- application method;
- application place;
- template found/not found;
- colored field found/not found;
- placement correct/incorrect/manual;
- actual artwork dimensions;
- technical violations;
- final status.

Visual evidence must be prominent:
- relevant template/product area;
- selected colored application field;
- detected customer artwork;
- clear circles/arrows for violations;
- if placement is wrong, visibly show actual vs expected region.

Detailed logs/diagnostics remain separately exportable.

## CURRENT ALPHA19 IMPLEMENTATION

### Version
- Android versionCode: 340019
- Android versionName: 3.4.0-alpha19
- branch: printcheck-build-3.4.0-alpha19

### Main behavior added in alpha19
- ConstructorFieldLogic.MIN_COLOR_HIGHLIGHT_SCORE = 0.48.
- Automatic field selection filters to real candidates with sufficient color-highlight evidence.
- Uncolored rectangles cannot auto-select solely from geometry/order size/residual.
- Generic strongly chromatic stroke/fill colors are supported; red receives only a small preference rather than being the sole accepted color.
- Diagnostics expose field_color_score, field_highlight_rgb, and field_highlight_role.
- ConstructorVectorInspector can inspect all PDF pages for colored-field anchors.
- MainActivity includes preserved-colored-field registration fallback for severely deleted retained templates.
- Old whole-template ~55% coverage criterion was removed as a blocking success condition.
- Deleted template content no longer reduces field confidence merely because it is absent.
- GeometryAnalyzer keeps asymmetric layout-minus-constructor artwork extraction.
- UI label is “Цветное поле шаблона”.
- CDR/AI/EPS/ZIP preservation from alpha18 remains.
- No synthetic order-size field mapper was reintroduced.
- ApplicationFieldMapper remains removed.
- Alpha7 small-element morphology remains.

### Field candidate policy
A candidate must originate from real PDF/CDR vector source data and carry real source path IDs.
Current alpha19 automatic selection uses:
- color-highlight evidence as primary evidence;
- geometry/style;
- order-size agreement only as verification/scale support;
- page plausibility;
- added residual artwork;
- selected application-template agreement as supporting evidence.

If colored candidates are absent or ambiguous, the correct result is manual review.

## ALPHA19 TEST/BUILD CHECKPOINT

Local/reproducibility checks:
- clean alpha18 → alpha19 patch reapply: success;
- alpha19 source audit: 15/15 passed;
- core tests: 52/52 passed.

Final GitHub Actions checkpoint:
- source commit: 1b4d84a0194e48870da8772e51444571817e52b0
- workflow run: 35452512452
- run status: success
- artifact name: PrintCheck_Android_3.4.0-alpha19_BUILD
- artifact ID: 10587615583
- artifact archive digest: sha256:6103b1ea801e4564d69635366b923eaa8f62e0c3ec9080f93274c724e5a38fd3
- artifact expiration reported by GitHub: 2026-09-26T15:41:23Z
- APK SHA-256: 4a8b71597045897d3b4bbe612580222c44c9db19ad30818a245508e74c932caf
- source ZIP SHA-256: d134a776d8b9b165728705b0ea1fe3f05c82f46af942001cbce001552487199f
- SHA file SHA-256 (local independent hash): 9507b81c91d8c40265e5910c139472eb08aa6fb7d7e0e47456e5b2676717562d

Final run steps all passed:
- canonical alpha19 source generation;
- source invariants;
- alpha19 audit;
- core tests;
- Android Gradle compile/build;
- source packaging;
- APK/source hashing;
- artifact upload;
- CI result recording.

The downloaded final APK was independently checked with unzip -t and reported no compressed-data errors. The downloaded APK/source SHA-256 values matched the CI hash file.

### Reproducible source transport
Generator:
- printcheck-build/prepare_alpha19.py

Manifest:
- printcheck-build/ALPHA19_MANIFEST.txt

Active transport chunks:
- pc340a19.b64.part00
- pc340a19.b64.part01
- pc340a19.b64.part02
- pc340a19.b64.part03a
- pc340a19.b64.part03b
- pc340a19.b64.part04

Concatenated active base64:
- length: 28556
- SHA-256: f97340de8e07b76c68965b011b45b42fedfb26698d046c49792eaa98c1305439

Decoded patch:
- length: 92255 bytes
- SHA-256: cfd6f131a1a91a081c614209313f52d09b41ca8757a838d14467241fd76e9b34

Historical damaged pc340a19.b64.part03 is intentionally not used by prepare_alpha19.py. It is retained only as evidence of the first transport failure.

### CI failure history worth retaining
- run 35452196424 / source 83e05f4107ebe8f637ed694faf3dfe00843f37f6 failed before alpha19 source generation because original part03 was 5999 instead of 6000 chars; invariant correctly stopped the build at total transport length 28555.
- run 35452229659 / source 14b8bc4460d0149ffc08501b5afad5c68b7c3579 also predates the repaired active transport.
- subsequent concurrent early repair/doc runs are not release checkpoints; the authoritative successful checkpoints are run 35452353767 and final run 35452512452.
- run 35452353767 / source 4ff838665155d50ea7767bf1ad0b20ffe7ed6a9b was the first fully successful alpha19 APK build.
- run 35452512452 / source 1b4d84a0194e48870da8772e51444571817e52b0 is the final documented build after CI paths-ignore cleanup.

## HISTORICAL ALPHA18 BASELINE

Alpha18 established the no-synthetic-field architecture:
- real PDF vector field candidates backed by source path IDs;
- order dimensions demoted to supporting evidence/scaling;
- asymmetric layout-minus-constructor residual;
- CDR/AI/EPS/ZIP source preservation;
- manual fallback instead of fabricated geometry;
- alpha7 morphology retained;
- detailed field/alignment/residual diagnostics.

Alpha18 successful checkpoint:
- branch: printcheck-build-3.4.0-alpha18
- source commit: b645fd5077b64a053e926efbaf7fdedf30c0cdde
- Actions run: 35448700332
- artifact: PrintCheck_Android_3.4.0-alpha18_BUILD
- APK SHA-256: 61642079af67bd4dc85551d6e2a429b68152910f07ae5b8b4ed243db8f7b89fd
- source ZIP SHA-256: 00852094e3af6a217004f3768ff1023fb884b7a6fbec0152191d61af27fae2af

Alpha19 supersedes alpha18 for current development.

## IMPORTANT CURRENT LIMITATIONS

1. CDR parsing is not implemented.
   - CDR is downloaded/preserved with relation.
   - parse_status remains saved_not_parsed.
   - PDF is the active vector geometry source.

2. General scale/rotation registration is not implemented.
   - RasterMatcher remains fundamentally translation/same-scale.
   - preserved-colored-field fallback also derives translation.
   - alpha19 can infer physical 1:1 / 1:10 field scale after selection, but this is not the same as general image registration with uniform scaling/rotation.
   - non-uniform warp must remain forbidden.

3. Effects/gradients/transparency are not yet fully spatially scoped to isolated customer artwork.
   - live fonts are already scoped to artwork.
   - future work must ensure template-only effects never create customer-artwork errors.

4. Real-order color-field mapping still needs fixture validation.
   - alpha19 makes color evidence primary and uses application/order evidence for disambiguation.
   - real order 7966463 must be used to verify that the selected application/place resolves to the intended colored field in actual production PDFs.

5. CDR should become a true inspectable geometry source in a later version if feasible without requiring Corel or an external desktop converter on the Android device.

## NEXT IMPLEMENTATION PRIORITIES

Immediate next step:
1. Install/run alpha19 on control order 7966463.
2. Use “Сохранить диагностику”.
3. Upload the diagnostic ZIP.
4. Inspect field_candidates → selected_field → alignment → residual artwork for every position.
5. Fix the real cause of any wrong/manual result; never introduce a synthetic field fallback.

Then, based on real diagnostics:
6. Extend Models.Occurrence/RasterMatcher/GeometryAnalyzer for safe uniform-scale registration and, only if actual fixtures require it, rotation.
7. Keep non-uniform deformation forbidden.
8. Spatially scope effects/gradients/transparency strictly to detected customer artwork.
9. Continue improving designer-first visual evidence/report compactness.
10. Implement/assess CDR vector inspection without Corel dependency.

## CONTROL FIXTURES

### Order 7966463
Item/article mappings:
- 49164234 / 19555.303
- 49164235 / 19555.305
- 49164563 / 16274.303
- 49164564 / 16274.304
- 49164565 / 16274.305
- 49164582 / 15147.30

PDF constructors:
- 19555_4.pdf
- 16274_9.pdf
- 15147_25.pdf

CDR sources:
- 19555_5.cdr
- 16274_10.cdr
- 15147_26.cdr

Hoodie and polo are strong partial-template fixtures.
Cap is a harder registration case.

### Historical regression order
- order 7920509 / oid 7738671

Historical alpha14 false geometry examples that must never return:
- article 30114.30 incorrectly produced ~260.64 × 55.49 mm instead of ~5 × 5.5 cm;
- article 25900.61 incorrectly produced ~8.6 × 3.13 mm instead of ~5 × 0.5 cm.

These failures were caused by treating unrelated/general constructor geometry as the production field and then counting guide/dashed lines as artwork/small elements. Never reintroduce that behavior.

## VERSIONING RULE

Every new PrintCheck version must update:
- Android versionCode;
- Android versionName;
- every UI location displaying the version;
- artifact/archive/release names;
- README/PROGRESS as relevant;
- PRINTCHECK_HANDOFF.md;
- DEVELOPMENT_LOG.md.

## BUILD / DELIVERY RULE

Whenever practical deliver a ready installable Android/Windows artifact, not only source code.

Before declaring a version/checkpoint complete:
- source invariants pass;
- tests pass;
- Android/desktop compilation passes as applicable;
- artifact is collected;
- artifact integrity is checked;
- SHA-256 hashes are recorded;
- known limitations are explicit;
- handoff and development log are current.

## PERMANENT GIT DOCUMENTATION

Read these first in every new chat:
- printcheck-build/PRINTCHECK_HANDOFF.md
- printcheck-build/DEVELOPMENT_LOG.md
- printcheck-build/ALPHA19_MANIFEST.txt
- .ci/alpha19-result.txt

Source reconstruction:
- printcheck-build/prepare_alpha19.py

Android workflow:
- .github/workflows/printcheck-android-alpha19.yml

## STARTING A NEW CHAT

Before changing PrintCheck code in a new chat:
1. Read PRINTCHECK_HANDOFF.md completely.
2. Read DEVELOPMENT_LOG.md, especially its latest entries.
3. Read the current version manifest and .ci result.
4. Identify the latest authoritative source commit/run/artifact.
5. Regenerate/read the current implementation source from that commit before editing.
6. Continue from NEXT IMPLEMENTATION PRIORITIES.
7. Do not ask the user to repeat requirements already documented here.
8. Keep logging every meaningful change back to Git.


## PERSISTENT ANDROID UPDATE SIGNING — REQUIRED FROM ALPHA20 FORWARD

User requirement:
new test APKs must install over the currently installed PrintCheck build without uninstalling it and without losing app data.

Rules:
1. Keep Android applicationId exactly `ru.printcheck.android`.
2. Increment versionCode for every distributed build.
3. All alpha20+ update-compatible test APKs must use the same persistent signing identity.
4. Do not fall back to per-run/default CI debug signing for distributed artifacts.
5. CI must fail if the persistent alpha signing material or expected hashes are missing/mismatched.

Implementation:
- Git transport: `printcheck-build/NON_PRODUCTION_ALPHA_SIGNING.p12.b64`
- generated key file: `.printcheck-alpha20/signing/printcheck-alpha-test.p12`
- Gradle signing config: `alphaPersistent`
- certificate SHA-256 fingerprint:
  `82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11`

Transition limitation:
alpha19 predates this persistent signing identity, so moving from an already-installed alpha19 to the first persistent-signed alpha20 may require one final uninstall. Once the persistent-signed alpha20 is installed, later alpha builds are expected to update it in place.

Security:
this key is NON-PRODUCTION test signing material. Never promote it to production signing.


## ALPHA20 SIGNED BUILD CHECKPOINT

Canonical update-compatible alpha baseline:
- versionName: 3.4.0-alpha20
- versionCode: 340020
- applicationId: ru.printcheck.android
- source commit: 6a000b08878cee7cc82c59003758eb3f8d1e58f5
- GitHub Actions run: 35455256258
- artifact ID: 10588296469
- APK SHA-256: 712d7931a67c624f6582ee9e3c6dbf33a7bf6c3048c56866b0eb874f5668128e
- source ZIP SHA-256: 98b0d953480377e5ddb6bcc266e25ced8e5e0fe54c7ce99ee47c38e2b60881ba
- persistent alpha signing certificate SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

All alpha21+ builds must preserve the same applicationId and signer and increment versionCode. A build violating any of these conditions must not be distributed as an update-compatible alpha.


## ALPHA21 DEVELOPMENT DELTA — ARTWORK DETECTION AND FULLSCREEN PHONE EVIDENCE

Alpha21 is built strictly on the persistent-signed alpha20 baseline.

Primary detection changes:
- local field-centered registration refinement before template subtraction;
- background-aware ArtworkDiffLogic;
- selected-template subtraction no longer removes a legitimate dominant/solid customer color merely because it is common;
- deletions from the template remain non-artwork;
- nearby matching template FEATURE suppresses edge residue only where appropriate;
- safe uniform-scale+translation recovery from preserved colored fields;
- significant non-uniform scaling remains rejected;
- separate artwork_file evidence explicitly shows what PrintCheck considers the customer application.

UI:
- larger inline evidence;
- fullscreen immersive viewer on tap;
- pinch-to-zoom, pan, double-tap zoom, up to 8×.

Update compatibility:
- versionCode 340021;
- same applicationId ru.printcheck.android;
- same persistent alpha signer as alpha20 is mandatory and checked both in generator and CI.

Tests before CI:
- core 60/60;
- audit 20/20.

Limitations:
- rotation registration not yet implemented;
- scaled-registration small-element morphology is temporarily manual until scale-aware;
- CDR parsing not implemented;
- real-order improvement must be verified with new diagnostics rather than inferred from unit tests.


## ALPHA21 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha21
- versionCode: 340021
- applicationId: ru.printcheck.android
- source commit: 0ea3f268bdf965b9fb299b9ad875e7f58a35c352
- GitHub Actions run: 35459832052
- artifact ID: 10589092459
- artifact name: PrintCheck_Android_3.4.0-alpha21_FINAL2_BUILD
- artifact digest: sha256:c012abcb19c6e77ca73f1f6e8a299dc02d82fc84bf22ccf4302bd03a958f0290
- APK SHA-256: d80340c44e396fcc551a301b46970df0a60866b48a6a3c6a149af1414539725f
- source ZIP SHA-256: 48b975a6f7f3c8ea08bdc3327c0d49f40b784d5caa54fb0221269c00c978f84b
- persistent signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha21 is update-compatible with the persistent-signed alpha20 baseline.

Key alpha21 behavior:
- local field-centered registration refinement;
- background-aware selected-template subtraction;
- dominant solid customer artwork retained;
- deleted template content excluded from artwork;
- safe uniform-scale+translation field-anchor recovery;
- non-uniform scaling remains forbidden;
- separate artwork_file evidence;
- larger result previews;
- immersive fullscreen evidence viewer with pinch, pan, double tap and up to 8× zoom.

Next required real fixture:
order 7920509 with saved diagnostics, comparing isolated artwork evidence position by position.


## ALPHA22 — HIGH-RES ARTWORK ROI IS NOW REQUIRED

Reason:
alpha21 diagnostics from order 7920509 proved that primary artwork segmentation reused global coarse rasters at only 65–100 dpi. This is insufficient for reliable 0.2–0.3 mm boundaries and can cause wrong artwork masks.

Mandatory alpha22+ architecture:
- coarse adaptive DPI is allowed only for whole-page discovery/registration;
- once a real selected application field is known, artwork segmentation must rerender the field ROI at a dedicated higher DPI;
- target DPI is 900;
- prefer at least 300 dpi when memory allows;
- enforce an 8M-pixel ROI budget instead of rendering whole giant pages at high DPI;
- high-res local registration and selected-template subtraction are authoritative for artwork detection;
- physical artwork measurements come from the high-res mask;
- saved artwork evidence comes from the high-res ROI;
- diagnostics must show coarse_geometry_dpi and artwork_analysis_dpi separately.

Observed alpha21 coarse DPI on control order 7920509:
15637=100, 17488.30=90, 19727.02=100, 30114.30=79, 15423.10=69, 17893.30=65.

Separate issue:
25900.61 produced no geometry at all in alpha21. Do not assume high-res ROI alone fixes it; if still missing after alpha22, inspect selected-application mapping/alignment independently.

Update compatibility:
- alpha22 versionCode 340022;
- applicationId stays ru.printcheck.android;
- same persistent NON-PRODUCTION alpha signer as alpha20/alpha21 is mandatory.


## ALPHA22 CANONICAL BUILD CHECKPOINT

- versionName: 3.4.0-alpha22
- versionCode: 340022
- applicationId: ru.printcheck.android
- source commit: f5c7ca5ae083d85731c8d16e3e941c2d316a50d2
- GitHub Actions run: 35461116755
- artifact ID: 10589449659
- artifact: PrintCheck_Android_3.4.0-alpha22_FINAL_BUILD
- APK SHA-256: 2dfee546036afc18dd88ddd386f93f5693a11116f3ee9d3266fc206574c855af
- source ZIP SHA-256: b514fd73df4c4e9893125b105ab1a19c5dfded1b0f299d8d1feca93df68aa5f0
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha22 is update-compatible with persistent-signed alpha21.

Authoritative alpha22 artwork pipeline:
coarse page discovery -> real selected colored field -> high-res ROI render -> high-res local registration -> high-res selected-template subtraction -> high-res physical measurement/evidence -> coarse-coordinate projection only for legacy overlays/font scoping.

Do not regress primary artwork segmentation back to RasterPdfIndexer.commonDpi.


## ALPHA23 PERFORMANCE CONTRACT

alpha22 high-res quality stays, but its exhaustive computation is forbidden.

Required pipeline:
- whole-page discovery: coarse adaptive raster;
- artwork segmentation: dedicated high-res ROI, target 720 dpi, >=300 dpi when feasible, 4M-pixel budget;
- high-res registration: cached reference support samples + coarse-to-fine offset search;
- hot raster diff/background sampling: bulk row reads, not millions of Bitmap.getPixel() calls;
- small-element analyzer reuses the artwork high-res mask when >=4 px/rule;
- additional fine render only for rules that truly need it, tight around detected artwork, target ~6 px/rule, <=1600 dpi, 2.5M-pixel budget;
- result.json must retain timing_coarse_render_ms / timing_artwork_highres_ms / timing_small_elements_ms / timing_geometry_total_ms.

Do not restore alpha22 exhaustive full-radius high-DPI registration or unconditional second high-res render.

Update compatibility:
- versionCode 340023;
- same applicationId and persistent signer as alpha20–alpha22.


## ALPHA23 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha23
- versionCode: 340023
- applicationId: ru.printcheck.android
- source commit: 85ec610f83247ae3246238a736e87e8baf948883
- GitHub Actions run: 35464170600
- job ID: 105953218866
- artifact ID: 10590573476
- artifact: PrintCheck_Android_3.4.0-alpha23_FINAL_BUILD
- APK SHA-256: 2afac3b7a11cc75f375abd35e29f0ae99bc4af81c08e65f48957b3e490b0710c
- source ZIP SHA-256: b5fed7c7ac9085862d4b44bb6cbfbe375ada0c711eab5e5e12d4ce4743c339d8
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha23 is update-compatible with alpha22.

Performance architecture:
- high-res artwork quality retained;
- target 720 dpi / 4M pixel main ROI;
- cached registration support samples;
- coarse-to-fine local registration;
- bulk pixel row reads;
- small-element pass reuses high-res artwork mask whenever resolution is sufficient;
- otherwise renders a tight artwork crop only, capped at 1600 dpi / 2.5M pixels;
- per-stage timing diagnostics are mandatory for future performance work.


## ALPHA24 — PHYSICAL REFERENCE RULER BEFORE SMALL-ELEMENT DETECTION

User-mandated measurement order:
**real field -> reference ruler -> artwork physical size -> small elements**.

This order is mandatory. Do not run automatic small-element morphology using renderer DPI alone.

Reference-ruler rules:
- derive pixels/mm from the observed real selected application field;
- selected application physical dimensions are allowed as the named physical reference only when consistent with observed/vector field geometry;
- when both order-selected dimensions and vector field dimensions exist, disagreement >12% blocks automatic morphology;
- X/Y calibration anisotropy >5.5% blocks automatic morphology;
- invalid ruler => manual small-element check, no automatic issue circles.

Authoritative fine-artwork rule:
- exact selected-application-template is authoritative;
- sufficiently agreeing selected application binding (>=0.55) may also be authoritative;
- a general constructor fallback can help position the field but is NOT sufficient by itself for automatic small-element issue marking.
- This rule was added because alpha23 article 15423.10 had reference_role=constructor, application_field_agreement=0, and falsely marked constructor service text/lines as hundreds of small-element violations.

Diagnostic requirement:
reference_ruler, calibrated artwork size, measurement_source and measurement_sequence must remain visible in result JSON/evidence.

Authentication UI:
- compact 70×30dp Вход/Выход button in upper-right header;
- actual session state detected via gifts.ru website session/logout link;
- logout clears PrintCheck WebView cookies/session locally;
- login remains website-only.

Alpha23 performance architecture MUST remain:
720dpi/4M main high-res ROI, cached/coarse-to-fine registration, calibrated mask reuse/tight fine rerender.

Version/update:
- alpha24 versionCode 340024;
- applicationId unchanged;
- same persistent non-production alpha signer required.

Separate unresolved fixture:
25900.61 had no geometry in alpha23. Do not conflate that mapping/alignment failure with reference-ruler calibration.


## ALPHA24 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha24
- versionCode: 340024
- applicationId: ru.printcheck.android
- source commit: 5df005250ff34beea815d059da163495ccb834f4
- GitHub Actions run: 35466938823
- job ID: 105960898373
- artifact ID: 10590694977
- artifact: PrintCheck_Android_3.4.0-alpha24_FINAL_BUILD
- APK SHA-256: a6de421a100a7ee677a3f58066d9890104da7ea91214bc5eac2662556e103ea7
- source ZIP SHA-256: 3ae49bfbac57e2b20edfea4c9ae6ecc2d61e1a95239478a806a3e8f7bc872cf4
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha24 is update-compatible with alpha23.

Authoritative measurement sequence:
real selected field -> reference ruler -> calibrated artwork size -> small-element morphology.

Automatic small-element markings are forbidden when:
- reference ruler is invalid;
- selected-size/vector-field disagreement >12%;
- X/Y scale disagreement >5.5%;
- fine-artwork reference is only an unconfirmed general constructor fallback.

UI:
compact 70x30dp top-right authentication button; text reflects session state as Вход/Выход.


## ALPHA25 — SAME-COLOR TECHNICAL MORPHOLOGY CONTRACT

Authoritative user rule:
- positive technical element = object/letter/stroke of ONE color;
- negative technical element = gap/reversal between or inside geometry of that SAME color;
- cross-color distance is never a negative element.

Required processing order:
real selected field
-> reference ruler
-> calibrated artwork physical size
-> visible color separation
-> per-color positive / negative / single-object analysis.

Do NOT restore a combined black/white binary artwork mask as the technical small-element model.

Per-color analysis requirements:
- split only the already-isolated customer artwork;
- process every stable visible color independently;
- anti-alias shades should remain with their parent flat color where possible;
- positive check measures physical object/stroke thickness for that color;
- negative check includes enclosed counters/reversals and too-small gaps only between disconnected components of that same color;
- minSingleElementMm checks isolated objects/letters per color independently;
- distances between different color layers are ignored for the negative rule.

Diagnostics must retain:
- color_analysis_mode
- color_layer_count
- color_layers[]
- cross_color_negative_gaps_ignored=true
- layer id/color on issue examples.

Continuous-tone safety:
- if no stable color layers are found, or >8 stable visible layers are needed, technical small-element automation becomes MANUAL;
- never produce hundreds of pseudo-color warnings by quantizing a photograph/gradient.

Important limitation:
ArtworkColorLayerLogic is rendered-visible-RGB separation, not native PDF CMYK/Pantone/spot parsing.
Future higher-fidelity color semantics should come from PDF object/color-space parsing, especially for White ink or spot colors invisible/ambiguous after rasterization.

Retained alpha24/alpha23 contracts:
- reference ruler calibration first;
- ruler mismatch/anisotropy blocks morphology;
- unconfirmed constructor fallback cannot create automatic small-element issues;
- 720dpi/4M high-res performance architecture;
- top-right Вход/Выход auth UI;
- persistent signer/update compatibility.

Version:
- alpha25 versionCode 340025;
- applicationId ru.printcheck.android;
- same persistent NON-PRODUCTION alpha signer required.

Separate unresolved fixture:
- 25900.61 geometry/mapping remains separate from color morphology.


## ALPHA25 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha25
- versionCode: 340025
- applicationId: ru.printcheck.android
- source commit: 9a75468eb2e0831eeba2b45331771909f5213e49
- GitHub Actions run: 35468997685
- job ID: 105966410774
- artifact ID: 10592755504
- artifact: PrintCheck_Android_3.4.0-alpha25_FINAL_BUILD
- APK SHA-256: 5eb7ad9dcfa31e4aa6489da388c01accd281e21a8eb676241c3b6f4db731288f
- source ZIP SHA-256: 9c8950512caa8c39e8c9e0564da8fc763e7837ca0b119de4de7a89a630beec28
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha25 is update-compatible with alpha24.

Authoritative small-element sequence:
real field
-> physical reference ruler
-> calibrated artwork size
-> visible color layers
-> independent positive / negative / single-object morphology PER COLOR.

Cross-color distances must remain ignored.
Continuous-tone/unstable visible separation must remain manual, not forced into pseudo-color technical verdicts.


## ALPHA26 — INTERSECTION-SAFE CENTERED FEATURE CONTRACT

Authoritative requirements:
1. A contact/intersection between DIFFERENT colors is never by itself a technical small element.
2. Technical morphology is performed on reconstructed SOLID geometry of one color, not on the thin layout-minus-template contour.
3. The report marker is centered on the real detected feature:
   - positive narrow region -> actual narrow-region center;
   - same-color negative gap -> physical gap midpoint;
   - single small object -> connected-component centroid.

Required pipeline:
diff seed
-> stable visible color
-> reconstruct full same-color connected solid
-> exclusive owner map
-> cross-color intersection/contact exclusion
-> per-color local-thickness / same-color-gap / single-object measurement
-> centered markers.

Do NOT regress to using the diff contour as the positive object.

Algorithmic basis:
- distance-transform / medial-ridge concept for local width;
- connected components / centroids for objects;
- nearest same-color components through unowned space for gap centers;
- other colors are barriers in negative-gap propagation.

Current alpha26 implementation intentionally avoids adding OpenCV; concepts are implemented on existing masks for APK size/control.
Future higher-fidelity direction: use existing PDFBox PDFGraphicsStreamEngine to recover native vector paths and stroking/non-stroking color state (CMYK/RGB/spot/White where available), then use raster reconstruction only as fallback.

Diagnostics:
- cross_color_intersections_excluded=true
- feature center_x / center_y
- feature_kind
- marker_style=centered_features_v6_intersection_safe_reference_ruler

Retained:
- reference ruler before morphology;
- per-color same-color-only semantics;
- constructor authority guard;
- 720dpi/4M performance architecture;
- top-right auth UI;
- persistent update-compatible signer.

Version:
- alpha26 versionCode 340026;
- app id unchanged;
- same persistent non-production alpha signer required.


## ALPHA26 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha26
- versionCode: 340026
- applicationId: ru.printcheck.android
- source commit: 6828caa6b1ba4cfb51c511ef5676487351e1ed91
- GitHub Actions run: 35470975423
- job ID: 105971763485
- artifact ID: 10592957794
- artifact: PrintCheck_Android_3.4.0-alpha26_FINAL_BUILD
- APK SHA-256: e4d9a48c0e95420002ac7f214e76780351502c3bd2c3d5925e48e653ff6e6feb
- source ZIP SHA-256: 473bc28271ba3bb614b07cb330c7dd10ac0a481556b43f3156a892277da43fad
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha26 is update-compatible with alpha25.

Authoritative morphology:
diff is seed only -> reconstruct full same-color solid -> exclusive color ownership -> exclude cross-color contacts -> distance/medial positive widths + same-color gaps + single objects -> centered evidence markers.

Do not regress markers to bbox centers or diff-edge contours.


## ALPHA27 — RULE-SIZED HOLLOW MARKER CONTRACT

User-visible marker contract:
- NO center dot;
- NO color swatch in center;
- NO crosshair;
- marker is a hollow circle only;
- OUTER circle diameter equals the minimum allowed physical size of the rule being visualized.

Per check:
- positive circle diameter = effective positive rule mm;
- negative circle diameter = effective negative rule mm;
- single-object circle diameter = minSingleElementMm.

Scaling:
- use the calibrated reference-ruler pixels/mm, never renderer DPI alone;
- multiply by evidence output scale;
- compensate stroke inward so the visible outer diameter remains the target rule size.

Do not restore:
- fixed 18px radius;
- central dot/swatch;
- central crosshair;
- bbox-sized marker.

Retained from alpha26:
- centers remain the actual feature centers/midpoints/centroids;
- cross-color intersections are excluded;
- same-color technical morphology only;
- diff is seed only, not measured geometry;
- reference ruler precedes morphology;
- 720dpi/4M performance architecture.

Canonical build:
- versionName 3.4.0-alpha27
- versionCode 340027
- applicationId ru.printcheck.android
- source commit c902251bec095e98756537406485c263ffaf761b
- GitHub Actions run 35492770823
- job 106030431055
- artifact ID 10599169903
- APK SHA-256 94844c23ccd2f3421aca7048fd64902a4efc7515f69d6adb82a56452194f7f62
- source ZIP SHA-256 8961ad7ec331762077118d838fc956da1113e4a3d91c02decd971e41aa5ef038
- signer SHA-256 82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha27 is update-compatible with alpha26.


## ALPHA28 — EXPANDABLE RESULT TREE CONTRACT

User-facing hierarchy:
**order number -> article -> brief checklist -> detailed checklist**.

UI requirements:
- PrintCheck name and version are on one line;
- version is small/muted;
- queue button text is exactly "Заказы ожидающие проверку";
- long queue button must remain readable on phone (full-width row).

Tree behavior:
- single checked order starts expanded;
- articles start collapsed;
- brief checklist is the first lightweight content under each article;
- detailed checklist is separately expandable;
- batch order nodes start collapsed;
- order PDF report belongs inside the order node;
- article PDF report belongs inside the article's brief checklist.

Brief checklist:
- compact statuses only;
- no long check detail text;
- method/place/alignment/small-elements summary included.

Detailed checklist:
- all evidence images, measurements, rules, full checks, files and comparisons.
- must be populated lazily on first open so batch results do not eagerly allocate every preview.

Do not regress alpha27 technical behavior:
- marker diameter = physical rule;
- no marker center dot/crosshair;
- alpha26 intersection-safe same-color morphology;
- reference-ruler calibration;
- 720dpi/4M performance architecture.

Version:
- alpha28 versionCode 340028;
- applicationId unchanged;
- same persistent non-production alpha signer required.


## ALPHA28 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha28
- versionCode: 340028
- applicationId: ru.printcheck.android
- source commit: 5f83c231ca78256f17e60fb1a80ec8fe2418c7b8
- GitHub Actions run: 35494396666
- job ID: 106034713262
- artifact ID: 10600521672
- artifact: PrintCheck_Android_3.4.0-alpha28_FINAL_BUILD
- APK SHA-256: b910d4208513169ecadf8025ce335e9dde1bf1c94e5e3065e14ea9da2ca31bdb
- source ZIP SHA-256: 71be0d3a78110905dbfd0766c8bc6e7cc2210f331420b2ffde99592bb0356b64
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha28 is update-compatible with alpha27.

UI contract:
- PrintCheck + small version on one horizontal line;
- queue button exact text: Заказы ожидающие проверку;
- result tree: order -> article -> brief checklist -> detailed checklist;
- batch orders collapsed initially;
- detailed checklist lazy-loads evidence only on first open.

Technical preflight remains alpha27/alpha26 unchanged.


## ALPHA29 — COMPACT RESULT TREE CONTRACT

Header:
- one horizontal line only: PrintCheck + small version + "read-only";
- do not restore the separate "безопасная проверка read-only" subtitle.

Order node:
- no trailing article/preflight status badge at order level;
- aggregate count text is allowed;
- future order status, if introduced, must describe the whole order rather than reuse a position status.

Brief checklist:
- dense two-column grid on phone;
- "Найденное нанесение" belongs in the brief checklist;
- found-artwork preview loads lazily on first ARTICLE expansion;
- tapping it still opens fullscreen zoom;
- article PDF report remains in brief checklist.

Detailed checklist:
- do not duplicate "Найденное нанесение";
- retain remaining evidence, measurements, technical requirements, all checks, files and comparisons;
- retain lazy loading.

Do not regress technical behavior from alpha28/27/26:
- physical-rule marker diameter;
- no center dot/crosshair;
- cross-color intersections excluded;
- same-color morphology;
- reference ruler;
- 720dpi/4M performance pipeline.

Version:
- alpha29 versionCode 340029;
- applicationId unchanged;
- same persistent non-production alpha signer required.


## ALPHA29 CANONICAL SUCCESSFUL BUILD CHECKPOINT

- versionName: 3.4.0-alpha29
- versionCode: 340029
- applicationId: ru.printcheck.android
- source commit: 0870044ae89f075db6d7de64a3d19f74e30ca856
- GitHub Actions run: 35507611527
- job ID: 106069963490
- artifact ID: 10604612015
- artifact: PrintCheck_Android_3.4.0-alpha29_FINAL_BUILD
- APK SHA-256: c1d3693ede92c4c4e512a2343bc9ab4843494db303272745d07b21cf1730858f
- source ZIP SHA-256: a3dfcc6eb40b3f2e5cf6236a7208193545d83d1d0130c7efca613d769d5a44f0
- signer SHA-256:
  82:25:40:C7:38:6D:19:3F:D3:DE:C1:65:62:03:98:57:23:06:A2:0B:26:40:B8:76:91:81:59:77:66:A4:5D:11

Alpha29 is update-compatible with alpha28.

UI contract:
- one-line header: PrintCheck + small version + read-only;
- no status badge on order node;
- article status badge retained;
- brief checklist is dense two-column;
- found-artwork evidence belongs to brief checklist and lazy-loads on first article open;
- no duplicate found-artwork in detailed checklist.

Technical preflight remains alpha28/27/26 unchanged.
