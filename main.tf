module "s3" {
  source           = "./module/s3"
  lake_bucket_name = var.lake_bucket_name
}

module "vpc" {
  source = "./module/vpc"
}

module "kinesis" {
  source = "./module/kinesis"
}

module "cloudwatch" {
  source = "./module/cloudwatch"
}

module "glue" {
  source           = "./module/glue"
  lake_bucket_name = var.lake_bucket_name
  stream_arn       = module.kinesis.stream_arn
}

module "ecr" {
  source = "./module/ecr"
}

module "ecs" {
  source         = "./module/ecs"
  account_id     = var.account_id
  subnets        = module.vpc.subnet_ids
  security_group = module.vpc.security_group_id
}

import {
  to = aws_glue_job.MyStreamingJob
  id = "transform-stream-data"
}
