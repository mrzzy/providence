/*
 * Providence
 * SimplyGo Integration Tests
 * MinIO Testcontainer
*/

use std::collections::HashMap;
use testcontainers::{core::WaitFor, Image, ImageArgs};

pub const MINIO_API_PORT: u16 = 9000;

#[derive(Debug)]
pub struct MinIO {
    env_vars: HashMap<String, String>,
}
impl Default for MinIO {
    fn default() -> Self {
        Self {
            env_vars: HashMap::from([
                (
                    "MINIO_ADDRESS".to_string(),
                    format!("0.0.0.0:{}", MINIO_API_PORT),
                ),
            ]),
        }
    }
}
impl Image for MinIO {
    type Args = MinIOServerArgs;

    fn name(&self) -> String {
        "minio/minio".to_owned()
    }
    fn tag(&self) -> String {
        // TODO(mrzzy): renovate upgrade
        "RELEASE.2023-06-09T07-32-12Z".to_owned()
    }
    fn ready_conditions(&self) -> Vec<WaitFor> {
        vec![WaitFor::message_on_stdout("API:")]
    }
    fn env_vars(&self) -> Box<dyn Iterator<Item = (&String, &String)> + '_> {
        Box::new(self.env_vars.iter())
    }
    fn expose_ports(&self) -> Vec<u16> {
        vec![MINIO_API_PORT]
    }
}

#[derive(Debug, Clone)]
pub struct MinIOServerArgs {
    pub dir: String,
}
impl Default for MinIOServerArgs {
    fn default() -> Self {
        Self {
            dir: "/data".to_owned(),
        }
    }
}
impl ImageArgs for MinIOServerArgs {
    fn into_iterator(self) -> Box<dyn Iterator<Item = String>> {
        Box::new(vec!["server".to_owned(), self.dir.to_owned()].into_iter())
    }
}
