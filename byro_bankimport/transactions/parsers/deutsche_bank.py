"""
Parse CSV export from Deutsche Bank.
"""

import csv
from typing import List, Tuple, Any, IO
from datetime import datetime
from decimal import Decimal

ROW_TYPE_IGNORE = "ignore"
ROW_TYPE_TRANSACTION = "transaction"

# Literal[ROW_TYPE_META, ...] did not work
RowType = str

Row = List[Any]

TX_TYPE_CREDIT = "credit"
TX_TYPE_DEBIT = "debit"


def parse_file(csv_file: IO) -> List[dict]:
    """Parse the accout export file"""
    reader = csv.reader(
        csv_file,
        delimiter=';',
        quotechar='"')

    results = [_parse_row(row) for row in reader]

    # Build transactions
    transactions = [tx for (row_type, tx) in results
                    if row_type == ROW_TYPE_TRANSACTION]

    return transactions


def _parse_row(row: Row) -> Tuple[RowType, dict]:
    """Parse Row"""
    row_type = _parse_row_type(row)
    if row_type == ROW_TYPE_TRANSACTION:
        return (row_type, _parse_transaction(row))

    return (row_type, {"row": row})


def _parse_row_type(row: Row) -> RowType:
    """Decode row type"""
    if _is_row_transaction(row):
        return ROW_TYPE_TRANSACTION

    return ROW_TYPE_IGNORE


def _is_row_transaction(row: Row) -> bool:
    """Is this a transaction row?"""
    try:
        return "SEPA" in row[2]
    except:
        return False


def _parse_transaction(row: Row) -> dict:
    """Parse a transaction row"""
    # Extract row values
    booking_datetime = _parse_datetime(row[0])
    value_datetime = _parse_datetime(row[1])
    if row[15]:
        tx_type = TX_TYPE_DEBIT
    else:
        tx_type = TX_TYPE_CREDIT
    name = row[3]
    memo = row[4]
    iban = row[5]
    bic = row[6]
    if tx_type == TX_TYPE_DEBIT:
        amount = _parse_amount(row[15])
    else:
        amount = _parse_amount(row[16])

    return {
        "type": tx_type,
        "booking_datetime": booking_datetime,
        "value_datetime": value_datetime,
        "name": name,
        "memo": memo,
        "iban": iban,
        "bic": bic,
        "amount": amount,
    }


def _must_positive_intvalue(value: str) -> int:
    """String must be an integer value > 0 - if not use default"""
    try:
        intval = int(value)
        if intval < 1:
            intval = 1
        return intval
    except:
        return 1


def _parse_datetime(value: str) -> datetime:
    """Robust parse date"""
    try:
        (dd, mm, yyyy, *rest) = value.split(".")
        if rest:
            raise ValueError(value)
    except:
        raise ValueError(value)

    return datetime(
        _must_positive_intvalue(yyyy),
        _must_positive_intvalue(mm),
        _must_positive_intvalue(dd),
    )


def _parse_amount(value: str) -> Decimal:
    """Parse amount value"""
    return Decimal(value.replace(".", "").replace(",", "."))

