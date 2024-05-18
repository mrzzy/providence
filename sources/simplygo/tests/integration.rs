/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

// NOTE: The following integration tests expect these environment variables to be set:
// - `SIMPLYGO_SRC_USERNAME`
// - `SIMPLYGO_SRC_PASSWORD`

use simplygo::{models::Card, SimplyGo};
use std::{env, fs::File};

use assert_cmd::Command;
use assert_fs::TempDir;
use serial_test::serial;

/// Test integration with SimplyGo
#[test]
#[serial]
fn simplygo_login_test() {
    SimplyGo::default().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
}

/// Test CLI scrape & write to file
#[test]
#[serial]
fn cli_output_file_test() {
    // test: command succeeds
    let mut cmd = Command::cargo_bin("simplygo_src").unwrap();
    let out =
        TempDir::new().unwrap_or_else(|e| panic!("Failed to create temporary directory {}", e));
    let assert_cli = cmd
        .args(&[
            "--trips-from",
            "2023-02-22",
            "--trips-to",
            "2023-02-22",
            "--output-dir",
            out.path().to_str().unwrap(),
        ])
        .assert();
    assert_cli.success();
    // test: we actually wrote something by checking file system
    let cards: Vec<Card> = serde_json::from_reader(
        File::open(out.path().join("cards.json"))
            .expect("Missing expected cards.json file to be written to output-dir"),
    )
    .unwrap_or_else(|e| panic!("Failed to parse cards.json: {}", e));
    // check that at least 1 card was written
    assert!(cards.len() > 0);
    // checked that scraped html for each card is noempty
    assert!(cards.into_iter().all(|card| File::open(
        out.path().join(card.id).with_extension("html")
    )
    .unwrap_or_else(|e| panic!("Failed to open scraped HTML for card id :{}", e))
    .metadata()
    .unwrap_or_else(|e| panic!("Failed to get file metadata: {}", e))
    .len()
        > 0));
}
