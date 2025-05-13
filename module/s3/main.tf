resource "aws_s3_bucket" "my_bucket" {
  bucket = var.lake_bucket_name
}
