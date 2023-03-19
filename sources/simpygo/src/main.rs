/*
 * Providence
 * SimplyGo Source
*/

use std::env;

use simplygo_src::SimplyGo;

fn main() {
    let simplygo = SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
    println!("{:?}", simplygo);
}
