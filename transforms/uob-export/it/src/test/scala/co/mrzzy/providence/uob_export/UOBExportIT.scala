/*
 * Providence
 * UOB Export
 * Integration Tests
 */

package co.mrzzy.providence.uob_export

import com.dimafeng.testcontainers.ContainerDef
import com.dimafeng.testcontainers.GenericContainer
import org.testcontainers.containers.wait.strategy.Wait
import org.apache.spark.sql.SparkSession
import com.dimafeng.testcontainers.munit.TestContainerForEach
import com.dimafeng.testcontainers.DockerComposeContainer
import java.io.File
import com.dimafeng.testcontainers.ExposedService

class UOBExportIT extends munit.FunSuite with TestContainerForEach {
  val S3APIPort = 9000

  // minio container to emulate cloud storage in test
  override val containerDef = DockerComposeContainer.Def(
    new File(getClass().getResource("/docker-compose.yml").toURI()),
    exposedServices = Seq(
      ExposedService("minio", S3APIPort, Wait.forListeningPort())
    )
  )

  test("UOBExport.run() exports Excel export to Minio storage") {
    withContainers { compose =>
      // construct test spark context
      val spark = SparkSession.builder
        .master("local[*]")
        .config(UOBExport.SparkConfig)
        .config(
          Map(
            "spark.hadoop.fs.s3a.access.key" -> "minioadmin",
            "spark.hadoop.fs.s3a.secret.key" -> "minioadmin",
            "spark.hadoop.fs.s3a.endpoint" -> s"http://localhost:${compose
                .getServicePort("minio", S3APIPort)}",
            "spark.hadoop.fs.s3a.path.style.access" -> "true",
            "spark.hadoop.fs.s3a.connection.ssl.enabled" -> "false"
          )
        )
        .getOrCreate

      // run uob export on test xlsx file
      val exportPath = "s3a://test/transactions"
      UOBExport.run(
        spark,
        Array(
          getClass.getResource("/ACC_TXN_test.xls").getPath,
          exportPath
        )
      )

      // test: check that we can read the exported excel file
      assertEquals(
        spark.read
          .parquet(exportPath)
          .rdd
          .count,
        2L
      )
    }
  }

}
