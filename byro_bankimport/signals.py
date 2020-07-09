# Register your receivers here

from django.dispatch import receiver

from byro.bookkeeping.signals import process_csv_upload

from byro_bankimport.transactions import csv_upload_handler


# Connect Signals
@receiver(process_csv_upload)
def handle_process_csv_upload(sender, **kwargs):
    return csv_upload_handler.process_csv_upload(sender)

