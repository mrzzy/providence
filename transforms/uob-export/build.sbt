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

// spark-excel both bundles the scala library causing conflicts
// use the 'last' merge strategy resolve conflicts using our version of the scala library.
ThisBuild / assemblyMergeStrategy := {
  case PathList("scala", xs @ _*) => MergeStrategy.last
  case x =>
    val oldStrategy = (ThisBuild / assemblyMergeStrategy).value
    oldStrategy(x)
}

lazy val root = (project in file("."))
  .settings(
    name := "uob_export",
    libraryDependencies ++= commonDeps,
    libraryDependencies += hadoopGCP,
    libraryDependencies += hadoopAWS,
    libraryDependencies += awsJavaSDK,
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
