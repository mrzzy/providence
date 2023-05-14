#
# Nimbus
# AWS S3 Module
# Output Variables
#

output "arn" {
  description = "ARN of the deployed AWS S3 bucket."
  value       = aws_s3_bucket.bucket.arn
}
