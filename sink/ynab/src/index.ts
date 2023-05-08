/*
 * Providence
 */

import pg from "pg";
import yargs from "yargs/yargs";
import { API, SaveTransactionsResponse } from "ynab";
import { transformYNAB } from "./transforms.js";

// parse command line args
const parser = yargs(process.argv.slice(2))
  .command(
    "$0 <dbHost> <tableId> <budgetId>",
    `YNAB Sink imports transactions from a table in AWS Redshift.

    Environment variables:
    - AWS_REDSHIFT_USER: Username used to authenticate with AWS Redshift.
    - AWS_REDSHIFT_PASSWORD: Password used to authenticate with AWS Redshift.
    - YNAB_ACCESS_TOKEN: Access Token used to authenticate with the YNAB API.
  `,
    (yargs) => {
      yargs.positional("dbHost", {
        describe:
          "<HOSTNAME>:<PORT> Database host to retrieve transactions from.",
        type: "string",
      });
      yargs.positional("tableId", {
        describe:
          "<DATABASE>.<SCHEMA>.<TABLE> AWS Redshift table to retrieve transactions from.",
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
(async function () {
  const argv = parser.parseSync();
  // read database credentials from env vars
  const hasEnvVars = [
    "AWS_REDSHIFT_USER",
    "AWS_REDSHIFT_PASSWORD",
    "YNAB_ACCESS_TOKEN",
  ]
    .map((envVar) => envVar in process.env)
    .reduce((hasAll, hasThis) => hasAll && hasThis);
  if (!hasEnvVars) {
    console.error(
      "Missing expected environment variables providing credentials."
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
    user: process.env.AWS_REDSHIFT_USER,
    password: process.env.AWS_REDSHIFT_PASSWORD,
  });
  await db.connect();

  // query the database table for transactions
  const results = await db.query(`SELECT * FROM ${schema}.${table};`);
  const transactions = transformYNAB(results.rows);

  // write transactions using the YNAB API
  const ynab = new API(process.env.YNAB_ACCESS_TOKEN!);
  let response: SaveTransactionsResponse | null = null;
  debugger;
  try {
    response = await ynab.transactions.createTransactions(
      argv.budgetId as string,
      {
        transactions,
      }
    );
  } catch (error) {
    console.error(
      `Failed to create transactions with YNAB API: ${JSON.stringify(error)}`
    );
    process.exit(1);
  }
  const duplicateIds = response.data.duplicate_import_ids;
  if (duplicateIds != null && duplicateIds.length > 0) {
    console.warn(`Skipping duplicate import IDs: ${duplicateIds}`);
  }
  process.exit();
})();
