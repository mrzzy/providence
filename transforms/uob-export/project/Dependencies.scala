import sbt._

object Dependencies {
  lazy val munit = "org.scalameta" %% "munit" % "1.0.0-M8"
  lazy val spark = "org.apache.spark" %% "spark-sql" % "3.4.0"

  // spark-excel both bundles dependencies in fat jar & declares them in pom.xml
  // causing conflicts in files when we bundle classes in dependencies
  // https://github.com/crealytics/spark-excel/issues/654
  // exclude conflicting dependencies from from sbt-assembly bundling.
  lazy val sparkExcel = ("com.crealytics" %% "spark-excel" % "3.3.1_0.18.7")
    .exclude("org.apache.poi", "poi")
    .exclude("org.apache.poi", "poi-ooxml")
    .exclude("org.apache.poi", "poi-ooxml-lite")
    .exclude("org.apache.xmlbeans", "xmlbeans")
    .exclude("com.norbitltd", "spoiwo_2.13")
    .exclude("com.github.pjfanning", "excel-streaming-reader")
    .exclude("com.github.pjfanning", "poi-shared-strings")
    .exclude("commons-io", "commons-io")
    .exclude("org.apache.commons", "commons-compress")
    .exclude("org.apache.logging.log4j", "log4j-api")
    .exclude("com.zaxxer", "SparseBitSet")
    .exclude("org.apache.commons", "commons-collections4")
    .exclude("com.github.virtuald", "curvesapi")
    .exclude("commons-codec", "commons-codec")
    .exclude("org.apache.commons", "commons-math3")
    .exclude("org.scala-lang.modules", "scala-collection-compat_2.13")
    .exclude("org.apache.logging.log4j", "log4j-core")
    .exclude("org.scala-lang", "scala-library")
    .exclude("org.apache.spark", "spark-core_2.13")
    .exclude("org.apache.spark", "spark-sql_2.13")
    .exclude("org.apache.spark", "spark-hive_2.13")

  val commonDeps = Seq(
    spark % "provided",
    sparkExcel,
    munit % Test
  )

  lazy val testContainers =
    "com.dimafeng" %% "testcontainers-scala-munit" % "0.40.17"
  // cloud storage connectors & sdks
  lazy val hadoopAWS = "org.apache.hadoop" % "hadoop-aws" % "3.3.4"
  lazy val awsJavaSDK = "com.amazonaws" % "aws-java-sdk-bundle" % "1.12.505"

  lazy val hadoopGCP =
    "com.google.cloud.bigdataoss" % "gcs-connector" % "hadoop3-2.2.16"
}
