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
    path = "${var.lake_bucket_name}/processed/"
  }
}
