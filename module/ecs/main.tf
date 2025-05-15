resource "aws_iam_role" "ecsTaskRole" {
  name = "ecsTaskRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}


resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "ecs-task-policy"
  role = "ecsTaskRole"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "arn:aws:s3:::*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetDatabase",
          "glue:GetDatabases"
        ]
        Resource = "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : "arn:aws:logs:eu-west-1:*"
      }
    ]
  })

  depends_on = [aws_iam_role.ecsTaskRole]
}

resource "aws_ecs_cluster" "telcopulse-cluster" {
  name = "telcopulse-cluster"
}

resource "aws_ecs_task_definition" "telcopulse-task" {
  family = "telcopulse-dashboard"
  container_definitions = jsonencode([
    {
      "name" : "telcopulse-dashboard",
      "image" : "${var.account_id}.dkr.ecr.eu-west-1.amazonaws.com/telcopulse-dashboard:latest",
      "essential" : true,
      "portMappings" : [
        {
          "containerPort" : 8501,
          "hostPort" : 8501,
          "protocol" : "tcp"
        }
      ],
      "logConfiguration" : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-group" : "/ecs/telcopulse-dashboard",
          "awslogs-region" : "eu-west-1",
          "awslogs-stream-prefix" : "ecs"
        }
      }
    }
  ])
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = "arn:aws:iam::${var.account_id}:role/ecsTaskExecutionRole"
  task_role_arn            = "arn:aws:iam::${var.account_id}:role/ecsTaskRole"
  memory                   = "2048"
  cpu                      = "1024"
}

resource "aws_ecs_service" "telcopulse-service" {
  name            = "telcopulse-service"
  cluster         = aws_ecs_cluster.telcopulse-cluster.id
  task_definition = aws_ecs_task_definition.telcopulse-task.arn
  desired_count   = 1

  launch_type = "FARGATE"

  network_configuration {
    subnets          = var.subnets
    security_groups  = [var.security_group]
    assign_public_ip = true
  }

  depends_on = [aws_ecs_task_definition.telcopulse-task]
  lifecycle {
    ignore_changes = [
      desired_count,
    ]
  }

}

resource "aws_cloudwatch_log_group" "telcopulse-log-group" {
  name              = "/ecs/telcopulse-dashboard"
  retention_in_days = 1
}
