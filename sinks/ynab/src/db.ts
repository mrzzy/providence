/*
 * Providence
 * YNAB Sink
 * Database
 */

import * as pg from "pg";
import { SaveTransaction } from "ynab";

/// Expected schema of the table providing transactions to import.
export interface TableRow {
  import_id: string;
  account_id: string;
  date: Date;
  // amount should be an integer as expected by the YNAB API
  amount: number;
  payee_id: string;
  category_id: string;
  memo: string | null;
  cleared: SaveTransaction.ClearedEnum;
  approved: boolean;
  flag_color: SaveTransaction.FlagColorEnum | null;
  split_id: string | null;
  split_payee_id: string | null;
  split_memo: string | null;
}

/**
 * Query the database table for table rows.
 *
 * @param dbHost <HOSTNAME>:<PORT> the database server is listenin on.
 * @param tableId DATABASE>.<SCHEMA>.<TABLE> specifying the database table to query from.
 * @param user Username credential used to authenticate with the database.
 * @param password Password credential used to authenticate with the database.
 * @param begin Begin of the date range to query.
 * @param end End of the date range to query.
 * @returns queried data as table rows.
 */
export async function queryDBTable(
  dbHost: string,
  tableId: string,
  user: string,
  password: string,
  begin: Date,
  end: Date
): Promise<TableRow[]> {
  // connect to the database with db client
  const [host, portStr] = dbHost.split(":");
  const [database, schema, table] = tableId.split(".");
  const db = new pg.Client({
    host,
    port: Number.parseInt(portStr),
    database,
    user,
    password,
  });
  // a connection has to be made first before querying, otherwise queries will
  // end up stuck in the query queue and never evaluate.
  await db.connect();
  // query the database table for transactions
  return (
    // redshift does not support $n parameterised queries, so we interpolate
    // user args directly into the sql query here. Although this poses a possible
    // SQL injection vulnerability, the risk is mitigated as this is a cli tool
    // and not meant to be exposed to external users with potentially malicious intent.
    (
      await db.query(
        `SELECT * FROM ${schema}.${table} WHERE updated_at BETWEEN '${begin.toISOString()}' AND '${end.toISOString()}';`
      )
    ).rows
  );
}
