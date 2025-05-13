variable "stream_script_location" {
  description = "The location of the Glue job script in S3"
  type        = string
}

variable "lake_bucket_name" {
  type = string
}

variable "stream_arn" {
  description = "The ARN of the Kinesis stream"
  type        = string
}

