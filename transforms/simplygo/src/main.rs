/*
 * Providence
 * SimplyGo Transform
*/

use std::{
    fs::{self, File},
    path::PathBuf,
};

use chrono::Utc;
use clap::Parser;
use simplygo::{models::Card, parsing::parse_trips};

use simplygo_tfm::*;

/// SimplyGo Transform extracts tabular trip data from raw data scraped by `simplygo_src`.
#[derive(Parser, Debug)]
struct Cli {
    /// Input Directory of raw SimplyGo data scraped by `simplygo_src`
    /// to extract SimplyGo trip data from.
    #[arg(long)]
    input_dir: PathBuf,

    /// Path of the output CSV to output extracted trip data.
    #[arg(long, default_value = "out.csv")]
    output: PathBuf,
}

fn main() {
    // parse program arguments
    let args = Cli::parse();

    // determine when data was scraped by checking manifest modtime
    let cards_json = File::open(args.input_dir.join("cards.json"))
        .expect("Failed to open expected cards.json manifest ");
    let scraped_on = to_sgt(
        cards_json
            .metadata()
            .unwrap_or_else(|e| panic!("Failed to query cards.json metadata: {}", e))
            .modified()
            .unwrap_or_else(|e| panic!("Unable to get modified time of cards.json: {}", e))
            .into(),
    );

    // timestamp when the trip data was transformed by this program
    let transformed_on = to_sgt(Utc::now());

    // read cards.json manifest in scraped data directory
    let cards: Vec<Card> = serde_json::from_reader(cards_json)
        .unwrap_or_else(|e| panic!("Failed to parse cards.json: {}", e));

    let mut out_csv = csv::Writer::from_path(args.output)
        .unwrap_or_else(|e| panic!("Failed to open output csv for writing: {}", e));
    cards.iter().for_each(|card| {
        // extract trip data from scraped html for each card
        let html = fs::read_to_string(args.input_dir.join(&card.id).with_extension("html"))
            .unwrap_or_else(|e| {
                panic!("Failed to open scraped HTML for card id {}: {}", card.id, e)
            });
        let trips = parse_trips(&card.id, &html);
        // flatten trip into cardinality: 1 trip leg = 1 row
        let records = flatten_records(card, &trips, &scraped_on, &transformed_on);
        // write record to output csv
        records.into_iter().for_each(|r| {
            out_csv
                .serialize(r)
                .unwrap_or_else(|e| panic!("Failed to write record to output CSV: {}", e))
        });
    });
}