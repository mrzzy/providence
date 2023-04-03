/*
 * Providence
 * SimplyGo Source
 * S3 Sink
*/

use std::io::{Error, ErrorKind, Result, Write};

use aws_sdk_s3::Client;
use tokio::runtime::{self, Runtime};
use url::Url;

/// Parse the given string as a s3:// URL into bucket name & path
fn parse_s3_url(s: &str) -> (String, String) {
    let url = Url::parse(s).unwrap_or_else(|e| panic!("Malformed URL: {}", e));
    // check url scheme & host (bucket)
    if url.scheme() != "s3" {
        panic!(
            "Expected scheme of S3 URL to be s3://, but received: {}",
            url.scheme()
        );
    }
    if !url.has_host() {
        panic!("Missing host component in S3 URL: {}", s);
    }

    (
        url.host_str().unwrap().to_owned(),
        // strip leading '/' in path
        url.path()[1..].to_owned(),
    )
}

/// Build an S3 client using config / credentials from environmennt variables.
pub fn s3_client(rt: &Runtime) -> Client {
    aws_sdk_s3::Client::new(&rt.block_on(aws_config::load_from_env()))
}

/// Sink that writes to AWS S3 in an object given by bucket & path.
/// Note that writes are buffered until flush() is called to commit writes to S3.
pub struct S3Sink {
    s3: Client,
    /// Name of the bucket to write to.
    bucket: String,
    /// Key / Path within the bucket specifying the object to write to.
    path: String,
    /// Sink writes to to buffer before committing them oneshot to AWS S3 on flush.
    buffer: Vec<u8>,
    /// Tokio async runtime used to run async S3 operations in blocking fashion
    rt: Runtime,
}
impl S3Sink {
    /// Construct a new S3 sink that writes to the object specified by the given S3 url.
    /// AWS Credentials should be passed via `AWS_SECRET_KEY_ID` & `AWS_SECRET_KEY_SECRET_KEY` env vars
    pub fn new(s3_url: &str) -> Self {
        let rt = runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();
        let (bucket, path) = parse_s3_url(s3_url);
        Self {
            s3: s3_client(&rt),
            bucket,
            path,
            buffer: vec![],
            rt,
        }
    }
}
impl Write for S3Sink {
    fn write(&mut self, buf: &[u8]) -> Result<usize> {
        // save to be written data to buffer
        self.buffer.extend_from_slice(buf);
        Ok(buf.len())
    }

    fn flush(&mut self) -> Result<()> {
        // write buffer to s3
        let result = match self.rt.block_on(
            self.s3
                .put_object()
                .bucket(&self.bucket)
                .key(&self.path)
                .body(self.buffer.clone().into())
                .send(),
        ) {
            Ok(_) => Ok(()),
            Err(e) => Err(Error::new(ErrorKind::Other, e)),
        };
        // clear written buffer
        self.buffer.clear();
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::panic;
    #[test]
    fn parse_s3_url_test() {
        let test_cases = [
            // s3 url, expecting error, parsed bucket, path
            ("s3://bucket/path", false, "bucket", "path"),
            ("s3://bucket/", false, "bucket", ""),
            ("s3://", true, "", ""),
            ("http://", true, "", ""),
            ("bucket/path", true, "", ""),
        ];

        test_cases
            .into_iter()
            .for_each(|(input, expect_err, bucket, path)| {
                assert_eq!(
                    expect_err,
                    panic::catch_unwind(|| {
                        let (actual_bucket, actual_path) = parse_s3_url(input);
                        assert_eq!(bucket, actual_bucket);
                        assert_eq!(path, actual_path);
                    })
                    .is_err()
                );
            });
    }
}
