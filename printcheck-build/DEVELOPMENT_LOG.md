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
