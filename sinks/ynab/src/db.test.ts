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
        "password",
        new Date("2023-05-12 00:00:00"),
        new Date("2023-05-12 23:59:59")
      )
    ).toEqual([modelTableRow]);
    // check we made the right SQL query
    expect(mockQuery.mock.calls[0]).toEqual([
      'SELECT * FROM $1.$2 WHERE "date" BETWEEN $3 AND $4;',
      [
        "schema",
        "table",
        "2023-05-11T16:00:00.000Z",
        "2023-05-12T15:59:59.000Z",
      ],
    ]);
    // check that we called connect() on the Client
    expect(mockConnect.mock.calls.length).toEqual(1);
  });
});
