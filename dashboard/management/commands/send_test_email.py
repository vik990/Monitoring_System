from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Send a test email using a resident profile or project SMTP'

    def add_arguments(self, parser):
        parser.add_argument('--resident', type=int, help='Resident ID to use for sending (optional)')
        parser.add_argument('--to', type=str, help='Recipient email address', required=True)

    def handle(self, *args, **options):
        resident_id = options.get('resident')
        to_addr = options.get('to')

        if resident_id:
            from dashboard.models import Resident
            try:
                r = Resident.objects.get(id=resident_id)
            except Resident.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Resident {resident_id} not found'))
                return

            subject = 'Test email from Household Electricity Dashboard (resident)'
            message = f"This is a test email using resident profile {r.profile_name} ({r.email})"
            ok = r.send_alert(subject, message)
            if ok:
                self.stdout.write(self.style.SUCCESS('Resident send_alert reported success'))
            else:
                self.stderr.write(self.style.ERROR('Resident send_alert reported failure'))

        else:
            # Use project send
            from django.core.mail import EmailMessage
            subject = 'Test email from Household Electricity Dashboard (project)'
            body = 'This is a test email using project SMTP settings.'
            email_msg = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_addr])
            try:
                email_msg.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS('Project SMTP send succeeded'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Project SMTP send failed: {e}'))
