/*
 * Providence
 * UOB Export
 * SBT Build
 */
import Dependencies._

ThisBuild / scalaVersion := "2.12.18"
ThisBuild / version := "0.1.0-SNAPSHOT"
ThisBuild / organization := "co.mrzzy"
ThisBuild / organizationName := "mrzzy"

// use merge strategy resolve conflicts with different versions of wfileslasses
ThisBuild / assemblyMergeStrategy := {
  case PathList("scala", _*)                    => MergeStrategy.last
  case PathList("org", "apache", "commons", _*) => MergeStrategy.last
  case "mozilla/public-suffix-list.txt"         => MergeStrategy.last
  case "library.properties"                     => MergeStrategy.last
  case "META-INF/versions/9/module-info.class"  => MergeStrategy.discard
  case "META-INF/io.netty.versions.properties"  => MergeStrategy.discard
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
    libraryDependencies += awsJavaSDK
  )

lazy val it = (project in file("it"))
  .dependsOn(root)
  .settings(
    // do not publish integration test project
    publish / skip := true,
    libraryDependencies ++= commonDeps,
    libraryDependencies += testContainers % Test,
    libraryDependencies += hadoopAWS % Test,
    libraryDependencies += awsJavaSDK % Test
  )
