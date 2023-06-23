import Dependencies._

ThisBuild / scalaVersion     := "2.13.10"
ThisBuild / version          := "0.1.0-SNAPSHOT"
ThisBuild / organization     := "co.mrzzy"
ThisBuild / organizationName := "mrzzy"
ThisBuild / crossScalaVersions := Seq("2.12.17")

lazy val root = (project in file("."))
  .settings(
    name := "uob_export",
    libraryDependencies += spark,
    libraryDependencies += sparkExcel,
    libraryDependencies += munit % Test,
  )

// See https://www.scala-sbt.org/1.x/docs/Using-Sonatype.html for instructions on how to publish to Sonatype.
