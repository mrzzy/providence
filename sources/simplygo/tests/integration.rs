/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

// NOTE: The following integration tests expect these environment variables to be set:
// - `SIMPLYGO_SRC_USERNAME`
// - `SIMPLYGO_SRC_PASSWORD`
// - `AWS_DEFAULT_REGION`
// - `AWS_ACCESS_KEY_ID`
// - `AWS_SECRET_ACCESS_KEY`

use std::os::unix::prelude::MetadataExt;
use std::{env, io::Write};

use assert_cmd::Command;
use assert_fs::NamedTempFile;
use aws_sdk_s3::types::{CreateBucketConfiguration, Delete, ObjectIdentifier};
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
/// Do not pass the leading '/' in object key.
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

/// Create a S3 bucket in SG region with the given s3 client name bucket name.
async fn create_s3_bucket(s3: &aws_sdk_s3::Client, bucket: &str) {
    s3.create_bucket()
        .bucket(bucket)
        .create_bucket_configuration(
            CreateBucketConfiguration::builder()
                // ap-southeast-1: singapore
                .location_constraint(aws_sdk_s3::types::BucketLocationConstraint::ApSoutheast1)
                .build(),
        )
        .send()
        .await
        .unwrap_or_else(|e| panic!("Could not create test s3 bucket {}: {:?}", bucket, e));
}

/// Delete S3 bucket with the given name, along with any object it stores.
async fn delete_s3_bucket(s3: &aws_sdk_s3::Client, bucket: &str) {
    // list contents of s3 bucket for deletion
    let response = s3
        .list_objects_v2()
        .bucket(bucket)
        .send()
        .await
        .unwrap_or_else(|e| panic!("Failed to list objects in s3 bucket {}: {:?}", bucket, e));
    let object_ids = response
        .contents()
        .unwrap_or_default()
        .iter()
        .map(|object| {
            ObjectIdentifier::builder()
                .key(object.key().unwrap())
                .build()
        });

    // delete s3 bucket's objects
    let mut delete = Delete::builder();
    for object_id in object_ids {
        delete = delete.objects(object_id);
    }
    s3.delete_objects()
        .bucket(bucket)
        .delete(delete.build())
        .send()
        .await
        .unwrap_or_else(|e| panic!("Failed to delete objects in s3 bucket {}: {:?}", bucket, e));

    // delete s3 bucket
    s3.delete_bucket()
        .bucket(bucket)
        .send()
        .await
        .unwrap_or_else(|e| panic!("Failed to delete s3 bucket {}: {:?}", bucket, e));
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
// #[serial]
fn s3_sink_test() {
    // create test bucket
    let rt = build_runtime();
    let s3 = s3_client(&rt);
    let bucket = format!(
        "mrzzy-co-providence-simplygo-src-integration-{}",
        random_alphanum(8).to_lowercase(),
    );
    rt.block_on(create_s3_bucket(&s3, &bucket));

    // write object with s3 sink
    let test_key = "test";
    let s3_url = format!("s3://{}/{}", bucket, test_key);
    let mut sink = S3Sink::new(&s3_url);
    let test_value = b"value";
    sink.write_all(test_value).unwrap();
    sink.flush()
        .unwrap_or_else(|e| panic!("Failed to write test value to {}: {:?}", s3_url, e));

    // get & check written value
    assert_eq!(
        test_value.to_vec(),
        rt.block_on(get_s3(&s3, &bucket, &test_key))
    );

    // clean up test bucket
    rt.block_on(delete_s3_bucket(&s3, &bucket));
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
    // create test bucket
    let rt = build_runtime();
    let s3 = s3_client(&rt);
    let bucket = format!(
        "mrzzy-co-providence-simplygo-src-integration-{}",
        random_alphanum(8).to_lowercase(),
    );
    rt.block_on(create_s3_bucket(&s3, &bucket));

    // test: command succeeds
    let mut cmd = Command::cargo_bin("simplygo_src").unwrap();
    let test_key = "test";
    let s3_url = format!("s3://{}/{}", bucket, test_key);
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
    rt.block_on(get_s3(&s3, &bucket, &test_key));

    // clean up test bucket
    rt.block_on(delete_s3_bucket(&s3, &bucket));
}
