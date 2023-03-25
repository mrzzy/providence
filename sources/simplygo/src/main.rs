/*
 * Providence
 * SimplyGo Source
*/

use chrono::{Local, NaiveDate};
use chrono_tz::Singapore;
use clap::Parser;
use simplygo_src::{models::Record, SimplyGo};
use std::fs::File;

#[derive(Parser, Debug)]
#[command(about)]
struct Cli {
    /// Username used to login on SimplyGo.
    #[arg(long, env = "SIMPLYGO_SRC_USERNAME")]
    username: String,
    /// Password used to login on SimplyGo.
    #[arg(long, env = "SIMPLYGO_SRC_PASSWORD")]
    password: String,
    #[arg(long)]
    /// Date starting period from which trips are scraped from SimplyGo in format YYYY-MM-DD
    trips_from: String,
    #[arg(long)]
    /// Date ending period from which trips are scraped from SimplyGo in format YYYY-MM-DD
    trips_to: String,
    /// Path of the output JSON file to write scraped data to.
    #[arg(long, default_value = "simplygo.json")]
    output: String,
}

fn main() {
    // parse command line args
    let args = Cli::parse();
    // parse trip query dates
    let (date_fmt, date_err_msg) = ("%Y-%m-%d", "Could not parse date in format YYYY-MM-DD.");
    let trips_from = NaiveDate::parse_from_str(&args.trips_from, date_fmt).expect(date_err_msg);
    let trips_to = NaiveDate::parse_from_str(&args.trips_to, date_fmt).expect(date_err_msg);

    // login on simplygo with credentials
    let simplygo = SimplyGo::new().login(&args.username, &args.password);
    // scrape data into record
    let cards = simplygo.cards();
    let record = Record {
        scraped_on: Local::now().with_timezone(&Singapore),
        trips_from,
        trips_to,
        trips: cards
            .iter()
            .flat_map(|card| simplygo.trips(card, &trips_from, &trips_to))
            .collect(),
        cards,
    };

    // write scraped record as json
    let json = File::create(&args.output)
        .unwrap_or_else(|e| panic!("Could not open {} for writing: {}", args.output, e));
    serde_json::to_writer(json, &record)
        .unwrap_or_else(|e| panic!("Failed to write data records to {}: {}", args.output, e));
}
