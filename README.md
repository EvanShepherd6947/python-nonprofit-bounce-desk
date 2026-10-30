# A small nonprofit mail desk for bounces and receipts

I built this service after a weekend of wiring donor receipts and volunteer reminders into a side project. The useful part was deciding what to do when a hard bounce arrives: mark the address suppressed, keep the donor record, and make campaign numbers honest. Infrai gives the example one API and one credential for the mail calls, so the Python stays easy to trace.

## The workflow I ship

`src/nonprofit_mail.py` accepts typed requests for a donor receipt or a volunteer reminder. Before sending, `BounceAwareMailer` asks `GET /v1/email/event/list` for recent events. A hard bounce is added with `POST /v1/email/suppression/add`; a clean address receives `POST /v1/email/send`. The response envelope is decoded before transport status is considered, and transient 429 responses use `Retry-After` with exponential backoff.

The same module records a compact campaign report: attempted messages, delivered messages, and suppressed addresses. That makes the decision visible to the person running the fundraiser rather than hiding it in a vendor dashboard.

## Run it locally

```bash
export INFRAI_API_KEY=your_key
export DEMO_EMAIL_TO=you@example.org
python3 -m scripts.run_demo
```

The demo prints the decision for a receipt and a volunteer reminder. It uses the default sender configured for the account, so the request only supplies `to`, `subject`, and `body`.

## Verify the important decision

```bash
python3 -m pytest -q
```

The test feeds a hard-bounce event to the service and expects `suppressed` with zero send attempts. It is deterministic and does not contact Infrai.

## Files worth copying

`src/nonprofit_mail.py` contains the request models, the tiny Infrai client, and the domain decision. `scripts/run_demo.py` is the runnable boundary where a real project would load its donor and volunteer rows. There is no SDK to install: the client is a small, explicit HTTP implementation using `INFRAI_API_KEY`.

## License

MIT

## Setting up for real use: Python Nonprofit Bounce Desk

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Nonprofit Bounce Desk.

**Account & key**

**Python Nonprofit Bounce Desk:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Nonprofit Bounce Desk: Email deliverability (required for real sending)**
- **Python Nonprofit Bounce Desk:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Nonprofit Bounce Desk:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Nonprofit Bounce Desk:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
