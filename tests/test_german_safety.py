"""German document headers must stay out of automatic cleanup plans."""
from __future__ import annotations

import datetime as dt
import unittest

from helpers import ROOT

from config import Account, Config, Policy, ScanOptions, UnsubscribeOptions
from mailparse import ParsedHeaders
from planning import build_plan
from safety import classify, protect_verdict
from store import StoredMessage
from util import to_iso, utcnow


DOCUMENT_SUBJECTS = (
    "Ihre Rechnung", "Deine Rechnung von Beispiel", "Rechnung RE-12345",
    "Ihre Rechnungen sind verfügbar", "Hier ist Ihre Gutschrift",
    "Ihre Kabel-Rechnung steht bereit", "Ihre Mobilfunkrechnung ist da",
    "Zahlungserinnerung zu Ihrer Bestellung", "Mahnung zur Rechnung 123",
    "Ihre Vertragsbestätigung", "Ihre Vertragsbestaetigung",
    "Bestätigung Ihrer Kündigung", "Bestaetigung Ihrer Kuendigung",
    "Kündigungsbestätigung", "Kuendigungsbestaetigung",
    "Ihr aktueller Versicherungsschein ist da", "Beitragsrechnung 2027",
    "Dein REWE eBon vom 01.01.2026", "Ihr Kassenbon",
    "Sicherheitswarnung", "Ungewöhnliche Anmeldung erkannt",
    "Ungewoehnliche Anmeldung erkannt", "Ihr Bestätigungscode",
    "Ihr Bestaetigungscode", "Passwort zurücksetzen",
    "Passwort zuruecksetzen", "Ihr Arbeitsvertrag",
    "Ihre Gehaltsabrechnung", "Ihr Steuerbescheid",
    "Unterhaltsvorschuss: Rückfrage zu Ihren Nachweisen",
    "Ihre Terminbestätigung", "Ihre Buchungsbestaetigung",
    "Ihre Reservierungsbestätigung", "Ihre Zahlungsbestätigung",
)

AD_SUBJECTS = (
    "Rabatt auf deine Versicherung", "Versicherungsschutz verbessern",
    "Jetzt kaufen auf Rechnung", "Kaufen auf Rechnung: neue Angebote",
    "20 Prozent Rabatt auf ausgewählte Verträge",
    "Sicherheit für dein Zuhause: unsere Angebote",
    "Gutschein für die nächste Reise", "Newsletter: Angebote der Woche",
)


class GermanSafetyTest(unittest.TestCase):
    def test_german_documents_are_protected_even_with_campaign_headers(self):
        for subject in DOCUMENT_SUBJECTS:
            with self.subTest(subject=subject):
                headers = ParsedHeaders(
                    from_addr="noreply@provider.example", subject=subject,
                    list_unsub="<https://provider.example/unsubscribe>",
                    list_id="news.provider.example", precedence="bulk",
                    x_campaign="campaign",
                )
                result = classify(headers)
                self.assertTrue(result.protected)
                self.assertIsNotNone(result.protected_reason)

    def test_plain_german_documents_are_transactional(self):
        for subject in DOCUMENT_SUBJECTS:
            with self.subTest(subject=subject):
                result = classify(ParsedHeaders(
                    from_addr="noreply@provider.example", subject=subject))
                self.assertEqual(result.category, "transactional")
                self.assertTrue(result.protected)

    def test_generic_german_advertising_is_not_a_document(self):
        for subject in AD_SUBJECTS:
            with self.subTest(subject=subject):
                self.assertFalse(protect_verdict(ParsedHeaders(
                    from_addr="news@provider.example", subject=subject)).protected)

    def test_german_protected_mail_is_neither_moved_nor_unsubscribed(self):
        old = to_iso(utcnow() - dt.timedelta(days=120))
        messages = []
        for uid, subject in enumerate(DOCUMENT_SUBJECTS, 1):
            headers = ParsedHeaders(
                from_addr="noreply@provider.example", subject=subject,
                list_unsub="<https://provider.example/unsubscribe>",
                list_unsub_post="List-Unsubscribe=One-Click",
                list_id="news.provider.example", precedence="bulk",
            )
            result = classify(headers)
            messages.append(StoredMessage(
                mailbox="INBOX", uid=uid, uidvalidity=1,
                message_id=f"synthetic-{uid}@example.test",
                from_addr=headers.from_addr, subject=subject, date=old,
                size=500, flags=[], category=result.category,
                confidence=result.confidence, protected=result.protected,
                protected_reason=result.protected_reason, reasons=result.reasons,
                bulk=result.bulk, list_unsub=headers.list_unsub,
                list_unsub_post=headers.list_unsub_post,
            ))
        config = Config(
            path=ROOT / "synthetic.toml",
            account=Account(email="me@example.test", imap_host="imap.example.test"),
            scan=ScanOptions(), policy=Policy(),
            unsubscribe=UnsubscribeOptions(one_click=True),
        )
        plan = build_plan(messages, config)
        self.assertEqual(plan.actions, [])


if __name__ == "__main__":
    unittest.main()
