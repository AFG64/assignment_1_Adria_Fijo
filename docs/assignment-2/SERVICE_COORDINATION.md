# Service coordination — milestone 5

The APIs coordinate over HTTP; neither service connects to the peer database.
No schema change, applied-migration edit or migration 002 is needed by this flow.

## Record a visit

1. Dining validates the JSON fields before any peer side effect.
2. In its own SQL transaction, dining acquires an exclusive application lock for
   the external saved ID, with a 2-second lock wait. All dining writes for that
   saved ID (including cleanup, items and bills) use the same lock.
3. Dining GETs the restaurant saved entry and PUTs its status to visited. Both
   requests have an explicit timeout and validate the returned saved ID; PUT
   confirmation must say visited.
4. Dining inserts the visit, reads its response and commits. Only then returns 201.

This POST is deliberately non-idempotent. The peer client never retries requests
or follows redirects. A transport/peer failure returns 503 peer_unavailable,
rolls back dining and creates no visit. The restaurant status may already have
changed. If the own database write/commit cannot be confirmed, the response is
503 visit_outcome_uncertain: inspect history before resubmitting. These responses
set retryable=false. There is no durable request-key ledger or automatic
compensation. Manually marked visited status already exists in Picky without a
visit, so a conservative visited flag can remain after failure; the failure is
never presented as a recorded visit. GET/PUT timeouts after a successful remote
write are also treated as failures, not assumed success.

## Remove a saved entry

Restaurants commits removal of the saved row first, retaining the catalog row.
It then DELETEs dining history for that old saved ID. Dining takes its lock and
removes visits, with SQL cascading items and bill bytes. Cleanup is idempotent:
an empty history is still 204. Restaurants returns 204 only after confirmation.
Repeating a restaurant DELETE must still call cleanup when the saved row is
already absent; otherwise recovery after partial failure would be impossible.

If dining is unavailable, restaurants returns 503 cleanup_pending with
retryable=true. The saved row is gone but history cleanup is unconfirmed. Retry
the same DELETE with the original saved ID until 204; do not interpret a missing
saved row or an empty saved list as confirmed cleanup. SQL failures before or
during revocation may also be uncertain; repeating DELETE is safe. If the first
cleanup response is lost, repetition does not recreate or duplicate data.

This revoke-first order supersedes the initial draft contract's proposed
cleanup-first order. A successful re-save creates a different saved ID, and
cleanup of the old ID cannot delete the new entry's history.

## Concurrency and availability

The dining lock spans the final saved-entry validation/status update and local
visit write. If a create wins, a later successful cleanup deletes it. If deletion
wins first, restaurant validation/marking fails and dining rolls back. If saved
revocation happens during creation, cleanup waits for the dining lock and then
clears the old ID. Thus after successful 204 cleanup, no earlier overlapping
create may later insert orphan visits. This assumes all dining writers use this
lock and ordinary callers cannot insert directly into the database.

With one synchronous worker per service, opposing requests can temporarily
wait on each other. Peer timeouts and the lock wait bound the blocking operations;
a visit may roll back and deletion may require a repeat. This is an availability
trade-off, not a distributed transaction. No restaurant SQL transaction is held
while waiting for dining. Own database health and history/catalog reads never
call the peer. The peer timeout defaults to 2 seconds (configured through the
service-specific *_TIMEOUT_S setting, valid range >0 to 10 seconds); response
bodies are capped at 64 KiB. The timeout applies to blocking socket operations,
not a guaranteed end-to-end deadline for the entire user flow.

SQL lock ownership/release follows [sp_getapplock](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-getapplock-transact-sql).
HTTP blocking-operation timeouts follow [urllib.request](https://docs.python.org/3/library/urllib.request.html).

## Verification and personal records

Unit tests cover input validation, peer 404/failure/timeout, unexpected response
shape, identity/status mismatch, rollback after marking, explicit uncertain
writes and retryable deletion. `python scripts/check_seam.py` checks both real
HTTP APIs and SQL: visit/status, stopped peers, own health/history availability,
partial deletion recovery, duplicate cleanup and concurrent create/delete. CI
runs it after the existing SQL tests. Test data is synthetic and cleaned up.

The user writes AI usage and ADR-9, and records the ordering/partial-failure
consequences in ADR-6/7 as appropriate. Tests described here are technical checks;
user-owned failure screenshots, CI run links and report evidence remain pending.
