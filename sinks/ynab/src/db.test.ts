/*
 * Providence
 * YNAB Sink
 * Database Unit Tests
 */

import { jest, describe, expect, it } from "@jest/globals";
import { queryDBTable } from "./db";
import { modelTableRow } from "./testModels.js";

// mock to intercept calls to Postgres Client
interface Params {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}
const mockConnect = jest.fn();
const mockQuery = jest.fn(async () => {
  return {
    rows: [modelTableRow],
  };
});
jest.mock("pg", () => {
  return {
    __esModule: true,
    Client: function ({ host, port, database, user, password }: Params) {
      expect(host).toStrictEqual("host");
      expect(port).toStrictEqual(5432);
      expect(database).toStrictEqual("database");
      expect(user).toStrictEqual("user");
      expect(password).toStrictEqual("password");

      return {
        connect: mockConnect,
        query: mockQuery,
      };
    },
  };
});

describe("queryDBTable()", () => {
  it("Builds Client and queries Database for Table Rows", async () => {
    expect(
      await queryDBTable(
        "host:5432",
        "database.schema.table",
        "user",
        "password"
      )
    ).toEqual([modelTableRow]);
    // check we made the right SQL query
    expect(mockQuery.mock.calls[0].at(0)).toEqual(
      "SELECT * FROM schema.table;"
    );
    // check that we called connect() on the Client
    expect(mockConnect.mock.calls.length).toEqual(1);
  });
});