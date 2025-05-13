resource "aws_kinesis_stream" "my-stream" {
  name                = "metric-stream"
  shard_count         = 1
  retention_period    = 24
  shard_level_metrics = ["IncomingBytes", "OutgoingBytes"]
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

output "stream_arn" {
  value = aws_kinesis_stream.my-stream.arn
}
