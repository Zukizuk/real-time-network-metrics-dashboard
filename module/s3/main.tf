resource "aws_s3_bucket" "my_bucket" {
  bucket = var.lake_bucket_name
}

resource "aws_s3_bucket" "glue_bucket" {
  bucket              = "aws-glue-assets-${var.account_id}-eu-west-1"
  bucket_prefix       = null
  force_destroy       = null
  object_lock_enabled = false
  tags                = {}
  tags_all            = {}
}
