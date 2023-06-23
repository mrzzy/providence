/*
 * Providence
 * UOB Export
 * SBT Build
 */
import Dependencies._

ThisBuild / scalaVersion := "2.13.10"
ThisBuild / version := "0.1.0-SNAPSHOT"
ThisBuild / organization := "co.mrzzy"
ThisBuild / organizationName := "mrzzy"
ThisBuild / crossScalaVersions := Seq("2.12.17")
ThisBuild / assemblyMergeStrategy := { case _ =>
  MergeStrategy.first
}

lazy val root = (project in file("."))
  .settings(
    name := "uob_export",
    libraryDependencies += spark % "provided",
    libraryDependencies += sparkExcel,
    libraryDependencies += munit % Test
  )
