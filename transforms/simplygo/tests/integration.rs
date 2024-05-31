/*
 * Providence
 * SimplyGo Transform
 * Integration Tests
*/

use std::fs;

use assert_cmd::Command;
use assert_fs::NamedTempFile;
use bytes::Bytes;
use parquet::arrow::arrow_reader::ParquetRecordBatchReader;

/// Test integration with raw data format exported from `simplygo_src`.
#[test]
fn cli_integration_simplygo_src() {
    let out_path = NamedTempFile::new("out.pq").unwrap();
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

    // read a single record from written parquet file
    ParquetRecordBatchReader::try_new(Bytes::from(fs::read(&out_path).unwrap()), 1)
        .unwrap()
        .next()
        .unwrap()
        .unwrap();
}
