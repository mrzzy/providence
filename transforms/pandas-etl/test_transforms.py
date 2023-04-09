#
# Providence
# Transforms
# Transformations
#

import pandas as pd
from pandas.io.common import Path
from pandas.testing import assert_frame_equal

from transforms import extract_uob, promote_header

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
            "Withdrawal": ["5", "5"],
            "Deposit": ["5", "5"],
            "Available Balance": ["2000", "2000"],
            "Account Number": ["123456789", "123456789"],
            "Account Type": ["One Account", "One Account"],
            "Statement Period": [
                "06 Feb 2023 To 07 Apr 2023",
                "06 Feb 2023 To 07 Apr 2023",
            ],
            "Currency": ["SGD", "SGD"],
        },
    )
    print(actual_df.to_string())

    assert expected_df.equals(actual_df)
