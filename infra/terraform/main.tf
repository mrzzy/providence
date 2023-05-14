#
# Providence
# Terraform Deployment on AWS
#

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.67.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# IAM
# iam policy to allows holder to list, CRUD objects in S3 buckets
data "aws_iam_policy_document" "s3_crud" {
  statement {
    sid       = "ListS3Buckets"
    resources = ["*"]
    actions   = ["s3:ListBucket"]
  }
  statement {
    sid       = "CRUDS3Objects"
    resources = ["*"]
    actions   = ["s3:*Object"]
  }
}
resource "aws_iam_policy" "s3_crud" {
  name_prefix = "AllowCRUDS3Objects"
  policy      = data.aws_iam_policy_document.s3_crud.json
}

# iam user to authenticate Airflow DAGs
resource "aws_iam_user" "airflow" {
  name = var.pipeline_aws_user
}
# allow CRUD on S3 objects
resource "aws_iam_user_policy_attachment" "airflow_s3" {
  user       = aws_iam_user.airflow.name
  policy_arn = aws_iam_policy.s3_crud.arn
}
# allow access to Redshift data warehouse
resource "aws_iam_user_policy_attachment" "airflow_redshift" {
  user       = aws_iam_user.airflow.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRedshiftFullAccess"
}
resource "aws_iam_user_policy_attachment" "airflow_redshiftdata" {
  user       = aws_iam_user.airflow.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRedshiftDataFullAccess"
}

# iam policy to allow AWS Redshift to assume iam role
data "aws_iam_policy_document" "warehouse_assume_role" {
  statement {
    sid     = "AllowRedshiftToAssumeRole"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}
# iam role to identify redshift when accessing other AWS services (eg. S3)
resource "aws_iam_role" "warehouse" {
  name_prefix        = "warehouse"
  assume_role_policy = data.aws_iam_policy_document.warehouse_assume_role.json
}
# allow Redshift CRUD on S3 and Athena access to query S3 objects
resource "aws_iam_role_policy_attachment" "warehouse_s3" {
  for_each = toset([
    aws_iam_policy.s3_crud.arn,
    "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
  ])
  role       = aws_iam_role.warehouse.name
  policy_arn = each.key
}

# VPC
# security group to attach redshift serverless workgroup vms
resource "aws_security_group" "warehouse" {
  name_prefix = "warehouse"
  description = "Security group attached to Redshift Serverless Workgroup warehouse."
}
# allow all egress traffic
resource "aws_vpc_security_group_egress_rule" "warehouse" {
  security_group_id = aws_security_group.warehouse.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = -1 # any
}
# allow redshift traffic over port 5439
resource "aws_vpc_security_group_ingress_rule" "warehouse" {
  security_group_id = aws_security_group.warehouse.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "tcp"
  from_port   = 5439
  to_port     = 5439
}

# S3
# S3 bucket for development
module "s3_dev" {
  source = "./modules/s3"
  bucket = "mrzzy-co-dev"
}
# S3 bucket as a Data Lake
module "s3_lake" {
  source = "./modules/s3"
  bucket = "mrzzy-co-data-lake"
}

# Redshift Serverless Data Warehouse
# namespace to segeregate our db objects within the redshift serverless
resource "aws_redshiftserverless_namespace" "warehouse" {
  namespace_name = var.redshift_namespace
  db_name        = var.redshift_prod_db
  # default iam role must also be listed in iam roles
  default_iam_role_arn = aws_iam_role.warehouse.arn
  iam_roles            = [aws_iam_role.warehouse.arn]
  lifecycle {
    ignore_changes = [
      iam_roles
    ]
  }
}
# workgroup of redshift serverless compute resources
resource "aws_redshiftserverless_workgroup" "warehouse" {
  namespace_name     = aws_redshiftserverless_namespace.warehouse.id
  workgroup_name     = var.redshift_workgroup
  security_group_ids = [aws_security_group.warehouse.id]
  # by default, redshift serverless runs with 128 RPUs, which is overkill.
  # with our small use case the minimum of 8 RPUs should do.
  base_capacity = 8
  # public access needed for querying from GCP over the internet
  publicly_accessible = true
}
