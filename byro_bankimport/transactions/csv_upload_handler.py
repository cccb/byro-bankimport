"""
Handle csv upload parse signal
"""
from hashlib import sha256

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

try:
    CREDIT_ACCOUNT_ID = config.get("bankimport", "credit_account_id")
    CREDIT_ACCOUNT = Account.objects.get(pk=CREDIT_ACCOUNT_ID)
except:
    CREDIT_ACCOUNT = None
    print("WARNING: Bank account not configured.")


def process_csv_upload(tx_source):
    """Process incoming Transaction file"""
    if not CREDIT_ACCOUNT:
        raise RuntimeError("Import Not Configured.")

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
        memo="Received from: {} | {} | {}".format(
            tx["name"],
            tx["iban"],
            tx["memo"]),
        booking_datetime=tx["booking_datetime"],
        value_datetime=tx["value_datetime"],
        data={
            "correlation_id": correlation_id(tx),
            "file_id": file_id,
            "nr": nr,
            "name": tx["name"],
            "memo": tx["memo"],
            "iban": tx["iban"],
            "bic": tx["bic"],
        },
    )
    transaction.save()

    booking = Booking(
        transaction=transaction,
        debit_account=CREDIT_ACCOUNT,
        source=tx_source,
        booking_datetime=tx["booking_datetime"],
        amount=tx["amount"],
        memo="{}: {}".format(tx["name"], tx["memo"]),
        importer="byro_bankimport",
    )
    booking.save()


def correlation_id(tx) -> str:
    """
    Calculate a hash over the bank account information
    for later correlation with the member account.

    The hash is calculated over the IBAN + BIC
    """
    shasum = sha256()
    shasum.update(bytes(tx["iban"], "utf-8"))
    shasum.update(bytes(tx["bic"], "utf-8"))

    return shasum.hexdigest()

