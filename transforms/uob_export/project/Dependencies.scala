import sbt._

object Dependencies {
  lazy val munit = "org.scalameta" %% "munit" % "1.0.0-M8"
  lazy val spark = "org.apache.spark" %% "spark-sql" % "3.4.0"
  lazy val sparkExcel = "com.crealytics" %% "spark-excel" % "3.3.1_0.18.7"
  val commonDeps = Seq(
    spark % "provided",
    sparkExcel,
    munit % Test
  )

  lazy val testContainers =
    "com.dimafeng" %% "testcontainers-scala-munit" % "0.40.17"
  lazy val hadoopAWS = "org.apache.hadoop" % "hadoop-aws" % "3.3.4"
  lazy val awsJavaSDK = "com.amazonaws" % "aws-java-sdk-bundle" % "1.12.505"
}
