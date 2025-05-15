resource "aws_glue_catalog_database" "my_catalog_database" {
  name = "project-9"
}

resource "aws_iam_role" "glue_service_role" {
  name = "glue_service_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "glue_policy" {
  name = "glue-permissions"
  role = aws_iam_role.glue_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:*",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kinesis:*",
        ]
        Resource = "arn:aws:kinesis:*:*:stream/*"
      }
    ]
  })
}



# crawler
resource "aws_glue_crawler" "processed_crawler" {
  name          = "crawl_processed"
  role          = aws_iam_role.glue_service_role.arn
  database_name = aws_glue_catalog_database.my_catalog_database.name
  s3_target {
    path = "s3://${var.lake_bucket_name}/processed/"
  }
}

resource "aws_glue_job" "MyStreamingJob" {
  connections = []
  default_arguments = {
    "--TempDir"                      = "s3://aws-glue-assets-${var.account_id}-eu-west-1/temporary/"
    "--enable-glue-datacatalog"      = "true"
    "--enable-job-insights"          = "true"
    "--enable-metrics"               = "true"
    "--enable-observability-metrics" = "false"
    "--enable-spark-ui"              = "true"
    "--extra-py-files"               = "s3://aws-glue-studio-transforms-244479516193-prod-eu-west-1/gs_common.py,s3://aws-glue-studio-transforms-244479516193-prod-eu-west-1/gs_null_rows.py"
    "--job-bookmark-option"          = "job-bookmark-disable"
    "--job-language"                 = "python"
    "--spark-event-logs-path"        = "s3://aws-glue-assets-${var.account_id}-eu-west-1/sparkHistoryLogs/"
  }
  description               = null
  execution_class           = "STANDARD"
  glue_version              = "5.0"
  job_run_queuing_enabled   = false
  maintenance_window        = null
  number_of_workers         = 10
  worker_type               = "G.1X"
  max_retries               = 0
  name                      = "transform-stream-data"
  non_overridable_arguments = {}
  role_arn                  = "arn:aws:iam::${var.account_id}:role/glue_service_role"
  security_configuration    = null
  tags                      = {}
  tags_all                  = {}
  # timeout                   = 1
  command {
    name            = "gluestreaming"
    python_version  = "3"
    runtime         = null
    script_location = "s3://aws-glue-assets-${var.account_id}-eu-west-1/scripts/transform-stream-data.py"
  }
  execution_property {
    max_concurrent_runs = 1
  }
}
