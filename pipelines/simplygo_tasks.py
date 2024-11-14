#
# Providence
# SimplyGo Flow
# Tasks
#

from datetime import date
from logging import Logger, LoggerAdapter
from typing import Any, Dict
import simplygo


def fetch_simplygo(
    client: simplygo.Ride,
    log: Logger | LoggerAdapter,
    trips_from: date,
    trips_to: date,
) -> Dict[str, Any]:
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
        A dictionary containing scraped simplygo data

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
