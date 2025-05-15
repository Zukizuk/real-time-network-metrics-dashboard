variable "region" {
  type        = string
  description = "The AWS region to deploy resources in."
}

variable "lake_bucket_name" {
  type = string
}

variable "account_id" {
  type        = string
  description = "The AWS account ID."
}
