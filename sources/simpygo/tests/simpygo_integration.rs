/*
 * Providence
 * SimplyGo Source
 * SimplyGo Integration Tests
*/

use std::env;

use simplygo_src::SimplyGo;

#[test]
fn simplygo_login_integration_test() {
    SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
}
