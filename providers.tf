provider "aws" {
  region = var.region
  default_tags {
    tags = {
      "project" = "project-9"
    }
  }
}
