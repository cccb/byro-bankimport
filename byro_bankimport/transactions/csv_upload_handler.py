"""
Handle csv upload parse signal
"""
from django.db.transaction import atomic

from byro.bookkeeping.models import (
    Transaction,
    Booking,
    Account,
)

from byro_bankimport.transactions.parsers import deutsche_bank
from byro_bankimport.transactions.parsers.deutsche_bank import (
    TX_TYPE_CREDIT,
)


# TODO: get from config
CREDIT_ACCOUNT_NAME = "Member fees"
CREDIT_ACCOUNT = Account.objects.get(name=CREDIT_ACCOUNT_NAME)

def process_csv_upload(tx_source):
    """Process incoming Transaction file"""
    print("processing source file:", tx_source.source_file)
    with open(tx_source.source_file.url, encoding="iso-8859-1") as f:
        transactions = deutsche_bank.parse_file(f) 

        # Create byro transactions and bookings
        for tx in transactions:
            if tx["type"] != TX_TYPE_CREDIT:
                continue # We are not interested.
            with atomic():
                transaction = Transaction(
                    memo=tx["name"],
                    booking_datetime=tx["booking_datetime"],
                    value_datetime=tx["value_datetime"],
                )
                transaction.save()

                booking = Booking(
                    transaction=transaction,
                    debit_account=CREDIT_ACCOUNT,
                    source=tx_source,
                    booking_datetime=tx["booking_datetime"],
                    amount=tx["amount"],
                    memo=tx["memo"], 
                    importer="byro_bankimport",
                )
                booking.save()
