/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export

import scala.reflect.io.Directory
import org.apache.spark.sql.SparkSession
import java.nio.file.Files

class UOBExportSpec extends munit.FunSuite {
  implicit val spark =
    SparkSession.builder
      .appName("pvd-uob-export")
      .config(UOBExport.SparkConfig)
      .master("local[*]")
      .getOrCreate()

  test("readTransactions() reads bank transactions from UOB export") {
    val df = UOBExport
      .readTransactions(getClass().getResource("/ACC_TXN_test.xls").getPath())
    // test: dimensions of export dataframe
    assertEquals(df.schema, UOBExport.BankTransaction)
    // use rdd count force spark to evaluate dataframe and get an accurate count
    assertEquals(df.rdd.count(), 2L)
  }

  test("readMetadata() reads metadata from UOB export") {
    val df = UOBExport
      .readMeta(getClass().getResource("/ACC_TXN_test.xls").getPath())
    assertEquals(df.schema, UOBExport.Metadata)
    // use rdd count force spark to evaluate dataframe and get an accurate count
    assertEquals(df.rdd.count(), 1L)
  }

  lazy val df = UOBExport
    .read(getClass().getResource("/ACC_TXN_test.xls").getPath())

  test("read() joins transactions & metadata, adds timestamp column") {
    assertEquals(df.schema, UOBExport.BankExport)
    // use rdd count force spark to evaluate dataframe and get an accurate count
    assertEquals(df.rdd.count(), 2L)

    assert(df.columns.contains(UOBExport.TimestampCol))
  }

  test("write() writes dataframe parquet files") {
    val targetPath = Files.createTempDirectory("UOBExportSpec_write")
    UOBExport.write(targetPath.toString)(df)
    // test that spark can read parquet files written previously
    spark.read.format("parquet").load(targetPath.toUri.toString)
    new Directory(targetPath.toFile).deleteRecursively
  }
}
