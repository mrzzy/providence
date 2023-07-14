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
    libraryDependencies ++= commonDeps,
  )

lazy val it = (project in file("it"))
  .dependsOn(root)
  .settings(
    // do not publish integration test project
    publish / skip := true,
    libraryDependencies ++= commonDeps,
    libraryDependencies += testContainers % Test,
    libraryDependencies += hadoopAWS % Test,
    libraryDependencies += awsJavaSDK % Test,
  )
