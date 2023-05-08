/*
 * Providence
 */

import pg from "pg";
import yargs from "yargs/yargs";

// parse command line args
const parser = yargs(process.argv.slice(2))
  .command(
    "$0 <dbHost> <tableId> <budgetId>",
    `YNAB Sink imports transactions from a table in AWS Redshift.

    Environment variables:
    - AWS_REDSHIFT_USER: Username used to authenticate with AWS Redshift.
    - AWS_REDSHIFT_PASSWORD: Password used to authenticate with AWS Redshift.
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
  if (
    !(
      "AWS_REDSHIFT_USER" in process.env &&
      "AWS_REDSHIFT_PASSWORD" in process.env
    )
  ) {
    console.error(
      "Missing expected environment variables providing AWS Redshift credentials."
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

  const results = await db.query(`SELECT * FROM ${schema}.${table} LIMIT 1;`);
  // TODO(mrzzy): call YNAB API with transactions

  process.exit();
})();
