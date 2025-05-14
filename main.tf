module "s3" {
  source           = "./module/s3"
  lake_bucket_name = var.lake_bucket_name
}

module "kinesis" {
  source = "./module/kinesis"
}

module "cloudwatch" {
  source = "./module/cloudwatch"
}

module "glue" {
  source = "./module/glue"
  # stream_script_location = module.s3.stream_script_location
  lake_bucket_name = var.lake_bucket_name
  stream_arn       = module.kinesis.stream_arn
}


import {
  to = aws_glue_job.MyStreamingJob
  id = "transform-stream-data"
}
