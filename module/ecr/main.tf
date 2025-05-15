resource "aws_ecr_repository" "telcopulse-dashboard" {
  name                 = "telcopulse-dashboard"
  image_tag_mutability = "MUTABLE"
}
