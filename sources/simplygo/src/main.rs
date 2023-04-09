/*
 * Providence
 * SimplyGo Source
*/

use chrono::{NaiveDate, Utc};
use clap::Parser;
use simplygo_src::S3Sink;
use simplygo_src::{models::Record, SimplyGo};
use std::fs::File;
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
    /// Path or S3 URL of the location to write output scraped data in JSON format.
    /// * Path writes the data as local file on disk.
    /// * S3 URL write the data as a blob on AWS S3 service:
    ///     - Requires AWS credentials to be provided via `AWS_ACCESS_KEY_ID` &
    ///         `AWS_SECRET_ACCESS_KEY` environment variables.
    ///     - Requires AWS Region to be set via `AWS_DEFAULT_REGION` environment variable.
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
        scraped_on: Utc::now(),
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
        s3_url if s3_url.starts_with("s3://") => Box::new(S3Sink::new(s3_url)),
        path => Box::new(
            File::create(path)
                .unwrap_or_else(|e| panic!("Could not open {} for writing: {}", args.output, e)),
        ),
    };
    serde_json::to_writer(&mut sink, &record)
        .unwrap_or_else(|e| panic!("Failed to write Record as JSON to Sink: {}", e));
    sink.flush()
        .unwrap_or_else(|e| panic!("Failed to commit Record to Sink: {}", e));
}
