/*
 * Providence
 * YNAB Sink
 * Transforms Unit Tests
 */

import { describe, expect, it } from "@jest/globals";
import { transformYNAB } from "./transforms";
import { SaveTransaction } from "ynab";

describe("transformYNAB()", () => {
  it("transforms full transaction MartTableRow to SaveTransaction", () => {
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
      subtransaction_group_id: null,
    };
    expect(transformYNAB([row])).toEqual([{ ...row, date: "2023-05-04" }]);
  });
});
