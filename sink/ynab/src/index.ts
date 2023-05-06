/*
 * Providence
 * YNAB Sink
 */

import pg from "pg";
import yargs from "yargs/yargs";

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
(async function () {
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
})();
