/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export

import org.apache.spark.sql.SparkSession

class UOBExportSpec extends munit.FunSuite {
  test("readExcel() reads test UOB export") {
    val spark = SparkSession.builder
      .appName("pvd-uob-export")
      .master("local[*]")
      .getOrCreate()

    UOBExport
      .readExcel(
        spark,
        getClass().getResource("/ACC_TXN_test.xls").getPath()
      )
      .count
  }
}
