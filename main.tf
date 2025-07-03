# Variables (equivalent to CloudFormation Parameters)
variable "username" {
  description = "Username to use with authenticating to container registry"
  type        = string
  sensitive   = true
}

variable "password" {
  description = "Password or access token to use with authenticating to container registry"
  type        = string
  sensitive   = true
}

variable "registry_url" {
  description = "The container registry containing private images to be pulled"
  type        = string
  default     = "https://index.docker.io/v1/"
}

variable "security_group" {
  description = "List of Security Groups for Application"
  type        = list(string)
  default     = ["sg-01"]
}

variable "subnet_list" {
  description = "Subnet List for Application"
  type        = list(string)
  default     = ["subnet-04", "subnet-06", "subnet-05"]
}

# Launch Template
resource "aws_launch_template" "batch_launch_template" {
  name = "AWSBatch-template"

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    batch_registry_secret = aws_secretsmanager_secret.batch_registry_secret.name
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "AWSBatch-template"
    }
  }
}

# Secrets Manager Secret
resource "aws_secretsmanager_secret" "batch_registry_secret" {
  name        = "batchPrivateRegistries"
  description = "Secret used to store users username and password for Batch private image demo"

  tags = {
    Name                  = "BatchRegistrySecret"
    Application          = "Application"
    AssetProtectionLevel = "AssetProtectionLevel"
    Brand                = "Brand"
    Team                 = "Team"
    CostCenter           = "CostCenter"
  }
}

resource "aws_secretsmanager_secret_version" "batch_registry_secret_version" {
  secret_id = aws_secretsmanager_secret.batch_registry_secret.id
  secret_string = jsonencode({
    username     = var.username
    password     = var.password
    registry_url = var.registry_url
  })
}

# EC2 Key Pair
resource "aws_key_pair" "ec2_key_pair" {
  key_name   = "BatchKey"
  public_key = file("~/.ssh/id_rsa.pub") # You'll need to provide your public key file

  tags = {
    Brand                = "Brand"
    Team                 = "Brand"
    Application          = "Application"
    CostCenter           = "CostCenter"
    AssetProtectionLevel = "AssetProtectionLevel"
  }
}

# IAM Role for Batch Service
resource "aws_iam_role" "batch_service_role" {
  name = "batch-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "batch.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "batch_service_role_policy" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

# IAM Role for Batch Compute
resource "aws_iam_role" "batch_compute_role" {
  name        = "rcpAWSBatchRole"
  description = "Batch Role for AWS Batch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "events.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Application          = "Application"
    AssetProtectionLevel = "AssetProtectionLevel"
    Brand                = "Brand"
    CostCenter           = "CostCenter"
    Name                 = "BatchCompute"
    Team                 = "Team"
  }
}

# IAM Policy for Batch Compute Role
resource "aws_iam_role_policy" "batch_compute_role_policy" {
  name = "rcpAWSBatchRolePolicy"
  role = aws_iam_role.batch_compute_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeTags",
          "ecs:CreateCluster",
          "ecs:DeregisterContainerInstance",
          "ecs:DiscoverPollEndpoint",
          "ecs:Poll",
          "ecs:RegisterContainerInstance",
          "ecs:StartTelemetrySession",
          "ecs:UpdateContainerInstancesState",
          "ecs:Submit*",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "ecs:TagResource"
        Resource = "*"
        Condition = {
          StringEquals = {
            "ecs:CreateAction" = [
              "CreateCluster",
              "RegisterContainerInstance"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = "secretsmanager:GetSecretValue"
        Resource = aws_secretsmanager_secret.batch_registry_secret.arn
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "batch_instance_profile" {
  name = "AWSBatchInstanceProfile"
  role = aws_iam_role.batch_compute_role.name
}

# Batch Compute Environment
resource "aws_batch_compute_environment" "batch_compute" {
  compute_environment_name = "rcpAWSBatchCompute"
  type                    = "MANAGED"
  state                   = "ENABLED"
  service_role           = aws_iam_role.batch_service_role.arn

  compute_resources {
    type                = "SPOT"
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"
    min_vcpus          = 4
    desired_vcpus      = 32
    max_vcpus          = 64
    instance_types     = ["optimal"]
    
    launch_template {
      launch_template_id = aws_launch_template.batch_launch_template.id
    }
    
    ec2_key_pair       = aws_key_pair.ec2_key_pair.key_name
    instance_role      = aws_iam_instance_profile.batch_instance_profile.arn
    subnets            = var.subnet_list
    security_group_ids = var.security_group

    tags = {
      Application          = "Application"
      AssetProtectionLevel = "Application"
      Brand                = "Brand"
      CostCenter           = "CostCenter"
      Name                 = "CostCenter"
      Team                 = "Team"
    }
  }
}

# Batch Job Queue
resource "aws_batch_job_queue" "job_queue" {
  name     = "rcpAWSBatchQueue"
  state    = "ENABLED"
  priority = 1

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.batch_compute.arn
  }

  depends_on = [aws_batch_compute_environment.batch_compute]
}

# Outputs
output "ec2_key_pair_name" {
  description = "Name of the EC2 Key Pair"
  value       = aws_key_pair.ec2_key_pair.key_name
}

output "batch_compute_environment_arn" {
  description = "ARN of the Batch Compute Environment"
  value       = aws_batch_compute_environment.batch_compute.arn
}

output "batch_job_queue_arn" {
  description = "ARN of the Batch Job Queue"
  value       = aws_batch_job_queue.job_queue.arn
}

output "batch_registry_secret_arn" {
  description = "ARN of the Batch Registry Secret"
  value       = aws_secretsmanager_secret.batch_registry_secret.arn
}
