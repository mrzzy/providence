/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.types.StructField
import org.apache.spark.sql.types.StringType
import org.apache.spark.sql.types.DecimalType

object UOBExport {
  val SparkExcelFormat = "com.crealytics.spark.excel";

  /** Schema of Bank transactions read from UOB exports */
  val BankTransaction = StructType(
    Seq(
      StructField("Transaction Date", StringType),
      StructField("Transaction Description", StringType),
      StructField("Withdrawal", DecimalType(13, 2)),
      StructField("Deposit", DecimalType(13, 2)),
      StructField("Available Balance", DecimalType(13, 2))
    )
  )

  /** Extract the bank transactions in the given UOB excel export into a
    * DataFrame.
    *
    * @param path
    *   Path to UOB bank transaction excel export.
    * @param spark
    *   Spark Session used to interface with spark.
    * @return
    *   DataFrame of read bank transactions.
    */
  def readTransactions(
      path: String
  )(implicit
      spark: SparkSession
  ): DataFrame = {
    spark.read
      .format(SparkExcelFormat)
      .option("header", true)
      .option("dataAddress", "A8")
      .schema(BankTransaction)
      .load(path)
  }

  def readMeta = ???

  def main(args: Array[String]): Unit = {
    // parse command args
    val usage = """Usage: uob_export <export_xlsx> <output_delta>

Extract UOB Bank transactions into a from the UOB Excel transactions export
at path 'export_xlsx' and write them into a Delta Lake table at path 'output_delta'.
    """
    if (args.length != 2) {
      println("Expected to be given 2 arguments")
      print(usage)
      sys.exit(1)
    }
    val (exportXlsx, outputDelta) = (args(0), args(1))
    implicit val spark =
      SparkSession.builder.appName("pvd-uob-export").getOrCreate()
  }
}
