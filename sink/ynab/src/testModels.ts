/*
 * Providence
 * YNAB Sink
 * Shared Testing Objects
 */

import { SaveTransaction } from "ynab";

export const modelSaveTransaction = {
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

export const modelTableRow = {
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
