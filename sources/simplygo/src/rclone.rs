/*
 * Providence
 * SimplyGo Source
 * RClone Sink
*/

use std::io::Write;
use std::process::{Child, ChildStdin, Command, Stdio};

/// Sink that writes written to an RClone location specified by target_path.
/// Expects rclone binary to be accessible in PATH
/// Note that once write is committed with `flush()`, the sink is considered
/// closed and can no longer be writtened to.
pub struct RCloneSink {
    rclone: Child,
}
impl RCloneSink {
    /// Create a new Rclone Sink that writes to given target_path.
    /// target_path: either a local path or a remote path  in the format rclone
    /// <RCLONE_REMOTE>:<REMOTE_PATH>
    pub fn new(target_path: &str) -> Self {
        Self {
            // launch rclone rcat process that writes stdin to target path
            rclone: Command::new("rclone")
                .stdin(Stdio::piped())
                .args(["rcat", target_path])
                .spawn()
                .unwrap_or_else(|e| panic!("Could not run 'rclone rcat': {}", e)),
        }
    }

    fn stdin(&mut self) -> &mut ChildStdin {
        self.rclone
            .stdin
            .as_mut()
            .expect("Could not obtain 'rclone rcat' stdin for writing")
    }
}
impl Write for RCloneSink {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        self.stdin().write(buf)
    }

    fn flush(&mut self) -> std::io::Result<()> {
        let result = self.stdin().flush();
        // take and drop stdin stream to close it, causing rclone to terminate
        self.rclone
            .stdin
            .take()
            .expect("Could not obtain 'rclone rcat' stdin for closing");
        // wait for rclone to terminate
        self.rclone
            .wait()
            .expect("Could not wait for 'rclone rcat' as it is not running");
        result
    }
}

#[cfg(test)]
mod tests {

    use tempfile::NamedTempFile;

    use super::*;

    #[test]
    fn sink_test() {
        let target = NamedTempFile::new()
            .expect("Could not create temporary file: {}");
        let mut sink = RCloneSink::new(&target.path().to_string_lossy());
        sink.write(b"test").expect("Failed to write");
    }
}
