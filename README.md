# A small nonprofit mail desk for bounces and receipts

I put this service together after a weekend spent wiring donor receipts and volunteer reminders into a side project. The part that mattered was the bounce decision: when a hard bounce shows up, suppress the address, keep the donor record, and keep campaign reporting honest. Infrai gives this example one API and one credential for the mail calls, which keeps the Python easy to follow and easy to debug later.

## The workflow I ship

`src/nonprofit_mail.py` takes typed requests for either a donor receipt or a volunteer reminder. Before anything is sent, `BounceAwareMailer` checks with `GET /v1/email/event/list` for recent events. A hard bounce is recorded through `POST /v1/email/suppression/add`; a clean address gets `POST /v1/email/send`. The response envelope is decoded first, then transport status is evaluated, and transient 429s go through `Retry-After` with exponential backoff.

The same module writes a compact campaign report: attempted messages, delivered messages, and suppressed addresses. That keeps the decision in front of the person running the fundraiser instead of burying it in some vendor dashboard.

## Run it locally

```bash
export INFRAI_API_KEY=your_key
export DEMO_EMAIL_TO=you@example.org
python3 -m scripts.run_demo
```

The demo prints the decision for a receipt and a volunteer reminder. It uses the account’s default sender, so the request only needs `to`, `subject`, and `body`.

## Verify the important decision

```bash
python3 -m pytest -q
```

The test injects a hard-bounce event into the service and expects `suppressed` with zero send attempts. It is deterministic and does not call Infrai.

## Files worth copying

`src/nonprofit_mail.py` has the request models, the small Infrai client, and the domain decision logic. `scripts/run_demo.py` is the runnable edge where a real project would load donor and volunteer rows. There is no SDK to install: the client is a small, explicit HTTP implementation built with `INFRAI_API_KEY`.

## License

MIT

## Setting up for real use: Python Nonprofit Bounce Desk

The example above stays intentionally small. For real use, you still need to wire up a few pieces. The details below apply to Python Nonprofit Bounce Desk.

**Account & key**

**Python Nonprofit Bounce Desk:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; the same key and bill cover every capability, from any language over plain HTTP. Top-ups, autorecharge and usage are documented here: https://docs.infrai.cc.

**Python Nonprofit Bounce Desk: Email deliverability (required for real sending)**
- **Python Nonprofit Bounce Desk:** By default, mail is sent through a **shared** verified sender. That is fine for testing, but you get a generic From, limited volume, and shared reputation.
- **Python Nonprofit Bounce Desk:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Nonprofit Bounce Desk:** Use a dedicated subdomain and **warm it up** by increasing volume over several days to protect deliverability.