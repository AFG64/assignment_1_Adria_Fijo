# Populated Azure 001 baseline before migration 002

Captured from the live system at 2026-11-26T18:37:55.232557+00:00.
Deployed source: `0d313d7b08ea4ba5ed79b4f47ba7ca660c37ad6a`.
Live page: https://afijoieu2024ui.z28.web.core.windows.net/#/restaurants/15

## Visible state and downloaded bill

- [Full restaurant and visit page](restaurant-before.png).
- [Visit, ordered item and bill control](visit-before.png).
- [Original downloaded PDF](baseline-bill.pdf) and [rendered preview](bill-preview.png).
- Browser download matched the saved PDF byte for byte (648 bytes).

Restaurant 15 / saved 1 / visit 1 / item 1 / bill 1 are retained. The visit is dated
2026-11-01, rated 4, and the saved entry is visited. Baseline soup has quantity 2
and unit price 3.50. The item response has no line_total field at this version.
Bill SHA-256: `abc73e5230c4d7659f95e0f4871c4e1aa3d77f16d49d2c2bea3c469e46ead63e`.

## Machine-readable captures

- [Capture time, version, IDs and original migration checksums](capture.json).
- [Restaurant](restaurant.json), [saved entry](saved-entry.json) and [visit history](visit-history.json).
- [API health](health.json), [UI release](release.json) and [HTTP response metadata](response-metadata.json).
- [Original 001 startup and subsequent no-op migration logs](startup-migrations.tsv), with [raw query result](startup-migrations.json).
- [First successful application deployment metadata](initial-deployment.json) and [latest successful deployment metadata](latest-deployment.json).

Initial deployment: https://github.com/AFG64/assignment_1_Adria_Fijo/actions/runs/44640494444
Latest deployment: https://github.com/AFG64/assignment_1_Adria_Fijo/actions/runs/44720653840

The startup log timestamps are UTC. They show 001_init.sql applied once in each
service and later startups applying zero migrations. Capture.json records the
unchanged release checkpoint: maximum_version 1 and before_evidence_confirmed false.
This bundle is awaiting user review/confirmation before migration 002 is created.

SHA256SUMS records file integrity for this bundle.
