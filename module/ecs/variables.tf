variable "account_id" {
  type        = string
  description = "The AWS account ID."
}

variable "subnets" {
  type        = set(string)
  description = "The subnets to use for the ECS service."
}

variable "security_group" {
  type        = string
  description = "The security groups to use for the ECS service."
}
