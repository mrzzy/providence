/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.Row
import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.types.StructField
import org.apache.spark.sql.types.StringType
import org.apache.spark.sql.types.DecimalType
import org.apache.spark.sql.types.TimestampType
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.types.DateType
import org.apache.spark.sql.functions

object UOBExport {
  val SparkExcelFormat = "com.crealytics.spark.excel";
  val TimestampCol = "__uob_export_timestamp"

  /** Schema of Bank transactions read from UOB exports */
  val BankTransaction = StructType(
    Seq(
      StructField("TransactionDate", DateType),
      StructField("TransactionDescription", StringType),
      StructField("Withdrawal", DecimalType(13, 2)),
      StructField("Deposit", DecimalType(13, 2)),
      StructField("AvailableBalance", DecimalType(13, 2))
    )
  )

  /** Schema of metadata read from UOB exports */
  val Metadata = StructType(
    Seq(
      StructField("AccountNumber", StringType),
      StructField("AccountType", StringType),
      StructField("StatementPeriod", StringType),
      StructField("Currency", StringType)
    )
  )

  /** Schema of the Bank export output */
  val BankExport = StructType(
    BankTransaction ++ Metadata :+ StructField(
      TimestampCol,
      TimestampType,
      nullable = false
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

  /** Extract the metadata from rows 5-7 of the UOB excel export into a
    * Dataframe.
    *
    * @param path
    *   Path to UOB bank transaction excel export.
    * @param spark
    *   Spark Session used to interface with spark.
    * @return
    *   Extracted metadata as a DataFrame.
    */
  def readMeta(
      path: String
  )(implicit
      spark: SparkSession
  ): DataFrame = {
    import spark.implicits._
    // extract metadata from rows 5-7 of the export
    val metaRows = spark.read
      .format(SparkExcelFormat)
      .option("header", true)
      .option("dataAddress", "A5:C8")
      .load(path)
      .collect()
    val metadata = Row(
      metaRows.map(_.getString(1)) :+
        // currency is oddly placed, so we extract it manually
        metaRows(0).getString(2): _*
    )
    spark.createDataFrame(
      spark.sparkContext.parallelize(Seq(metadata)),
      Metadata
    )
  }

  /** Extract the UOB Excel Export into a Tabular Bank Export DataFrame
    *
    * @param path
    *   Path to UOB bank transaction excel export.
    * @param spark
    *   Spark Session used to interface with spark.
    * @return
    *   Tabular Bank Export DataFrame.
    */
  def read(path: String)(implicit spark: SparkSession): DataFrame = {
    // join metadata to every transaction
    readTransactions(path)
      .crossJoin(readMeta(path))
      // add processing timestamp
      .withColumn(TimestampCol, functions.current_timestamp())
  }

  def write(df: DataFrame, path: String) {
    df.write
      .format("delta")
      .mode(SaveMode.Overwrite)
      .partitionBy("TransactionDate")
      .save(path)
  }

  def configDelta(builder: SparkSession.Builder): SparkSession.Builder = {
    builder
      .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
      .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog"
      )
  }

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
    implicit val spark = configDelta(
      SparkSession.builder
        .appName("pvd-uob-export")
    ).getOrCreate()

    // write extracted bank export into delta table.
    write(read(exportXlsx), outputDelta)
  }
}
