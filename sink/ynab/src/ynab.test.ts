/*
 * Providence
 * YNAB Sink
 * YNAB Unit Tests
 */

import { jest, describe, expect, it } from "@jest/globals";
import { TableRow } from "./db.js";
import { SaveTransaction, API, PostTransactionsWrapper } from "ynab";
import { createYNABTransactions, toYNABTransactions } from "./ynab.js";
import { modelSaveTransaction, modelTableRow } from "./testModels.js";

describe("toYNABTransactions()", () => {
  it("transforms full transaction TableRow to YNAB's SaveTransaction", () => {
    expect(toYNABTransactions([modelTableRow])).toEqual([modelSaveTransaction]);
  });
  it("transaction split transactions TableRows to YNAB's SaveTransaction", () => {
    // template multiple rows to simulate subtransactions in a split transaction
    const split_params = {
      split_id: "split",
      split_memo: modelTableRow.memo,
      split_payee_id: modelTableRow.payee_id,
    };
    const rows: TableRow[] = [
      {
        ...modelTableRow,
        category_id: "category1",
        payee_id: "payee1",
        memo: "memo1",
        amount: 1,
        ...split_params,
      },
      {
        ...modelTableRow,
        category_id: "category2",
        payee_id: "payee2",
        memo: "memo2",
        amount: 2,
        ...split_params,
      },
      {
        ...modelTableRow,
        category_id: "category3",
        payee_id: "payee3",
        memo: "memo3",
        amount: 3,
        ...split_params,
      },
    ];
    expect(toYNABTransactions(rows)).toEqual([
      {
        ...modelSaveTransaction,
        category_id: null,
        date: "2023-05-04",
        amount: 1 + 2 + 3,
        subtransactions: [
          {
            category_id: "category1",
            payee_id: "payee1",
            memo: "memo1",
            amount: 1,
          },
          {
            category_id: "category2",
            payee_id: "payee2",
            memo: "memo2",
            amount: 2,
          },
          {
            category_id: "category3",
            payee_id: "payee3",
            memo: "memo3",
            amount: 3,
          },
        ],
      },
    ]);
  });
});

describe("createTransaction", () => {
  it("calls YNAB API Client's createTransaction()", async () => {
    /// mock YNAB client's createTransaction() for testing
    jest.doMock("ynab", () => {
      return {
        __esModule: true,
        API: function () {
          return {
            transactions: {
              createTransactions: jest.fn(
                async (_budget_id: string, _data: PostTransactionsWrapper) => {
                  return {
                    data: {
                      transaction_ids: (_data.transactions ?? []).map((t) =>
                        JSON.stringify(t)
                      ),
                      server_knowledge: 0,
                    },
                    rateLimit: null,
                  };
                }
              ),
            },
          };
        },
      };
    });

    const mockYNAB = await import("ynab");
    const api = new mockYNAB.API("token");
    createYNABTransactions(api, "budget", [modelSaveTransaction]);
    const nCalls = (
      api.transactions.createTransactions as jest.Mock<
        API["transactions"]["createTransactions"]
      >
    ).mock.calls.length;
    expect(nCalls).toEqual(1);
  });
});
