/*
 * Providence
 * SimplyGo Source
*/

use simplygo_src::SimplyGo;
use std::env;

fn main() {
    let simplygo = SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
    println!("{:?}", simplygo);
}
