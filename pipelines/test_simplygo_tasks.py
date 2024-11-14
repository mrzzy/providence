#
# Providence
# SimplyGo Flow Tasks
# Tests
#

from logging import Logger
from pendulum import date
import pytest

from simplygo_tasks import fetch_simplygo


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
