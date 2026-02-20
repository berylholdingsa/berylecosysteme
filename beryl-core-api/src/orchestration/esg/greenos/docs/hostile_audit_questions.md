# GreenOS Hostile Audit Questions

Version: 2026-02-17
Mode: skeptical external audit

## A. MRV integrity and reproducibility
1. How do you prove that two identical MRV payloads always produce the same verification hash?
2. What prevents hidden JSON key-order variations from changing reported MRV hashes?
3. How are decimals normalized so that language/runtime differences do not alter hash results?
4. Can an operator regenerate an MRV export with modified aggregation while preserving prior signature validity?
5. What exact checks decide `verified=true` on MRV verification?
6. How do you detect a methodology drift where payload remains unchanged but method registry changed?
7. How do you prevent exporting MRV when baseline references are incomplete?
8. How do you prevent exports when geographic scope and configured country factors are inconsistent?

## B. Double counting and replay resistance
9. What prevents duplicate insertion of the same trip event into the ledger?
10. If the same event is replayed five times, what guarantees no fivefold climate credit?
11. Can the same trip appear multiple times in one MRV export under different model versions?
12. What deterministic dedup rule is used and where is it encoded?
13. How do you prove dedup happened rather than asserting it in documentation?
14. What prevents two MRV exports for the exact same reporting window?
15. How is overlap conflict surfaced at API level for clients and auditors?
16. Could an attacker bypass dedup by changing only metadata while keeping trip semantics identical?

## C. Cryptographic non-repudiation
17. Why keep HMAC when Ed25519 exists, and what risk is covered by each?
18. How do you verify signatures externally without sharing any secret?
19. How do you expose public key material in a stable and institutionally anchorable way?
20. How do you verify the published public key itself (fingerprint trust)?
21. What happens if a signature is present but encoded in invalid base64?
22. Can verification succeed with wrong key version due to fallback behavior?
23. During key rotation, how do historical records remain verifiable?
24. What fails closed in production if cryptographic keys are missing or placeholders?

## D. Secret governance and operational security
25. Is GreenOS still environment-variable only, or does it support runtime secret backends?
26. How does Vault integration avoid leaking secrets in logs?
27. What is the behavior if Vault/KMS returns partial key material in production?
28. How do you prove secret status without exposing secret values?
29. Is the secret status endpoint public or restricted?
30. What explicit controls prevent startup with invalid signing configuration?

## E. Reliability, delivery guarantees, and DLQ
31. How do you guarantee ledger write and outbox enqueue are atomic?
32. What prevents two outbox workers from double-publishing the same message?
33. What happens under retry storm when publisher is constantly failing?
34. At what point does an outbox event move from retry to FAILED and DLQ?
35. Which metrics indicate retry pressure and publication failure?
36. How do you prove DLQ was actually produced, not only logged?

## F. Governance, bias, and institutional defensibility
37. What assumptions remain outside the cryptographic trust boundary?
38. How do you mitigate bias or staleness in country emission factors?
39. How does methodology version governance avoid silent breaking changes?
40. What minimum evidence package should be archived for hostile third-party re-audit?
