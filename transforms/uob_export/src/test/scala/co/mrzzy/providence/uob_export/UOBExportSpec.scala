/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export

import org.apache.spark.sql.SparkSession

class UOBExportSpec extends munit.FunSuite {
  implicit val spark = SparkSession.builder
    .appName("pvd-uob-export")
    .master("local[*]")
    .getOrCreate()

  test("readTransactions() reads bank transactions from UOB export") {
    val df = UOBExport
      .readTransactions(getClass().getResource("/ACC_TXN_test.xls").getPath())
    // test: dimensions of export dataframe
    assertEquals(df.columns.length, 5)
    assertEquals(df.count(), 2L)
  }
}
