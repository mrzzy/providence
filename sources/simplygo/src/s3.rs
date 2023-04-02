/*
 * Providence
 * SimplyGo Source
 * S3 Sink
*/

use std::io::{Error, ErrorKind, Result, Write};

use aws_sdk_s3::Client;
use tokio::runtime::{Builder, Runtime};
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

    (url.host_str().unwrap().to_owned(), url.path().to_owned())
}

/// Sink that writes to AWS S3 in an object given by bucket & path.
struct S3Sink<'a> {
    s3: &'a Client,
    /// Name of the bucket to write to.
    bucket: String,
    /// Key / Path within the bucket specifying the object to write to.
    path: String,
    /// Sink writes to to buffer before committing them oneshot to AWS S3 on flush.
    buffer: Vec<u8>,
    /// Tokio async runtime used to run async S3 operations in blocking fashion
    rt: Runtime,
}
impl<'a> S3Sink<'a> {
    pub fn new(s3: &'a Client, s3_url: &str) -> Self {
        let (bucket, path) = parse_s3_url(s3_url);
        Self {
            s3,
            bucket,
            path,
            buffer: vec![],
            rt: Builder::new_current_thread().enable_all().build().unwrap(),
        }
    }
}
impl Write for S3Sink<'_> {
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
            ("s3://bucket/path", false),
            ("s3://bucket/", false),
            ("s3://", true),
            ("http://", true),
            ("bucket/path", true),
        ];

        test_cases.into_iter().for_each(|(input, expect_err)| {
            println!("{}", input);
            assert_eq!(
                expect_err,
                panic::catch_unwind(|| parse_s3_url(input)).is_err()
            );
        });
    }
}
