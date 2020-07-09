"""
Handle csv upload parse signal
"""
from django.db.transaction import atomic

from byro.settings import config
from byro.bookkeeping.models import (
    Transaction,
    Booking,
    Account,
)

from byro_bankimport.transactions.parsers import deutsche_bank
from byro_bankimport.transactions.parsers.deutsche_bank import (
    TX_TYPE_CREDIT,
)


CREDIT_ACCOUNT_NAME = config.get("bankimport", "credit_account_name")
CREDIT_ACCOUNT = Account.objects.get(name=CREDIT_ACCOUNT_NAME)



def process_csv_upload(tx_source):
    """Process incoming Transaction file"""
    print("processing source file:", tx_source.source_file)
    filepath = tx_source.source_file.path
    with open(filepath, encoding="iso-8859-1") as f:
        transactions = deutsche_bank.parse_file(f)
        file_id = deutsche_bank.file_id(f)

        # Create byro transactions and bookings
        for nr, tx in enumerate(transactions):
            if tx["type"] != TX_TYPE_CREDIT:
                continue # We are not interested.

            _import_transaction(tx_source, file_id, nr, tx)


@atomic
def _import_transaction(tx_source, file_id, nr, tx):
    """Import the transaction"""
    # Check if transaction is already present!
    if Transaction.objects.filter(
            data__file_id=file_id,
            data__nr=nr,
        ).exists():
        print(" - skipping transaction nr: {}".format(nr))
        return

    transaction = Transaction(
        memo=tx["name"],
        booking_datetime=tx["booking_datetime"],
        value_datetime=tx["value_datetime"],
        data={
            "file_id": file_id,
            "nr": nr,
        },
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
