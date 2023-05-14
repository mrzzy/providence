#
# Providence
# Terraform Deployment on AWS
# Input Variables
#

variable "region" {
  description = "Target AWS Region to deploy to."
  type        = string
}

variable "pipeline_aws_user" {
  description = "Name of the AWS IAM user to create for authenticating pipelines to AWS."
  type        = string
}

variable "s3_dev_bucket" {
  description = "Unique name of the AWS S2 bucket to create as a data lake for development."
  type        = string
}

variable "s3_prod_bucket" {
  description = "Unique name of the AWS S3 bucket to create as a data lake for production."
  type        = string
}

variable "redshift_namespace" {
  description = "Name of Redshift Serverless namespace to create as a data warehouse."
  type        = string
  default     = "main"
}

variable "redshift_workgroup" {
  description = "Name of Redshift Serverless compute to workgroup to proceess queries."
  type        = string
  default     = "main"
}

variable "redshift_prod_db" {
  description = "Name of the Redshift Database where production data will be stored. "
  type        = string
}
