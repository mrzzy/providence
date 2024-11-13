#
# Providence
# Sources
# SimplyGo Source
#

import argparse
import json
import logging
import os
from datetime import date
from logging import log
from pathlib import Path
from typing import cast

import simplygo


def parse_args():
    parser = argparse.ArgumentParser(description="SimplyGo Source")

    parser.add_argument(
        "--username",
        help="Username used to login on SimplyGo",
        default=os.environ.get("SIMPLYGO_SRC_USERNAME"),
    )

    parser.add_argument(
        "--password",
        help="Password used to login on SimplyGo",
        default=os.environ.get("SIMPLYGO_SRC_PASSWORD"),
    )

    parser.add_argument(
        "--trips-from",
        required=True,
        type=date.fromisoformat,
        help="Date starting period from which trips are scraped from SimplyGo in format YYYY-MM-DD",
    )

    parser.add_argument(
        "--trips-to",
        required=True,
        type=date.fromisoformat,
        help="Date ending period from which trips are scraped from SimplyGo in format YYYY-MM-DD",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default="out.json",
        help="Output path to write trip data scraped from SimplyGo as JSON.",
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # parse program args
    args = parse_args()

    # setup simplygo client
    simplygo = simplygo.Ride(args.username, args.password)

    # fetch user id
    logging.info("Fetching user info from SimplyGo API")
    user_info = simplygo.get_user_info()
    if not user_info:
        raise RuntimeError("Failed to get user info from SimplyGo API")
    user_id = user_info["UniqueCode"]  # type: ignore
    logging.info(f"Got user info from SimplyGo API for user unique code: {user_id}")

    # fetch card ids
    logging.info("Fetching card info from SimplyGo API")
    cards = simplygo.get_card_info()
    if not cards:
        raise RuntimeError("Failed to get card info from SimplyGo API")
    logging.info(f"Got card info from SimplyGo API for {len(cards)} cards.")  # type: ignore

    # fetch transactions (eg. trips) made on each card
    for card in cards:  # type: ignore
        card_id = card["UniqueCode"]
        logging.info(f"Fetching transactions from SimplyGo API for card: {card_id}")
        transactions = simplygo.get_transactions(  # type: ignore
            card_id=card_id,
            start_date=args.trips_from,
            end_date=args.trips_to,
        )
        if not transactions:
            raise RuntimeError(
                f"Failed to fetch transactions from SimplyGo API for card: {card_id}"
            )
        logging.info(f"Fetched transactions from SimplyGo API for card: {card_id}")

    # write scrapped data as json
    logging.info(f"Writing SimplyGo data as JSON")
    with open(args.output, "w") as f:
        json.dump(cards, f)
    logging.info(f"Wrote SimplyGo data as JSON: {args.output}")
