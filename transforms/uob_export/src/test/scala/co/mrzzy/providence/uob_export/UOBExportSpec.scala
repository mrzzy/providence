/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export

import scala.reflect.io.Directory
import org.apache.spark.sql.SparkSession
import java.nio.file.Files
import org.apache.spark.sql.Row
import scala.collection.immutable.ArraySeq
import java.sql.Date

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
    // test: read dataframe schema
    assertEquals(df.schema, UOBExport.BankTransaction)
    // test: read dataframe contents
    assertEquals(
      df.collect().toSeq,
      ArraySeq(
        Row(
          Date.valueOf("2023-04-06"),
          "Placeholder Description",
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("2000.00")
        ),
        Row(
          Date.valueOf("2023-04-07"),
          "Placeholder Description",
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("2000.00")
        )
      )
    )
  }

  test("readMetadata() reads metadata from UOB export") {
    // test: read dataframe schema
    val df = UOBExport
      .readMeta(getClass().getResource("/ACC_TXN_test.xls").getPath())
    assertEquals(df.schema, UOBExport.Metadata)
    // test: read dataframe contents
    assertEquals(
      df.collect().toSeq,
      ArraySeq(
        Row("123456789", "Test Account", "06 Feb 2023 To 07 Apr 2023", "SGD")
      )
    )
  }

  lazy val df = UOBExport
    .read(getClass().getResource("/ACC_TXN_test.xls").getPath())

  test("read() joins transactions & metadata, adds timestamp column") {
    // test: read dataframe schema
    assertEquals(df.schema, UOBExport.BankExport)
    assert(df.columns.contains(UOBExport.TimestampCol))

    // test: read dataframe contents
    assertEquals(
      df.drop(UOBExport.TimestampCol).collect.toSeq,
      ArraySeq(
        Row(
          Date.valueOf("2023-04-06"),
          "Placeholder Description",
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("2000.00"),
          "123456789",
          "Test Account",
          "06 Feb 2023 To 07 Apr 2023",
          "SGD"
        ),
        Row(
          Date.valueOf("2023-04-07"),
          "Placeholder Description",
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("5.00"),
          new java.math.BigDecimal("2000.00"),
          "123456789",
          "Test Account",
          "06 Feb 2023 To 07 Apr 2023",
          "SGD"
        )
      )
    )
  }

  test("write() writes dataframe parquet files") {
    val targetPath = Files.createTempDirectory("UOBExportSpec_write")
    UOBExport.write(targetPath.toString)(df)
    // test that spark can read parquet files written previously
    spark.read.format("parquet").load(targetPath.toUri.toString)
    new Directory(targetPath.toFile).deleteRecursively
  }
}
