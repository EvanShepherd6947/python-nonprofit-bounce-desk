import os

from src.nonprofit_mail import BounceAwareMailer, DonorReceipt, InfraiClient, VolunteerReminder


def main() -> None:
    target = os.environ.get("DEMO_EMAIL_TO")
    if not target:
        raise SystemExit("Set DEMO_EMAIL_TO before running the demo")
    mailer = BounceAwareMailer(InfraiClient())
    print(mailer.send_receipt(DonorReceipt(target, "Sam", 2500, "Spring appeal")))
    print(mailer.remind_volunteer(VolunteerReminder(target, "Sam", "Saturday morning")))
    print(mailer.report)


if __name__ == "__main__":
    main()
