/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

// NOTE: The following integration tests expect these environment variables to be set:
// - `SIMPLYGO_SRC_USERNAME`
// - `SIMPLYGO_SRC_PASSWORD`
// and access to:
// - working Docker installation via the the `docker` CLI
// - `rclone` binary.

use std::io::{Error, ErrorKind};
use std::process::Command;
use std::thread::sleep;
use std::{env, io::Write};

use assert_cmd::Command as AssertCmd;
use std::time::Duration;
use tempfile::NamedTempFile;
use testcontainers::clients::Cli;
use testcontainers::Container;

use simplygo_src::{RCloneSink, SimplyGo};

mod minio;
use minio::{MinIO, MINIO_API_PORT};

// Test Utilities
/// Spin up a Minio test container with the given test container client for
/// testing with rclone.
/// Returns MinIO Testcontainer & the rclone connection string that can be
/// use to interact with the MinIO instance.
fn run_minio(client: &Cli) -> (Container<MinIO>, String) {
    let minio = client.run(MinIO::default());

    // get external port mapped to minio's s3 api port
    let port = minio.get_host_port_ipv4(MINIO_API_PORT);
    (
        minio,
        format!(
            ":s3,provider='Minio',access_key_id='{}',secret_access_key='{}',endpoint='http://localhost:{}':",
            // default credentials used by minio container
            "minioadmin", "minioadmin", port
        )
    )
}

/// Create director with `rclone mkdir` at the given path.
/// Used to create buckets when working cloud storage.
fn mkdir(target_dir: &str) {
    Command::new("rclone")
        .args(["mkdir", target_dir])
        .spawn()
        .unwrap_or_else(|e| panic!("Could not rclone mkdir: {}", e));
}

/// Wait for the given path to exist by running `rclone ls` repeatedly
/// Retries 5 times at intervals of 50 ms each, after which it gives up and panics.
fn wait_rclone_path(target_path: &str) {
    assert!(
        (1..=5)
            .map(|_| {
                let out = Command::new("rclone").args(["ls", &target_path]).output()?;
                match out.status.success() {
                    true => Ok(()),
                    false => {
                        sleep(Duration::from_millis(50));
                        Err(Error::new(
                            ErrorKind::NotFound,
                            "rclone ls could not locate test value",
                        ))
                    }
                }
            })
            .any(|result| result.is_ok()),
        "Timeout waiting for path: {}",
        target_path,
    );
}

// Integration Tests
/// Test integration with SimplyGo
#[test]
fn simplygo_login_test() {
    SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
}

/// Test writing to Rclone sink
#[test]
fn rclone_sink_test() {
    let docker = Cli::docker();
    let (_minio, rclone_conn_str) = run_minio(&docker);

    // create test bucket with rclone
    let test_bucket = format!("{}/test", rclone_conn_str);
    mkdir(&test_bucket);

    // write test value via rclone sink
    let target_path = format!("{}/key", test_bucket);
    let mut sink = RCloneSink::new(&target_path);
    let test_value = "value";
    sink.write_all(test_value.as_bytes())
        .and_then(|()| sink.flush())
        .unwrap_or_else(|e| panic!("Failed to write test value via Rclone sink: {}", e));

    // wait for minio to reflect the write
    wait_rclone_path(&target_path);

    // get & check written value
    let out = Command::new("rclone")
        .args(["cat", &target_path])
        .output()
        .expect("Failed to run rclone cat");
    assert!(
        out.status.success(),
        "Failed to get value written by Rclone Sink: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), test_value);
}

/// Test CLI scrape & write to file
#[test]
fn cli_output_file_test() {
    // test: command succeeds
    let mut cmd = AssertCmd::cargo_bin("simplygo_src").unwrap();
    let out_file = NamedTempFile::new().unwrap();
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
    assert!(out_file.as_file().metadata().unwrap().len() > 0);
    out_file.close().unwrap();
}

/// Test CLI scrape & write to Minio via Rclone Sink
#[test]
fn cli_output_rclone_minio_test() {
    let docker = Cli::docker();
    let (_minio, rclone_conn_str) = run_minio(&docker);

    // create test bucket with rclone
    let test_bucket = format!("{}/test", rclone_conn_str);
    mkdir(&test_bucket);

    // test: command succeeds
    let mut cmd = AssertCmd::cargo_bin("simplygo_src").unwrap();
    let rclone_path = format!("{}/key", test_bucket);
    let assert_cli = cmd
        .args(&[
            "--trips-from",
            "2023-02-22",
            "--trips-to",
            "2023-02-22",
            "--output",
            &rclone_path,
        ])
        .assert();
    assert_cli.success();

    // test: we actually wrote something on Minio
    wait_rclone_path(&rclone_path);
}
