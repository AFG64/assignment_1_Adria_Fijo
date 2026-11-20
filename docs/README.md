# Documentation index

The current application is Assignment 2's static UI and two SQL-backed services.
Start with the [repository README](../README.md) for live URLs, compose startup,
test commands and the folder map. Commands in technical guides run from the
repository root unless stated otherwise.

## Current technical guides

| Topic | Document |
|---|---|
| Local setup, configuration, SQL checks and copied-data transfer | [Local development](assignment-2/LOCAL_DEVELOPMENT.md) |
| Browser operations mapped to service endpoints | [API transition](assignment-2/API_TRANSITION.md) |
| Visit/deletion ordering, partial failure and safe retry | [Service coordination](assignment-2/SERVICE_COORDINATION.md) |
| Static UI behavior, configuration and verification | [Static UI](assignment-2/STATIC_UI.md) |
| Initial Azure setup, main releases and recovery commands | [Azure operations](assignment-2/AZURE_OPERATIONS.md) |
| Actual Azure names, roles, settings and service origins | [Azure readiness/inventory](assignment-2/AZURE_READINESS.md) |
| Changes superseding the original Azure contract | [Requirement updates](assignment-2/REQUIREMENT_UPDATES.md) |
| Official system schema source and compatibility | [System schema](assignment-2/SYSTEM_SCHEMA.md) |

Machine-readable contracts remain at the assignment-required paths:
[system.yaml](../system.yaml), [official schema](../system.schema.json),
[restaurant OpenAPI](../services/restaurants/openapi.yaml) and
[dining OpenAPI](../services/dining/openapi.yaml). Database schemas are defined by
each service's versioned migrations; applied migrations are never edited.

## Course references

The current full ten-page brief is the user-supplied
assignment_2_instructions/Assignment_2.pdf. Read it with the
[updated requirements](assignment-2/REQUIREMENT_UPDATES.md) and the
[supplied Azure deployment guide](assignment-2/AZURE_DEPLOYMENT_GUIDE.txt).
The searchable [original brief](assignment-2/BRIEF.txt) is historical; the current
brief and guide supersede its shared-class subscription/Static Web App plan.
The root system.schema.json is the supplied official schema, not a custom one.

## Assignment 1 and student-owned deliverables

- [Legacy application instructions](assignment-1/README.md).
- [Original brief](../assignment_1.md), [project plan](PROJECT_PLAN.md),
  [domain boundaries](DOMAIN_BOUNDARIES.md) and [SQLite schema](SCHEMA.md).
- [Existing Assignment 1 report source](REPORT.md) and
  [PDF](../output/pdf/picky-assignment-1-report.pdf).
- [Architecture decisions](../ADR.md) and [AI usage records](../AI_USAGE.md).

The reports and process records are student-owned and are not rewritten by these
technical guides. The local working roadmap/instructions remain local; consult
them when continuing the assignment. Migration 002 is paused until the populated
Azure baseline and the student's before evidence are explicitly confirmed.
