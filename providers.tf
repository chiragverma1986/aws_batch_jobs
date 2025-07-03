# providers.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Additional variable for AWS region
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}
