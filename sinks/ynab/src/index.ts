/*
 * Providence
 * YNAB Sink
 */

import yargs from "yargs/yargs";
import { API } from "ynab";
import { createYNABTransactions, toYNABTransactions } from "./ynab.js";
import { queryDBTable } from "./db.js";

// parse command line args
// 2 - skip 'node' & 'index.ts' in argv
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

// wrap in anonymous async function so that we can use "top-level" await
(async function () {
  const argv = parser.parseSync();
  // read database credentials from env vars
  const [redshift_user, redshift_password, ynab_token] = [
    "AWS_REDSHIFT_USER",
    "AWS_REDSHIFT_PASSWORD",
    "YNAB_ACCESS_TOKEN",
  ].map((key) => process.env[key]);
  if (
    redshift_user == null ||
    redshift_password == null ||
    ynab_token == null
  ) {
    console.error(
      "Missing expected environment variables providing credentials."
    );
    parser.showHelp();
    process.exit(1);
  }
  // query database for table rows
  const rows = await queryDBTable(
    argv.dbHost as string,
    argv.tableId as string,
    redshift_user,
    redshift_password
  );
  // write transactions using the YNAB API
  createYNABTransactions(
    new API(ynab_token),
    argv.budgetId as string,
    toYNABTransactions(rows)
  );
  process.exit();
})();
