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
