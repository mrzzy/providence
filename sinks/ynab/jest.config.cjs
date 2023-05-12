/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: "ts-jest/presets/default-esm",
  testEnvironment: "node",
  modulePathIgnorePatterns: ["<rootDir>/dist/", "<rootDir>/node_modules/"],
  // fix '*.js' imports
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
};
