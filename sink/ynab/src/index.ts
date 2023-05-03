/*
 * Providence
 * YNAB Sink
 */

import yargs from "yargs/yargs";

// parse command line args & env vars
const parser = yargs(process.argv.slice(2))
  .command(
    "$0 <db_host> <table_id> <budget_id>",
    `YNAB Sink writes transactions from SQL database into YNAB.

    Environment variables are used to pass database credentials:
    - DB_USERNAME: Username used to authenticate with the database.
    - DB_PASSWORD: Password used to authenticate with the database.
    `,
    (yargs) => {
      yargs.positional("db_host", {
        describe:
          "<HOSTNAME>:<PORT> Database host to retrieve transactions from.",
        type: "string",
      });
      yargs.positional("table_id", {
        describe:
          "<DATABASE>.<SCHEMA>.<TABLE> Table to retrieve transactions from.",
        type: "string",
      });
      yargs.positional("budget_id", {
        describe:
          "YNAB Budget ID specifying the budget to write transactions to.",
        type: "string",
      });
    }
  )
  .demandCommand();
if (!("DB_USERNAME" in process.env && "DB_PASSWORD" in process.env)) {
  parser.showHelp();
  process.exit(1);
}
