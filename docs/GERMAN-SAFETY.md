# German protected-mail recognition

This fork extends the existing protected-mail policy to concrete German subject
lines. It does not change the policy, move semantics or unsubscribe behavior.

The original classifier recognized English and Spanish document vocabulary but
classified synthetic `Ihre Rechnung`, `Ihre Vertragsbestaetigung` and
`Sicherheitswarnung` messages from an automated sender as unprotected
notifications. This can make important German mail eligible for cleanup.

## Scope

`tools/safety.py` now shares one German pattern between `protect_verdict` and
transactional classification. Covered signals include:

- invoices addressed to the recipient or identified at the start of the subject;
- named utility invoices, credit notes, payment reminders and receipts;
- contract/cancellation confirmations and insurance documents;
- security warnings, verification codes and password-reset messages;
- employment/pay documents, tax assessments and maintenance-advance cases;
- appointment, payment, booking and reservation confirmations.

Common umlaut transliterations are recognized. Matching is case-insensitive.
Generic terms such as `Versicherung`, `Vertrag` and `Sicherheit` are not sufficient
by themselves. `Kaufen auf Rechnung` is not treated as an actual invoice.

## Verification

`tests/test_german_safety.py` uses fictional senders and subjects only. It verifies
document protection even with campaign headers, ordinary transactional
classification, advertising counterexamples, and exclusion from both move and
unsubscribe plans. The classifier's winning category can still be a bulk category
when strong bulk signals are present; the protected flag must nevertheless keep
the message out of all automatic actions.

Run the focused tests with:

```sh
python -m unittest discover -s tests -p test_german_safety.py -v
```

## Limits

This is conservative header-based recognition, not a complete German-language
classifier or a guarantee that every important message is recognized. A subject
can be misleading, a real document may have a generic subject, and marketing can
mention a real document. Protected does not mean authenticated or trustworthy.

Use explicit protected sender lists and review plans. Existing cached
classifications and previously generated plans must be refreshed after updating;
the change does not rewrite them. Do not enable automatic cleanup of old plans.

No message body, attachment, real mailbox or cloud AI service is needed for the
regression tests. Docker deployment, technical-alert policies, crash recovery and
real-provider validation remain separate work before productive use.
