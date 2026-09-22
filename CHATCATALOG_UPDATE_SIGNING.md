# ChatCatalog AI update signing baseline

Stable update line starts at **0.3.1**.

- Application ID: `ru.chatcatalog.ai`
- Baseline versionName: `0.3.1`
- Baseline versionCode: `3`
- Release certificate SHA-256: `76:67:AD:22:27:50:0F:4E:94:4A:77:F1:5E:13:7B:5F:EE:10:F6:18:F5:90:1B:53:5B:65:6F:02:7D:BB:00:F8`

Future releases must keep the same application ID, use a higher versionCode, and be signed with the private release keystore kept by the user in `ChatCatalog-signing-key-backup-v2.zip`.

Do not commit the private JKS or its password to this public repository.

The older 0.2.0/0.3.0 debug builds were signed with a different debug certificate, so migration to 0.3.1 requires a one-time uninstall/install. Once 0.3.1 is installed, later APKs can be installed over it as updates while preserving app data.
