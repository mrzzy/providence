/*
 * Providence
 * YNAB Sink
 * Transforms Unit Tests
 */

import { describe, expect, it } from "@jest/globals";
import { MartTableRow, transformYNAB } from "./transforms";
import { SaveTransaction } from "ynab";

describe("transformYNAB()", () => {
  const row = {
    account_id: "account",
    date: new Date("2023-05-04"),
    amount: 2,
    payee_id: "payee",
    category_id: "category",
    memo: "memo",
    cleared: SaveTransaction.ClearedEnum.Cleared,
    approved: false,
    flag_color: SaveTransaction.FlagColorEnum.Red,
    import_id: "import",
    split_id: null,
    split_memo: null,
    split_payee_id: null,
  };
  const expected = {
    account_id: "account",
    date: "2023-05-04",
    amount: 2,
    payee_id: "payee",
    category_id: "category",
    memo: "memo",
    cleared: SaveTransaction.ClearedEnum.Cleared,
    approved: false,
    flag_color: SaveTransaction.FlagColorEnum.Red,
    import_id: "import",
    subtransactions: null,
  };
  it("transforms full transaction MartTableRow to YNAB's SaveTransaction", () => {
    expect(transformYNAB([row])).toEqual([expected]);
  });
  it("transaction split transactions MartTableRows to YNAB's SaveTransaction", () => {
    // template multiple rows to simulate subtransactions in a split transaction
    const split_params = {
      split_id: "split",
      split_memo: row.memo,
      split_payee_id: row.payee_id,
    };
    const rows: MartTableRow[] = [
      {
        ...row,
        category_id: "category1",
        payee_id: "payee1",
        memo: "memo1",
        amount: 1,
        ...split_params,
      },
      {
        ...row,
        category_id: "category2",
        payee_id: "payee2",
        memo: "memo2",
        amount: 2,
        ...split_params,
      },
      {
        ...row,
        category_id: "category3",
        payee_id: "payee3",
        memo: "memo3",
        amount: 3,
        ...split_params,
      },
    ];
    expect(transformYNAB(rows)).toEqual([
      {
        ...expected,
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
