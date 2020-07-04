
import pytest
import os

from byro_bankimport.transactions.parsers import deutsche_bank

def _test_data_filename(filename):
    """Get full path to test data"""
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "data", filename)


def test_parse_file():
    """Test parsing"""
    with open(_test_data_filename("fileupload.csv"), encoding="iso-8859-1") as f:
        transactions = deutsche_bank.parse_file(f)
        print(transactions)

        # Test Assertions
        assert transactions
        assert len(transactions) == 7


