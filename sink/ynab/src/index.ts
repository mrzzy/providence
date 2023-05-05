/*
 * Providence
 * YNAB Sink
 */

import pg from "pg";
import yargs from "yargs/yargs";
import { SaveTransaction, TransactionsSummary } from "ynab";

/// Expected schema of the YNAB Sink mart table providing transactions to import.
interface MartTableRow {
  account_id: string;
  date: Date;
  amount: number;
  payee_id: string;
  category_id: string;
  memo: string;
  cleared: TransactionsSummary.ClearedEnum;
  approved: boolean;
  flag_color: TransactionsSummary.FlagColorEnum;
  import_id: string;
  subtransaction_group_id: string;
}

/**
 * Transform transfactions in the given mart table rows into YNAB API SaveTransactions.
 *
 * Groups transactions with the same subtransaction_group_id as the subtransactions
 * of one split transaction.
 */
function transformYNAB(rows: MartTableRow[]): SaveTransaction[] {
  // convert date to ISO format: YYYY-MM-DD
  const datedRows = rows.map(({ date, ...params }) => {
    return {
      date: `${date.getUTCFullYear()}-${date.getMonth()}-${date.getDay()}`,
      ...params,
    };
  });
  // full, non-split transactions
  const transactions: SaveTransaction[] = datedRows.filter(
    ({ subtransaction_group_id }) => subtransaction_group_id == null
  );

  // group subtransactions into splits
  const splits: { [k: string]: typeof datedRows } = {};
  datedRows
    .filter(({ subtransaction_group_id }) => subtransaction_group_id != null)
    .forEach((row) => {
      splits[row.subtransaction_group_id] =
        splits[row.subtransaction_group_id] ?? [];
    });

  // derive parent, subtransactions in split transaction
  const splitTransactions: SaveTransaction[] = Object.values(splits).map(
    (subRows) => {
      return {
        account_id: subRows[0].account_id,
        date: subRows[0].date,
        amount: subRows.map(({ amount }) => amount).reduce((acc, x) => acc + x),
        payee_id: subRows[0].payee_id,
        memo: subRows[0].memo,
        cleared: subRows[0].cleared,
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
} // TODO(mrzzy): add test for this

// parse command line args
const parser = yargs(process.argv.slice(2))
  .command(
    "$0 <dbHost> <tableId> <budgetId>",
    `YNAB Sink imports transactions from YNAB Sink mart table in Postgres-compatible DB to YNAB.

  Environment variables are used to pass database credentials:
  - YNAB_SINK_DB_USERNAME: Username used to authenticate with the database.
  - YNAB_SINK_DB_PASSWORD: Password used to authenticate with the database.
  `,
    (yargs) => {
      yargs.positional("dbHost", {
        describe:
          "<HOSTNAME>:<PORT> Database host to retrieve transactions from.",
        type: "string",
      });
      yargs.positional("tableId", {
        describe:
          "<DATABASE>.<SCHEMA>.<TABLE> YNAB mart table to retrieve transactions from.",
        type: "string",
      });
      yargs.positional("budgetId", {
        describe:
          "YNAB Budget ID specifying the budget to write transactions to.",
        type: "string",
      });
    }
  )
  .demandCommand();
const argv = parser.parseSync();
// read database credentials from env vars
if (
  !(
    "YNAB_SINK_DB_USERNAME" in process.env &&
    "YNAB_SINK_DB_PASSWORD" in process.env
  )
) {
  console.error(
    "Missing expected environment variables providing DB credentials."
  );
  parser.showHelp();
  process.exit(1);
}

// connect to the database with db client
const [host, portStr] = (argv.dbHost as string).split(":");
const [database, schema, table] = (argv.tableId as string).split(".");
const db = new pg.Client({
  host,
  port: Number.parseInt(portStr),
  database,
  user: process.env.YNAB_SINK_DB_USERNAME,
  password: process.env.YNAB_SINK_DB_PASSWORD,
});
await db.connect();

const results = await db.query(`SELECT * FROM ${schema}.${table} LIMIT 1;`);
// TODO(mrzzy): call YNAB API with transactions

process.exit();
