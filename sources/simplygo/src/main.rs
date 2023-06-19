/*
 * Providence
 * SimplyGo Source
*/

use chrono::{Local, NaiveDate};
use clap::Parser;
use simplygo_src::{models::Record, RCloneSink, SimplyGo};
use std::io::Write;

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
    /// Path or Rclone remote location to write output scraped data in JSON format.
    /// * Path writes the data as local file on disk.
    /// * Rclone remote location in the format <RCLONE_REMOTE>:<REMOTE_PATH>
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
        scraped_on: Local::now().naive_local(),
        trips_from,
        trips_to,
        trips: cards
            .iter()
            .flat_map(|card| simplygo.trips(card, &trips_from, &trips_to))
            .collect(),
        cards,
    };

    // write scraped record as json
    let mut sink: Box<dyn Write> = match &args.output {
        target_path => Box::new(RCloneSink::new(&target_path)),
    };
    serde_json::to_writer(&mut sink, &record)
        .unwrap_or_else(|e| panic!("Failed to write Record as JSON to Sink: {}", e));
    sink.flush()
        .unwrap_or_else(|e| panic!("Failed to commit Record to Sink: {}", e));
}
