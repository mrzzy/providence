/*
 * Providence
 * SimplyGo Source
 * RClone Sink
*/

use std::io::{Error, ErrorKind, Write};
use std::process::Command;

use tempfile::NamedTempFile;

/// Sink that writes written to an RClone Remote location specified by path.
/// Expects rclone binary to be accessible in PATH
/// Note that writes written to a local temporary file until flush() is called
/// to commit writes to Rclone Remote.
pub struct RCloneSink {
    rclone: Command,
    /// Temporary file to store writes before they are committed.
    buffer: NamedTempFile,
}
impl RCloneSink {
    // Create a new Rclone Sink that writes to given remote_path.
    /// * remote_path: in the format <RCLONE_REMOTE>:<REMOTE_PATH>
    pub fn new(remote_path: String) -> Self {
        let buffer = NamedTempFile::new().unwrap_or_else(|e| {
            panic!(
                "Unexpected error creating temporary file for writing: {}",
                e
            )
        });
        let rclone = Command::new("rclone");
        let mut sink = Self { rclone, buffer };
        sink.rclone.args([
            "copyto",
            sink.buffer
                .path()
                .to_str()
                .expect("Unable to convert name of temporary file to string"),
            &remote_path,
        ]);
        sink
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
        let result = match self.rclone.spawn() {
            Ok(_) => Ok(()),
            Err(e) => Err(Error::new(ErrorKind::Other, e)),
        };
        // cleanup temp file
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_test() {
        let remote_path = ":s3,key=value:/remote/path";
        let sink = RCloneSink::new(remote_path.to_string());
        assert_eq!(
            sink.rclone.get_args().collect::<Vec<_>>(),
            ["copyto", sink.buffer.path().to_str().unwrap(), remote_path,]
        )
    }

    #[test]
    fn write_test() {
        let remote_path = ":s3,key=value:/remote/path";
        let mut sink = RCloneSink::new(remote_path.to_string());
        sink.write(b"test").expect("Failed to write");
    }
}
