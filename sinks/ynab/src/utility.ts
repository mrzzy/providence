/*
 * Providence
 * Utility Functions
 */

/**
 * Check that all the given envVars are set.
 * @param envVars List of environment variables to check.
 * @returns true if all envVars are set, false otherwise
 */
export function checkEnv(envVars: string[]): boolean {
  return envVars
    .map((envVar) => envVar in process.env)
    .reduce((hasAll, hasThis) => hasAll && hasThis);
}
