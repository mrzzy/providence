/*
 * Providence
 * SimplyGo Source
*/

use chrono::NaiveDate;
use clap::Parser;
use simplygo::SimplyGo;
use std::fs::{self, create_dir_all, File};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(about)]
struct Cli {
    /// Username used to login on SimplyGo.
    #[arg(long, env = "SIMPLYGO_SRC_USERNAME")]
    username: String,
    /// Password used to login on SimplyGo.
    #[arg(long, env = "SIMPLYGO_SRC_PASSWORD")]
    password: String,
    /// Date starting period from which trips are scraped from SimplyGo in format YYYY-MM-DD
    #[arg(long)]
    trips_from: String,
    /// Date ending period from which trips are scraped from SimplyGo in format YYYY-MM-DD
    #[arg(long)]
    trips_to: String,
    /// Path of the local directory on disk to write scraped HTML.
    /// By default writes to the directory 'out'.
    /// Creates the output directory if it does not already exist.
    #[arg(long, default_value = "out")]
    output_dir: PathBuf,
}

fn main() {
    // parse command line args
    let args = Cli::parse();
    // parse trip query dates
    let (date_fmt, date_err_msg) = ("%Y-%m-%d", "Could not parse date in format YYYY-MM-DD.");
    let trips_from = NaiveDate::parse_from_str(&args.trips_from, date_fmt).expect(date_err_msg);
    let trips_to = NaiveDate::parse_from_str(&args.trips_to, date_fmt).expect(date_err_msg);

    // login on simplygo with credentials
    let simplygo = SimplyGo::default().login(&args.username, &args.password);

    // create output directory if it does not already exist
    create_dir_all(&args.output_dir)
        .unwrap_or_else(|e| panic!("Could not create output directory: {}", e));

    // scrape & write cards manifest
    let cards = simplygo.cards();
    let cards_json_path = args.output_dir.join("cards.json");
    let cards_json = File::create(&cards_json_path).unwrap_or_else(|e| {
        panic!(
            "Could not open {} for writing: {}",
            cards_json_path.display(),
            e
        )
    });
    serde_json::to_writer(cards_json, &cards).unwrap_or_else(|e| {
        panic!(
            "Failed to write cards to {}: {}",
            cards_json_path.display(),
            e
        )
    });

    // scrape & write trip html for each card
    cards.iter().for_each(|card| {
        let path = args.output_dir.join(&card.id).with_extension("html");
        let html = simplygo.trips(card, &trips_from, &trips_to);
        fs::write(&path, html)
            .unwrap_or_else(|e| panic!("Failed to write scraped HTML to {}: {}", path.display(), e))
    })
}
