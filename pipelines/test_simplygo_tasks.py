#
# Providence
# SimplyGo Flow Tasks
# Tests
#

import pandas as pd
from logging import Logger
from pendulum import date, datetime
import pytest

from simplygo_tasks import fetch_simplygo, transform_simplygo


def test_fetch_simplygo(mocker):
    # Mock SimplyGo client and its methods
    client = mocker.Mock()
    client.get_user_info.return_value = {"UniqueCode": "user123"}
    client.get_card_info.return_value = [{"UniqueCode": "card123"}]
    transactions = [{"transaction": "trip details"}]
    client.get_transactions.return_value = transactions

    # Call the function
    trips_from = date(2024, 11, 12)
    trips_to = date(2024, 11, 14)
    result = fetch_simplygo(client, Logger("test"), trips_from, trips_to)

    # Assertions
    client.get_user_info.assert_called_once()
    client.get_card_info.assert_called_once()
    client.get_transactions.assert_called_once_with(
        card_id="card123", start_date=trips_from, end_date=trips_to
    )
    assert result == [{"UniqueCode": "card123", "transactions": transactions}]


def test_transform_simplygo_valid_data():
    # Embedded mock data
    mock_data = [
        {
            "UniqueCode": "123456",
            "Description": "Test Card",
            "transactions": {
                "Histories": [
                    {
                        "Type": "Journey",
                        "TokenID": "ABC123",
                        "EntryLocationId": "E1",
                        "EntryTransactionDate": "2024-11-14T00:00:00Z",
                        "Trips": [
                            {
                                "TransactionType": "CTP Bus Usage Mtch",
                                "EntryTransactionDate": "2024-11-14T00:00:00Z",
                                "Fare": "$1.50",
                                "EntryLocationName": "Station A",
                                "ExitLocationName": "Station B",
                            },
                            {
                                "TransactionType": "CTP Rail Usage Mtch",
                                "EntryTransactionDate": "2024-11-13T00:00:00Z",
                                "Fare": "Pass Usage",
                                "EntryLocationName": "Station C",
                                "ExitLocationName": "Station D",
                            },
                        ],
                    }
                ]
            },
        }
    ]

    scraped_on = datetime(2024, 11, 14, 10, 0, 0)

    # Call the function
    df = transform_simplygo(Logger("test"), mock_data, scraped_on)

    # Check the number of rows in the result
    assert len(df) == 2, "Expected two rows of data"

    # Check if the result contains the expected columns
    expected_columns = [
        "card_id",
        "card_name",
        "cost_sgd",
        "scraped_on",
        "source",
        "destination",
        "trip_id",
        "mode",
        "posting_ref",
    ]
    assert all(
        col in df.columns for col in expected_columns
    ), "Missing expected columns"

    # check pass usage is parsed correctly
    assert df.loc[1, "cost_sgd"] == "Pass Usage"
