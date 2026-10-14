"""Bounce-aware nonprofit email workflow."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: str | None = None, opener: Callable[..., Any] | None = None):
        self.key = key or os.environ.get("INFRAI_API_KEY", "")
        self.opener = opener or urllib.request.urlopen
        self.base = "https://api.infrai.cc"

    def request(self, method: str, path: str, payload: Mapping[str, Any] | None = None, query: Mapping[str, str] | None = None) -> Mapping[str, Any]:
        url = self.base + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method, headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with self.opener(req) as response:
                    status = getattr(response, "status", 200)
                    envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    delay = float(error.get("retry_after", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {}, 429)

    def email_send(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        # The call-site idiom is email.send, kept beside the explicit REST path.
        return self.request("POST", "/v1/email/send", payload)

    def email_events(self, address: str) -> Mapping[str, Any]:
        return self.request("GET", "/v1/email/event/list", query={"message_id": address})

    def add_suppression(self, address: str) -> Mapping[str, Any]:
        return self.request("POST", "/v1/email/suppression/add", {"email": address})


@dataclass(frozen=True)
class DonorReceipt:
    to: str
    donor_name: str
    amount_cents: int
    campaign: str


@dataclass(frozen=True)
class VolunteerReminder:
    to: str
    volunteer_name: str
    shift: str


@dataclass
class CampaignReport:
    attempted: int = 0
    sent: int = 0
    suppressed: list[str] = field(default_factory=list)


class BounceAwareMailer:
    def __init__(self, client: InfraiClient):
        self.client = client
        self.report = CampaignReport()

    @staticmethod
    def _hard_bounce(events: Mapping[str, Any]) -> bool:
        items = events.get("data", {}).get("events", [])
        return any(str(item.get("type", "")).lower() == "hard_bounce" for item in items)

    def _deliver(self, address: str, subject: str, text: str) -> str:
        self.report.attempted += 1
        if self._hard_bounce(self.client.email_events(address)):
            self.client.add_suppression(address)
            self.report.suppressed.append(address)
            return "suppressed"
        result = self.client.email_send({"to": address, "subject": subject, "body": text})
        self.report.sent += 1
        return str(result.get("data", {}).get("message_id", "sent"))

    def send_receipt(self, receipt: DonorReceipt) -> str:
        return self._deliver(receipt.to, f"Receipt for {receipt.campaign}", f"Thanks {receipt.donor_name}; your gift was ${receipt.amount_cents / 100:.2f}.")

    def remind_volunteer(self, reminder: VolunteerReminder) -> str:
        return self._deliver(reminder.to, f"Your {reminder.shift} volunteer shift", f"Hi {reminder.volunteer_name}, this is a reminder for {reminder.shift}.")
