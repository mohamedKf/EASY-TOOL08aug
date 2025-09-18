from django.core.management.base import BaseCommand
from accounts.models import generate_monthly_reports_from_attendance  # make sure it's in models.py

class Command(BaseCommand):
    help = 'Generate monthly reports from attendance records'

    def handle(self, *args, **kwargs):
        generate_monthly_reports_from_attendance()
        self.stdout.write(self.style.SUCCESS("✅ Monthly reports generated successfully."))
