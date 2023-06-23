/*
 * Providence
 * Transforms
 * UOB Export
 */

package co.mrzzy.providence.uob_export
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.DataFrame

object UOBExport {

  /** Read the excel at the given path a dataframe.
    *
    * @param spark
    * @param path
    * @return
    */
  def readExcel(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .format("com.crealytics.spark.excel")
      .option("header", false)
      .load(path)
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
    val (export_xlsx, output_delta) = (args(0), args(1))

    val spark = SparkSession.builder.appName("pvd-uob-export").getOrCreate()
  }
}
