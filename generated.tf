# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform
resource "aws_glue_job" "MyStreamingJob" {
  connections = []
  default_arguments = {
    "--TempDir"                      = "s3://aws-glue-assets-448049788660-eu-west-1/temporary/"
    "--enable-glue-datacatalog"      = "true"
    "--enable-job-insights"          = "true"
    "--enable-metrics"               = "true"
    "--enable-observability-metrics" = "false"
    "--enable-spark-ui"              = "true"
    "--extra-py-files"               = "s3://aws-glue-studio-transforms-244479516193-prod-eu-west-1/gs_common.py,s3://aws-glue-studio-transforms-244479516193-prod-eu-west-1/gs_null_rows.py"
    "--job-bookmark-option"          = "job-bookmark-disable"
    "--job-language"                 = "python"
    "--spark-event-logs-path"        = "s3://aws-glue-assets-448049788660-eu-west-1/sparkHistoryLogs/"
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
  role_arn                  = "arn:aws:iam::448049788660:role/glue_service_role"
  security_configuration    = null
  tags                      = {}
  tags_all                  = {}
  # timeout                   = 1
  command {
    name            = "gluestreaming"
    python_version  = "3"
    runtime         = null
    script_location = "s3://aws-glue-assets-448049788660-eu-west-1/scripts/transform-stream-data.py"
  }
  execution_property {
    max_concurrent_runs = 1
  }
}
