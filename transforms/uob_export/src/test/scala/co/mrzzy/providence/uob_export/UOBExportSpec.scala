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
    assertEquals(df.count(), 2L)
  }

  test("readMetadata() reads metadata from UOB export") {
    val df = UOBExport
      .readMeta(getClass().getResource("/ACC_TXN_test.xls").getPath())
    assertEquals(df.schema, UOBExport.Metadata)
    assertEquals(df.count(), 1L)
  }

  lazy val df = UOBExport
    .read(getClass().getResource("/ACC_TXN_test.xls").getPath())

  test("read() joins transactions & metadata, adds timestamp column") {
    assertEquals(df.schema, UOBExport.BankExport)
    assertEquals(df.count(), 2L)

    assert(df.columns.contains(UOBExport.TimestampCol))
  }

  test("write() writes dataframe delta paritioned by date") {
    val targetPath = Files.createTempDirectory("UOBExportSpec_write")
    UOBExport.write(targetPath.toString)(df)
    // test that spark can read delta table written by scalaa
    spark.read.format("delta").load(targetPath.toUri.toString)
    new Directory(targetPath.toFile).deleteRecursively
  }
}
