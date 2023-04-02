/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

use std::{env, io::Write};

use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};
use simplygo_src::{S3Sink, SimplyGo};
use tokio::runtime;

#[test]
fn simplygo_login_test() {
    SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
}

/// Generate a random alphanumeric string of given length
fn random_alphanum(len: u32) -> String {
    let mut rng = thread_rng();
    (0..len).map(|_| rng.sample(Alphanumeric) as char).collect()
}

#[test]
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
    let rt = runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let s3 = aws_sdk_s3::Client::new(&rt.block_on(aws_config::load_from_env()));
    assert_eq!(
        test_value,
        rt.block_on(async {
            s3.get_object()
                .bucket(&bucket)
                .key(&test_key)
                .send()
                .await
                .unwrap_or_else(|e| panic!("Failed to read test value from {}: {:?}", s3_url, e))
                .body
                .collect()
                .await
                .unwrap()
                .into_bytes()
        })
        .as_ref()
    );
    rt.block_on(s3.delete_object().bucket(&bucket).key(&test_key).send())
        .unwrap_or_else(|e| panic!("Could not clean up test value {}: {:?}", s3_url, e));
}
