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
const mockEnd = jest.fn();
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
        end: mockEnd,
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
        "password",
        new Date("2023-05-11T00:00:00Z"),
        new Date("2023-05-11T23:59:59Z")
      )
    ).toEqual([modelTableRow]);
    // check we made the right SQL query
    expect(mockQuery.mock.calls[0]).toEqual([
      `SELECT * FROM schema.table WHERE updated_at BETWEEN '2023-05-11T00:00:00.000Z' AND '2023-05-11T23:59:59.000Z';`,
    ]);
    // check that we called connect() on the Client
    expect(mockConnect.mock.calls.length).toEqual(1);
    // check that we closed the db connection by calling end() on the Client
    expect(mockEnd.mock.calls.length).toEqual(1);
  });
});
