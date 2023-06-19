/*
 * Providence
 * SimplyGo Source
 * RClone Sink
*/

use std::io::{Error, ErrorKind, Write};
use std::process::Command;

use tempfile::NamedTempFile;

/// Sink that writes written to an RClone location specified by target_path.
/// Expects rclone binary to be accessible in PATH
/// Note that writes written to a local temporary file until flush() is called
/// to commit writes to Rclone Remote.
pub struct RCloneSink {
    target_path: String,
    /// Temporary file to store writes before they are committed.
    buffer: NamedTempFile,
}
impl RCloneSink {
    /// Create a new Rclone Sink that writes to given target_path.
    /// target_path: either a local path or a remote path  in the format rclone
    /// <RCLONE_REMOTE>:<REMOTE_PATH>
    pub fn new(target_path: &str) -> Self {
        Self {
            target_path: target_path.to_string(),
            buffer: NamedTempFile::new().unwrap_or_else(|e| {
                panic!(
                    "Unexpected error creating temporary file for writing: {}",
                    e
                )
            }),
        }
    }

    fn buffer_path(&self) -> String {
        self.buffer
            .path()
            .to_str()
            .expect("Unable to convert name of temporary file to string")
            .to_string()
    }
}
impl Write for RCloneSink {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        self.buffer.write(buf)
    }
    fn flush(&mut self) -> std::io::Result<()> {
        // ensure any buffered writes are synced to file
        self.buffer.flush()?;
        // copy written file to rclone remote
        let result = match Command::new("rclone")
            .args(["copyto", &self.buffer_path(), &self.target_path])
            .spawn()
        {
            Ok(_) => Ok(()),
            Err(e) => Err(Error::new(ErrorKind::Other, e)),
        };
        // cleanup temp file
        result
    }
}
#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::*;

    #[test]
    fn new_test() {
        let target_path = ":s3,key='value':/remote/path";
        let sink = RCloneSink::new(target_path);
        assert!(Path::new(&sink.buffer_path()).exists());
    }

    #[test]
    fn write_test() {
        let target_path = ":s3,key='value':/remote/path";
        let mut sink = RCloneSink::new(target_path);
        sink.write(b"test").expect("Failed to write");
    }
}
