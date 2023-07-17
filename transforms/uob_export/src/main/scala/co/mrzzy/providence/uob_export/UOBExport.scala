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
import org.apache.spark.sql.functions._

object UOBExport {
  val SparkExcelFormat = "com.crealytics.spark.excel";
  val SparkConfig: Map[String, String] = Map(
  )

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
    // cast column to bank transaction schema
    val castSchema =
      (column: String, field: String) =>
        col(column).cast(BankTransaction(field).dataType).as(field)
    spark.read
      .format(SparkExcelFormat)
      .option("header", true)
      .option("dataAddress", "A8")
      .load(path)
      .select(
        castSchema("Transaction Date", "TransactionDate"),
        castSchema("Transaction Description", "TransactionDescription"),
        castSchema("Withdrawal", "Withdrawal"),
        castSchema("Deposit", "Deposit"),
        castSchema("Available Balance", "AvailableBalance")
      )
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
      .withColumn(TimestampCol, current_timestamp())
  }

  /** Write extracted bank export into Parquet files
    *
    * @param path
    *   Path / location to write the Parquet files to.
    * @param df
    *   Dataframe to write as Parquet files.
    */
  def write(path: String)(df: DataFrame) {
    df.write
      .format("parquet")
      .mode(SaveMode.Overwrite)
      .save(path)
  }

  /** Run the UOB Export Pipeline with the given SparkSession.
    *
    * @param spark
    *   Spark Session used to interface with spark.
    * @param args
    *   Command line argv passed to main.
    */
  def run(implicit spark: SparkSession, args: Array[String]): Unit = {
    // parse command args
    val usage = """Usage: uob_export <export_xlsx> <output_path>

Extract UOB Bank transactions into a from the UOB Excel transactions export
at path 'export_xlsx' and write them into a Parquet file at path 'output_path'.
    """
    if (args.length != 2) {
      println("Expected to be given 2 arguments")
      print(usage)
      sys.exit(1)
    }
    val (exportXlsx, outputPath) = (args(0), args(1))
    // run uob export pipeline
    val df = read(exportXlsx)
    write(outputPath)(df)
  }

  def main(args: Array[String]): Unit = {
    // run Pipeline
    val spark = SparkSession.builder
      .appName("pvd-uob-export")
      .config(SparkConfig)
      .getOrCreate
    run(spark, args)
  }
}
