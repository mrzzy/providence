/*
 * Providence
 * YNAB Sink
 * YNAB
 */

import { SaveTransaction } from "ynab";
import { API, SaveTransactionsResponse } from "ynab";
import { TableRow } from "./db.js";

/**
 * Transform transfactions in the given table rows into YNAB API SaveTransactions.
 *
 * Groups transactions with the same split_id as the subtransactions
 * of one parent split transaction.
 */
export function toYNABTransactions(rows: TableRow[]): SaveTransaction[] {
  // group subtransactions into splits
  const splits: { [k: string]: TableRow[] } = {};
  rows.forEach((row) => {
    // consider full transactions are a special case of split transaction with only 1 split.
    // full transactions will be grouped by import_id, which is unique by transaction.
    const group_id = row.split_id ?? row.import_id;
    splits[group_id] = (splits[group_id] ?? []).concat([row]);
  });

  // whether the given rows of a split comprise a split (true) or full (false) transaction.
  const isSplit = (rows: TableRow[]) => rows[0].split_id != null;
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

/**
 * Create transactions in the given YNAB budget, ignoring duplicates.
 *
 * @param ynab YNAB API client used to make the create transaction API request.k
 * @param budgetId ID of the YNAB budget to create transactions within.
 * @param List of transactions to create.
 * @throws Error if one is encountered trying to create transactions.
 */
export async function createYNABTransactions(
  ynab: API,
  budgetId: string,
  transactions: SaveTransaction[]
) {
  let response: SaveTransactionsResponse | null = null;
  try {
    response = await ynab.transactions.createTransactions(budgetId, {
      transactions,
    });
  } catch (error) {
    throw `Failed to create transactions with YNAB API: ${JSON.stringify(
      error
    )}`;
  }

  const duplicateIds = response.data.duplicate_import_ids;
  if (duplicateIds != null && duplicateIds.length > 0) {
    console.warn(`Skipping duplicate import IDs: ${duplicateIds}`);
  }
}
