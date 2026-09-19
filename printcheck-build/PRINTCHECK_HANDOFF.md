# PrintCheck — canonical handoff and development protocol

Last updated: 2026-09-19
Repository: tohaa28/helpdesk
Current implementation line: Android 3.4.0-alpha18
Current build branch: printcheck-build-3.4.0-alpha18

## STRICT CONTINUITY RULE

This file is the permanent Git-backed handoff for PrintCheck. It must be updated whenever behavior, architecture, rules, file mapping, diagnostics, test expectations, build process, versioning, or known limitations change.

A new chat must be able to continue development from Git without reconstructing decisions from memory.

For every meaningful change:
1. Update code in Git.
2. Update DEVELOPMENT_LOG.md with what changed and why.
3. Update this handoff if the change affects canonical behavior, architecture, rules, limitations, build instructions, or next steps.
4. Record tests performed and their result.
5. Record the exact branch/commit and produced artifacts when available.
6. Never rely on chat-only context for an implementation decision.

No release is considered complete until the documentation above matches the actual code.

## PRODUCT PURPOSE

PrintCheck checks customer artwork against:
- the actual order data;
- the constructor/template for the ordered article;
- the exact application method selected by the customer;
- the exact application place selected by the customer;
- the technical requirements for that application method.

The output must be short, structured, understandable to a technical designer, and visually explain what was found and what is wrong.

## CANONICAL CHECKING ALGORITHM — USER CONFIRMED 2026-09-19

### 1. Read the order page

For every ordered item obtain and preserve:
- article;
- item ID / item relation when available;
- selected application method;
- selected application place;
- relations between the item and its layout/template files.

Do not guess application type or place from filenames when the page contains the relation.

### 2. Download source files

Download and preserve:
- customer layouts;
- templates / constructors in PDF;
- templates / constructors in CDR;
- all useful relation metadata from the page.

PDF and CDR must remain associated with the exact article / item / template relation from the order page.

### 3. Find the customer-selected application field in the template

The application field exists inside the template and is always highlighted by color.

Primary task:
- identify the color-highlighted field that corresponds to the application method and application place selected by the customer;
- use the real geometry from the template.

Critical rule:
- DO NOT construct a synthetic field from width/height values from the order;
- DO NOT choose an arbitrary rectangle only because its dimensions look plausible;
- dimensions from the order may only be supporting verification.

The field color is the principal signal and must become the core of the next implementation line.

### 4. Compare template and customer layout

Register the customer layout against the correct full template and determine whether the artwork occupies the correct application field.

Partial template deletion is allowed.

If the customer/designer removed most of the template but the relevant application field is preserved, this is NOT an error.

The application must not require an arbitrary percentage of the whole template to remain.

Use whatever retained template information is sufficient to establish the field and artwork position.

Template service graphics are not customer artwork:
- field outline;
- product outlines;
- guides;
- labels;
- technical lines;
- other constructor/template objects.

### 5. Check the actual artwork against technical requirements

After the real artwork has been separated from template content, check only that artwork against the requirements of the exact application method selected by the customer.

Examples include, where relevant:
- live fonts;
- gradients;
- transparency;
- prohibited effects;
- minimum positive elements;
- minimum negative elements / knockouts;
- allowed size;
- resolution;
- technology-specific constraints.

Requirements belonging only to the template must not cause a customer-artwork failure.

## REPORT / UX REQUIREMENTS

The result must not be primarily a technical log.

For each item show a compact human-readable summary:
- article;
- application method;
- application place;
- template found / not found;
- field found / not found;
- placement correct / incorrect / manual review;
- dimensions;
- technical-rule violations;
- final status.

Visual evidence must be large and understandable:
- show the relevant template/product area;
- show the selected colored application field;
- show detected artwork;
- mark violations with clear circles/arrows;
- if placement is wrong, show both the actual and expected region clearly.

Diagnostics must still be available separately and in detail.

## FONT RULE

Live fonts are forbidden only in the actual customer artwork.

Text in:
- template;
- constructor;
- service labels;
- areas outside the actual application

must not cause an artwork-font error.

## CURRENT ALPHA18 STATE

Alpha18 implemented a real-vector-field architecture for PDF constructors and removed synthetic order-size field construction.

Implemented:
- PDF constructor vector inspection via pdfbox-android;
- candidates backed by real PDF path IDs;
- order dimensions used only as evidence/scaling;
- asymmetric layout-minus-constructor residual logic;
- preservation of CDR/AI/EPS/ZIP constructor sources;
- manual fallback instead of inventing geometry;
- alpha7-style positive/negative small-element morphology retained;
- detailed field/alignment/residual diagnostics;
- UI wording around “real constructor field”.

Current alpha18 build:
- branch: printcheck-build-3.4.0-alpha18
- successful source commit: b645fd5077b64a053e926efbaf7fdedf30c0cdde
- successful Actions run: 35448700332
- successful artifact name: PrintCheck_Android_3.4.0-alpha18_BUILD
- APK SHA-256: 61642079af67bd4dc85551d6e2a429b68152910f07ae5b8b4ed243db8f7b89fd
- source ZIP SHA-256: 00852094e3af6a217004f3768ff1023fb884b7a6fbec0152191d61af27fae2af

## IMPORTANT ALPHA18 LIMITATIONS

These are not to be forgotten in future chats:

1. CDR files are preserved but not parsed.
   Current status: saved_not_parsed.
   PDF is the active geometric source.

2. Field discovery in alpha18 is still candidate/scoring based.
   The newly confirmed canonical rule is stronger:
   the target field is color-highlighted in the template and field color must become the primary detector.

3. RasterMatcher still fundamentally assumes translation / same-scale registration.
   Uniform scale and rotation registration are not generally implemented.
   Non-uniform warp is not desired.

4. Alpha18 still contains legacy-style whole-template integrity heuristics such as constructor coverage.
   Canonical behavior now says missing template content is acceptable if the target field is preserved and placement can be established.
   Therefore whole-template coverage must not be a blocking requirement.

5. Application-template and order dimensions may support identification but must never synthesize the production field.

## NEXT IMPLEMENTATION PRIORITIES

1. Replace/augment generic rectangle candidate scoring with explicit colored-field detection from template geometry.
2. Determine how field color maps to selected application/place using actual order/template evidence.
3. Make partial-template cases succeed when the target field remains even if most of the template is deleted.
4. Extend registration safely for uniform scale and, if needed by real fixtures, rotation.
5. Preserve the rule that non-uniform deformation is not accepted.
6. Continue isolating template content from customer artwork before running technical checks.
7. Add real CDR parsing/inspection path when feasible without requiring Corel on the Android device.
8. Keep rich diagnostics and designer-first visuals.
9. Validate using real control orders, especially 7966463 and historical 7920509.

## CONTROL FIXTURES

Order 7966463:
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

Historical regression fixture:
- order 7920509 / oid 7738671

Never reintroduce synthetic geometry that recreates the old false fields seen there.

## VERSIONING RULE

Every new PrintCheck version must update the version number:
- in the release/archive/artifact name;
- in Android versionName/versionCode;
- everywhere the UI displays the version;
- in handoff and change log documentation.

## BUILD / DELIVERY RULE

Whenever practical, deliver a ready installable artifact, not only source code.

Before declaring a build complete:
- source invariants pass;
- tests pass;
- compilation/build passes;
- artifact is collected;
- hashes are recorded;
- documentation is updated;
- known limitations are stated.

## STARTING A NEW CHAT

Before changing code in a new chat:
1. Read this file.
2. Read DEVELOPMENT_LOG.md.
3. Identify latest branch/commit/build.
4. Read the current implementation sources from that commit.
5. Continue from the documented next step.
6. Do not ask the user to repeat already documented requirements.
