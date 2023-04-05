#
# Providence
# YNAB Source
#

from datetime import datetime
from io import BytesIO
import json
from unittest.mock import patch, Mock
import boto3

import pytest
from ynab_sdk.api.models.responses.budget_detail import (
    Budget,
    BudgetDetailResponse,
    CurrencyFormat,
    Data,
    DateFormat,
)
from ynab import YNAB, ingest_budget_s3, to_json


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


def test_budget_to_json(budget: Budget):
    actual_budget = Budget.from_dict(json.loads(to_json(budget)))
    assert actual_budget == budget


def test_ingest_budget_s3(budget: Budget):
    ynab, s3 = Mock(YNAB), Mock(boto3.client("s3"))
    ynab.budgets.get_budget.return_value = BudgetDetailResponse(
        data=Data(
            server_knowledge=0,
            budget=budget,
        )
    )

    ingest_budget_s3(ynab, s3, "budget_id", "s3://bucket/path/data.json")

    s3.upload_fileobj.assert_called_once()
    assert s3.upload_fileobj.call_args[0][1:] == ("bucket", "path/data.json")
    assert s3.upload_fileobj.call_args[0][0].getvalue().decode() == to_json(budget)
