from src.nonprofit_mail import BounceAwareMailer, DonorReceipt, VolunteerReminder


class FakeClient:
    def __init__(self):
        self.sent = []
        self.suppressed = []

    def email_events(self, address):
        return {"ok": True, "data": {"events": [{"type": "hard_bounce"}]}}

    def add_suppression(self, address):
        self.suppressed.append(address)
        return {"ok": True, "data": {}}

    def email_send(self, payload):
        self.sent.append(payload)
        return {"ok": True, "data": {"message_id": "m-1"}}


class CleanClient(FakeClient):
    def email_events(self, address):
        return {"ok": True, "data": {"events": []}}


def test_hard_bounce_suppresses_before_send():
    client = FakeClient()
    mailer = BounceAwareMailer(client)
    result = mailer.send_receipt(DonorReceipt("donor@example.org", "Lee", 1000, "Winter"))
    assert result == "suppressed"
    assert client.suppressed == ["donor@example.org"]
    assert client.sent == []
    assert mailer.report.suppressed == ["donor@example.org"]


def test_send_uses_contract_body_field():
    client = CleanClient()
    mailer = BounceAwareMailer(client)
    assert mailer.send_receipt(DonorReceipt("donor@example.org", "Lee", 1000, "Winter")) == "m-1"
    assert mailer.remind_volunteer(VolunteerReminder("donor@example.org", "Lee", "Monday")) == "m-1"
    assert client.sent == [
        {"to": "donor@example.org", "subject": "Receipt for Winter", "body": "Thanks Lee; your gift was $10.00."},
        {"to": "donor@example.org", "subject": "Your Monday volunteer shift", "body": "Hi Lee, this is a reminder for Monday."},
    ]
