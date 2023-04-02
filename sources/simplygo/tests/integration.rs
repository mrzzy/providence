/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

// NOTE: The following integration tests expect these environment variables to be set:
// - `SIMPLYGO_SRC_USERNAME`
// - `SIMPLYGO_SRC_PASSWORD`
// - `AWS_S3_TEST_BUCKET`
// - `AWS_ACCESS_KEY_ID`
// - `AWS_SECRET_ACCESS_KEY`

use std::os::unix::prelude::MetadataExt;
use std::{env, io::Write};

use assert_cmd::Command;
use assert_fs::NamedTempFile;
use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};
use serial_test::serial;
use simplygo_src::{s3_client, S3Sink, SimplyGo};
use tokio::runtime::{self, Runtime};

/// Generate a random alphanumeric string of given length
fn random_alphanum(len: u32) -> String {
    let mut rng = thread_rng();
    (0..len).map(|_| rng.sample(Alphanumeric) as char).collect()
}

/// Build a Tokio runtime for testing
fn build_runtime() -> Runtime {
    runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap()
}

/// Get the object stored in the given bucket and Key as a Vec of bytes
/// Include the leading '/' in given key referencing the root of the bucket.
async fn get_s3(s3: &aws_sdk_s3::Client, bucket: &str, key: &str) -> Vec<u8> {
    s3.get_object()
        .bucket(bucket)
        .key(key)
        .send()
        .await
        .unwrap_or_else(|e| panic!("Failedto read from S3: {:?}", e))
        .body
        .collect()
        .await
        .unwrap()
        .to_vec()
}

/// Test integration with SimplyGo
#[test]
#[serial]
fn simplygo_login_test() {
    SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
}

/// Test integration with AWS S3
#[test]
#[serial]
fn s3_sink_test() {
    // expects existing, already created S3 bucket
    let bucket = env::var("AWS_S3_TEST_BUCKET").unwrap();

    // write object with s3 sink
    let test_key = format!(
        "/providence/simplygo_src/s3_sink_test/{}",
        random_alphanum(8)
    );
    let s3_url = format!("s3://{}{}", bucket, test_key);
    let mut sink = S3Sink::new(&s3_url);
    let test_value = b"value";
    sink.write_all(test_value).unwrap();
    sink.flush()
        .unwrap_or_else(|e| panic!("Failed to write test value to {}: {:?}", s3_url, e));

    // get & check written value
    let rt = build_runtime();
    let s3 = s3_client(&rt);
    assert_eq!(
        test_value.to_vec(),
        rt.block_on(get_s3(&s3, &bucket, &test_key))
    );

    // clean up value
    rt.block_on(s3.delete_object().bucket(&bucket).key(&test_key).send())
        .unwrap_or_else(|e| panic!("Could not clean up test value {}: {:?}", s3_url, e));
}

/// Test CLI scrape & write to file
#[test]
#[serial]
fn cli_output_file_test() {
    // test: command succeeds
    let mut cmd = Command::cargo_bin("simplygo_src").unwrap();
    let out_file = NamedTempFile::new("simplygo.json").unwrap();
    let assert_cli = cmd
        .args(&[
            "--trips-from",
            "2023-02-22",
            "--trips-to",
            "2023-02-22",
            "--output",
            out_file.path().to_str().unwrap(),
        ])
        .assert();
    assert_cli.success();
    // test: we actually wrote something by checking file system
    assert!(out_file.metadata().unwrap().size() > 0);
    out_file.close().unwrap();
}

/// Test CLI scrape & write to AWS S3
#[test]
#[serial]
fn cli_output_s3_test() {
    // expects existing, already created S3 bucket
    let bucket = env::var("AWS_S3_TEST_BUCKET").unwrap();

    // test: command succeeds
    let mut cmd = Command::cargo_bin("simplygo_src").unwrap();
    let test_key = format!(
        "/providence/simplygo_src/s3_sink_test/{}",
        random_alphanum(8)
    );
    let s3_url = format!("s3://{}{}", bucket, test_key);
    let assert_cli = cmd
        .args(&[
            "--trips-from",
            "2023-02-22",
            "--trips-to",
            "2023-02-22",
            "--output",
            &s3_url,
        ])
        .assert();
    assert_cli.success();

    // test: we actually wrote something by retrieving from s3
    let rt = build_runtime();
    let s3 = s3_client(&rt);
    rt.block_on(get_s3(&s3, &bucket, &test_key));

    // clean up test object
    rt.block_on(s3.delete_object().bucket(&bucket).key(&test_key).send())
        .unwrap_or_else(|e| panic!("Could not clean up test value {}: {:?}", s3_url, e));
}
