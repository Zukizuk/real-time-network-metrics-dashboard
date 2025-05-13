module "s3" {
  source           = "./module/s3"
  lake_bucket_name = var.lake_bucket_name
}

module "kinesis" {
  source = "./module/kinesis"
}
