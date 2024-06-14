/*
 * Providence
 * SimplyGo Transform
*/

use std::{
    fs::{self, File},
    io::prelude::*,
    io::BufWriter,
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

    /// Path of the output parquet file to write extracted trip data.
    #[arg(long, default_value = "out.pq")]
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
            .unwrap()
            .modified()
            .unwrap_or_else(|e| panic!("Unable to get modified time of cards.json: {}", e))
            .into(),
    );

    // timestamp when the trip data was transformed by this program
    let transformed_on = to_sgt(Utc::now());

    // read cards.json manifest in scraped data directory
    let cards: Vec<Card> = serde_json::from_reader(cards_json)
        .unwrap_or_else(|e| panic!("Failed to parse cards.json: {}", e));

    // write cards to output parquet
    let mut out = BufWriter::new(
        File::create(&args.output)
            .unwrap_or_else(|e| panic!("Failed to open output file for writing: {}", e)),
    );
    let n_written: usize = cards
        .iter()
        .map(|card| {
            // extract trip data from scraped html for each card
            let html = fs::read_to_string(args.input_dir.join(&card.id).with_extension("html"))
                .unwrap_or_else(|e| {
                    panic!("Failed to open scraped HTML for card id {}: {}", card.id, e)
                });
            let trips = parse_trips(&card.id, &html);
            // flatten trip into cardinality: 1 trip leg = 1 row
            let records = flatten_records(card, &trips, &scraped_on, &transformed_on);
            // only write to parquet if with nonzero batch of records to write
            // writing empty records will create a malformed parquet file
            if !records.is_empty() {
                write_parquet(&records, &mut out);
            }
            records.len()
        })
        .sum();
    // flush buffered writer
    out.flush()
        .unwrap_or_else(|e| panic!("Failed to write to file: {}", e));
    // remove output file if no records are written
    if n_written == 0 {
        println!("Warning: No trip records written.");
        fs::remove_file(args.output)
            .unwrap_or_else(|e| println!("Failed to remove empty output file: {}", e));
    }
}
