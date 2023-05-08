/*
 * Providence
 * YNAB Sink
 * Transforms
 */

import { SaveTransaction } from "ynab";

/// Expected schema of the YNAB Sink mart table providing transactions to import.
export interface MartTableRow {
  import_id: string;
  account_id: string;
  date: Date;
  amount: number;
  payee_id: string;
  category_id: string;
  memo: string | string;
  cleared: SaveTransaction.ClearedEnum;
  approved: boolean;
  flag_color: SaveTransaction.FlagColorEnum | null;
  split_id: string | null;
  split_payee_id: string | null;
  split_memo: string | null;
}

/**
 * Transform transfactions in the given mart table rows into YNAB API SaveTransactions.
 *
 * Groups transactions with the same split_id as the subtransactions
 * of one parent split transaction.
 */
export function transformYNAB(rows: MartTableRow[]): SaveTransaction[] {
  // group subtransactions into splits
  const splits: { [k: string]: MartTableRow[] } = {};
  rows.forEach((row) => {
    // consider full transactions are a special case of split transaction with only 1 split.
    // full transactions will be grouped by import_id, which is unique by transaction.
    const group_id = row.split_id ?? row.import_id;
    splits[group_id] = (splits[group_id] ?? []).concat([row]);
  });

  // whether the given rows of a split comprise a split (true) or full (false) transaction.
  const isSplit = (rows: MartTableRow[]) => rows[0].split_id != null;
  return Object.values(splits).map((rows) => {
    return {
      account_id: rows[0].account_id,
      // obtain only date part of iso by clipping after 'T' delimiter
      date: rows[0].date.toISOString().split("T")[0],
      amount: rows
        .map(({ amount }) => amount)
        .reduce((sum, amount) => sum + amount),
      // category for split transactions is automatically set by YNAB.
      category_id: isSplit(rows) ? null : rows[0].category_id,
      payee_id: isSplit(rows) ? rows[0].split_payee_id : rows[0].payee_id,
      memo: isSplit(rows) ? rows[0].split_memo : rows[0].memo,
      cleared: rows[0].cleared,
      // all subtransactions must be approved for the parent split transaction
      // to be also considered to be approved.
      approved: rows
        .map(({ approved }) => approved)
        .reduce((prevApproved, approved) => prevApproved && approved),
      flag_color: rows[0].flag_color,
      import_id: rows[0].import_id,
      subtransactions: !isSplit(rows)
        ? null
        : rows.map(({ amount, payee_id, category_id, memo }) => {
            return { amount, payee_id, category_id, memo };
          }),
    };
  });
}
