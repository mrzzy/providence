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
 * of one split transaction.
 */
export function transformYNAB(rows: MartTableRow[]): SaveTransaction[] {
  const datedRows = rows.map(({ date, ...params }) => {
    return {
      ...params,
      // convert date to ISO format: YYYY-MM-DD, full ISO string has time after "T"
      date: date.toISOString().split("T")[0],
    };
  });
  // full, non-split transactions
  const transactions: SaveTransaction[] = datedRows.filter(
    ({ split_id }) => split_id == null
  );

  // group subtransactions into splits
  const splits: { [k: string]: typeof datedRows } = {};
  datedRows.forEach((row) => {
    if (row.split_id != null) {
      splits[row.split_id] = (splits[row.split_id] ?? []).concat([row]);
    }
  });

  // derive parent, subtransactions in split transaction
  const splitTransactions: SaveTransaction[] = Object.values(splits).map(
    (subRows) => {
      return {
        account_id: subRows[0].account_id,
        date: subRows[0].date,
        amount: subRows
          .map(({ amount }) => amount)
          .reduce((sum, amount) => sum + amount),
        payee_id: subRows[0].payee_id,
        memo: subRows[0].memo,
        cleared: subRows[0].cleared,
        // all subtransactions must be approved for the parent split transaction
        // to be also considered to be approved.
        approved: subRows
          .map(({ approved }) => approved)
          .reduce((prevApproved, approved) => prevApproved && approved),
        flag_color: subRows[0].flag_color,
        import_id: subRows[0].import_id,
        subtransactions: subRows.map(
          ({ amount, payee_id, category_id, memo }) => {
            return { amount, payee_id, category_id, memo };
          }
        ),
      };
    }
  );
  return transactions.concat(splitTransactions);
}
