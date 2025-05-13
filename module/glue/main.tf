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
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetJob",
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:BatchGetJobs",
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions"
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
          "kinesis:DescribeStream",
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:ListStreams",
          "kinesis:DescribeStreamSummary"
        ]
        Resource = "arn:aws:kinesis:*:*:stream/*"
      }
    ]
  })
}


resource "aws_glue_job" "streaming-job" {
  name     = "transform-streams-job"
  role_arn = aws_iam_role.glue_service_role.arn
  command {
    name            = "gluestreaming"
    script_location = "s3://${var.lake_bucket_name}/${var.stream_script_location}"
  }

  default_arguments = {
    "--window_size"                      = "60"
    "--output_path"                      = "s3://${var.lake_bucket_name}/data/"
    "--kinesis_stream_arn"               = var.stream_arn
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-metrics"                   = "true"
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://${var.lake_bucket_name}/glue/tmp"
  }

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 5
}
