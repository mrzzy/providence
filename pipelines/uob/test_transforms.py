#
# Providence
# UOB Transforms
# Unit Tests
#

import pandas as pd
from pandas.io.common import Path
from pandas.testing import assert_frame_equal
from datetime import date

from uob.transforms import extract_uob, parse_scraped_on, promote_header

RESOURCES_DIR = Path(__file__).parent / "resources"


def test_promote_header():
    actual_df = promote_header(
        pd.DataFrame(
            [
                [1, 2],
                [3, 4],
            ]
        ),
    )
    expected_df = pd.DataFrame(
        {
            1: [3],
            2: [4],
        },
        index=pd.RangeIndex(start=1, stop=2, step=1),
    )
    assert expected_df.equals(actual_df)


def test_transform_uob():
    # read test data as string to avoid pandas's type inference from interfering with testing
    df = pd.read_excel(RESOURCES_DIR / "ACC_TXN_test.xls", dtype=str)
    actual_df = extract_uob(df)
    expected_df = pd.DataFrame(
        {
            "Transaction Date": ["06 Apr 2023", "04 Apr 2023"],
            "Transaction Description": [
                "Placeholder Description",
                "Placeholder Description",
            ],
            "Withdrawal": [5.0, 5.0],
            "Deposit": [5.0, 5.0],
            "Available Balance": [2000.0, 2000.0],
            "Account Number": ["123456789", "123456789"],
            "Account Type": ["Test Account", "Test Account"],
            "Statement Period": [
                "06 Feb 2023 To 07 Apr 2023",
                "06 Feb 2023 To 07 Apr 2023",
            ],
            "Currency": ["SGD", "SGD"],
        },
    )
    assert expected_df.equals(actual_df)


def test_parse_uob():
    cases = [
        ["ACC_TXN_History_05062024124137.xls", date(2024, 6, 5)],
        ["ACC_TXN_History_05062024355224.xls", date(2024, 6, 5)],
        ["ACC_TXN_History_05062024.xls", date(2024, 6, 5)],
        ["ACC_TXN_History_05072022.xls", date(2022, 7, 5)],
    ]

    for filename, expected in cases:
        assert parse_scraped_on(filename) == expected
