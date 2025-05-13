resource "aws_s3_bucket" "my_bucket" {
  bucket = var.lake_bucket_name
}

resource "aws_s3_object" "glue_job_script" {
  bucket = aws_s3_bucket.my_bucket.bucket
  key    = "scripts/stream_job_script.py"
  source = "${path.module}/scripts/spark-stream-job.py"
  etag   = filemd5("${path.module}/scripts/spark-stream-job.py")
}
