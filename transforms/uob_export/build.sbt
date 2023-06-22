import Dependencies._

ThisBuild / scalaVersion     := "2.13.11"
ThisBuild / version          := "0.1.0-SNAPSHOT"
ThisBuild / organization     := "co.mrzzy"
ThisBuild / organizationName := "mrzzy"

lazy val root = (project in file("."))
  .settings(
    name := "uob_export",
    libraryDependencies += munit % Test,
    libraryDependencies += "org.apache.spark" %% "spark-sql" % "3.4.0",
  )

// See https://www.scala-sbt.org/1.x/docs/Using-Sonatype.html for instructions on how to publish to Sonatype.
