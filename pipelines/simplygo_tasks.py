#
# Providence
# SimplyGo Flow
# Tasks
#
import re

from datetime import date, datetime
from logging import Logger, LoggerAdapter
from typing import Any, Dict
import simplygo

import pandas as pd


def fetch_simplygo(
    client: simplygo.Ride,
    log: Logger | LoggerAdapter,
    trips_from: date,
    trips_to: date,
) -> list[Dict[str, Any]]:
    """
    Fetches SimplyGo card transactions within a date range for a specified user.

    Logs into the SimplyGo API, retrieves user and card details, and fetches trip transactions
    for each card within the specified date range.

    Args:
        client: SimplyGo API client to fetch data with.
        log: Logger for recording process info and errors.
        trips_from: Start date for transactions.
        trips_to: End date for transactions.

    Returns:
        A scrapped Simplygo data as a list of cards.

    Raises:
        RuntimeError: If user info, card info, or transactions cannot be retrieved.
    """
    # fetch user id
    log.info("Fetching user info from SimplyGo API")
    user_info = client.get_user_info()
    if not user_info:
        raise RuntimeError("Failed to get user info from SimplyGo API")
    user_id = user_info["UniqueCode"]  # type: ignore
    log.info(f"Got user info from SimplyGo API for user unique code: {user_id}")

    # fetch card ids
    log.info("Fetching card info from SimplyGo API")
    cards = client.get_card_info()
    if not cards:
        raise RuntimeError("Failed to get card info from SimplyGo API")
    log.info(f"Got card info from SimplyGo API for {len(cards)} cards.")  # type: ignore

    # fetch transactions (eg. trips) made on each card
    for card in cards:  # type: ignore
        card_id = card["UniqueCode"]
        log.info(f"Fetching transactions from SimplyGo API for card: {card_id}")
        transactions = client.get_transactions(  # type: ignore
            card_id=card_id,
            start_date=trips_from,
            end_date=trips_to,
        )
        if not transactions:
            raise RuntimeError(
                f"Failed to fetch transactions from SimplyGo API for card: {card_id}"
            )
        card["transactions"] = transactions
        log.info(f"Fetched transactions from SimplyGo API for card: {card_id}")
    return cards  # type: ignore


def transform_simplygo(
    log: Logger | LoggerAdapter,
    data: list[Dict[str, Any]],
    scraped_on: datetime,
) -> pd.DataFrame:
    """
    Transforms SimplyGo transaction data into a structured DataFrame.

    Extracts relevant details from a list of transaction data, including card information,
    trip details, fare, and transport mode. It returns a DataFrame with each trip leg's
    information.

    Args:
        log: Logger or LoggerAdapter instance for logging.
        data: List of dictionaries containing SimplyGo transaction history.
        scraped_on: Datetime when the data was scraped.

    Returns:
        A pandas DataFrame with trip leg details including card ID, cost, source, destination,
        transport mode, and trip ID.

    Raises:
        ValueError: If the transport mode cannot be extracted from the transaction data.
    """
    mode_re = re.compile(r"CTP (?P<mode>\w+) Usage Mtch")

    # fetch user id
    rows = []
    for card in data:
        for history in card["transactions"]["Histories"]:
            if history["Type"] == "Journey":
                # trip is a set of trip legs. In Simplygo API, this is known as 'Journey'.
                # composite trip id that uniquely identifies the trip
                trip = history
                trip_id = f'{trip["TokenID"]}_{trip["EntryLocationId"]}_{trip["EntryTransactionDate"]}'

                # trip leg is a segment if a trip. In Simplygo API, this is now as a 'Trip'.
                for leg in trip["Trips"]:
                    match = mode_re.match(leg["TransactionType"])
                    if not match:
                        raise ValueError(
                            "Failed to match transport mode in given data."
                        )
                    rows.append(
                        {
                            "card_id": card["UniqueCode"],
                            "card_name": card["Description"],
                            # remove leading '$' in Fare.
                            "cost_sgd": leg["Fare"].replace("$", ""),
                            "scraped_on": scraped_on.strftime("%Y-%m-%d %H:%M:%S"),
                            "source": leg["EntryLocationName"],
                            "destination": leg["ExitLocationName"],
                            "trip_id": trip_id,
                            "mode": match["mode"],
                            "traveled_on": leg["EntryTransactionDate"],
                            # posting ref defaults to empty as a nonpopulated legacy field
                            "posting_ref": "",
                        }
                    )

    return pd.DataFrame(rows)
