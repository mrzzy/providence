/*
 * Providence
 * YNAB Sink
 */

import { describe, expect, it } from "@jest/globals";
import { checkEnv } from "./utility.js";

describe("checkEnv()", () => {
  it("Returns true when all env vars are set", () => {
    process.env.INDEX_TEST = "true";
    process.env.INDEX_TEST_2 = "true";
    expect(checkEnv(["INDEX_TEST"])).toBeTruthy();
    expect(checkEnv(["INDEX_TEST", "INDEX_TEST_2"])).toBeTruthy();
    expect(checkEnv(["INDEX_TEST_MISSING"])).toBeFalsy();
  });
});
