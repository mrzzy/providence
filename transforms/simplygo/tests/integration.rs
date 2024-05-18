/*
 * Providence
 * SimplyGo Transform
 * Integration Tests
*/

use std::fs;

use assert_cmd::Command;
use assert_fs::NamedTempFile;

/// Test integration with raw data format exported from `simplygo_src`.
#[test]
fn cli_integration_simplygo_src() {
    let out_path = NamedTempFile::new("out.csv").unwrap();
    Command::cargo_bin("simplygo_tfm")
        .unwrap()
        .args(&[
            "--input-dir",
            concat!(env!("CARGO_MANIFEST_DIR"), "/resources/raw"),
            "--output",
            out_path.to_str().unwrap(),
        ])
        .assert()
        .success();

    println!("{}", fs::read_to_string(&out_path).unwrap());
    let mut out_csv = csv::Reader::from_path(out_path)
        .unwrap_or_else(|e| panic!("Failed to read out.csv: {}", e));
    // check output csv headers
    let headers = out_csv
        .headers()
        .unwrap_or_else(|e| panic!("Failed to parse headers from out.csv: {}", e));
    assert_eq!(
        headers,
        vec![
            "card_id",
            "card_name",
            "cost_sgd",
            "source",
            "destination",
            "mode",
            "posting_ref",
            "trip_id",
            "traveled_on",
            "scraped_on",
            "transformed_on"
        ]
    );
    assert_eq!(out_csv.records().count(), 1);
}
