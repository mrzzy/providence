#
# Providence
# YNAB Source
#

from dataclasses import asdict
from datetime import datetime
from io import BytesIO
import json
from unittest.mock import patch, Mock
import boto3

import pytest
from ynab_sdk import YNAB
from ynab_sdk.api.models.responses.budget_detail import (
    Budget,
    BudgetDetailResponse,
    CurrencyFormat,
    Data,
    DateFormat,
)
from ynab import MetaBudget, ingest_budget_s3, to_json


@pytest.fixture
def budget() -> Budget:
    return Budget(
        id="budget_id",
        name="name",
        last_modified_on=datetime.min,
        first_month="",
        last_month="",
        date_format=DateFormat(format=""),
        currency_format=CurrencyFormat("", "", 0, "", False, "", "", False),
        accounts=[],
        payees=[],
        payee_locations=[],
        category_groups=[],
        categories=[],
        months=[],
        transactions=[],
        subtransactions=[],
        scheduled_transactions=[],
        scheduled_subtransactions=[],
    )


@pytest.fixture
def metabudget(budget: Budget) -> MetaBudget:
    return MetaBudget(
        _ynab_src_scraped_on=datetime.min,
        **asdict(budget),
    )


def test_budget_to_json(metabudget: MetaBudget):
    assert json.loads(to_json(metabudget)) == {
        "id": "budget_id",
        "name": "name",
        "last_modified_on": "0001-01-01T00:00:00",
        "first_month": "",
        "last_month": "",
        "date_format": {"format": ""},
        "currency_format": {
            "iso_code": "",
            "example_format": "",
            "decimal_digits": 0,
            "decimal_separator": "",
            "symbol_first": False,
            "group_separator": "",
            "currency_symbol": "",
            "display_symbol": False,
        },
        "accounts": [],
        "payees": [],
        "payee_locations": [],
        "category_groups": [],
        "categories": [],
        "months": [],
        "transactions": [],
        "subtransactions": [],
        "scheduled_transactions": [],
        "scheduled_subtransactions": [],
        "_ynab_src_scraped_on": "0001-01-01T00:00:00",
    }


def test_ingest_budget_s3(budget: Budget, metabudget: MetaBudget):
    ynab, s3 = Mock(YNAB), Mock(boto3.client("s3"))
    ynab.budgets.get_budget.return_value = BudgetDetailResponse(
        data=Data(
            server_knowledge=0,
            budget=budget,
        )
    )

    ingest_budget_s3(ynab, s3, "budget_id", "s3://bucket/path/data.json", datetime.min)

    s3.upload_fileobj.assert_called_once()
    assert s3.upload_fileobj.call_args[0][1:] == ("bucket", "path/data.json")
    assert s3.upload_fileobj.call_args[0][0].getvalue().decode() == to_json(metabudget)
