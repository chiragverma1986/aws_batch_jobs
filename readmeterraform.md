# AWS Batch Terraform Configuration

This Terraform configuration creates AWS Batch resources converted from a CloudFormation template. It includes:

- AWS Batch Compute Environment with SPOT instances
- AWS Batch Job Queue
- IAM roles and policies for Batch operations
- EC2 Launch Template with user data for Docker registry authentication
- AWS Secrets Manager secret for container registry credentials
- EC2 Key Pair for SSH access

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version >= 1.0)
3. SSH key pair for EC2 instances

## Usage

1. **Prepare your SSH key:**
   ```bash
   # Generate a new SSH key pair if you don't have one
   ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa
   ```

2. **Configure variables:**
   ```bash
   # Copy the example variables file
   cp terraform.tfvars.example terraform.tfvars
   
   # Edit terraform.tfvars with your values
   # Make sure to update:
   # - username: Your container registry username
   # - password: Your container registry password/token
   # - security_group: Your actual security group IDs
   # - subnet_list: Your actual subnet IDs
   ```

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

4. **Plan the deployment:**
   ```bash
   terraform plan
   ```

5. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Important Notes

- **Security Groups and Subnets**: Make sure to update the `security_group` and `subnet_list` variables with your actual AWS resource IDs
- **SSH Key**: The configuration assumes your SSH public key is located at `~/.ssh/id_rsa.pub`. Update the path in `main.tf` if your key is elsewhere
- **Registry Credentials**: The username and password variables are marked as sensitive and will be stored in AWS Secrets Manager
- **Region**: The configuration defaults to `us-west-2`. Update the `aws_region` variable if needed

## Key Differences from CloudFormation

1. **Variables**: CloudFormation Parameters are converted to Terraform variables
2. **Functions**: CloudFormation intrinsic functions like `Fn::Sub`, `Fn::Join`, etc. are replaced with Terraform equivalents
3. **References**: CloudFormation `Ref` and `GetAtt` are replaced with Terraform resource references
4. **User Data**: Moved to a separate shell script file for better maintainability

## Outputs

- `ec2_key_pair_name`: Name of the created EC2 Key Pair
- `batch_compute_environment_arn`: ARN of the Batch Compute Environment
- `batch_job_queue_arn`: ARN of the Batch Job Queue
- `batch_registry_secret_arn`: ARN of the Secrets Manager secret

## Cleanup

To destroy the resources:
```bash
terraform destroy
```

## Issue with Job Queue

**Note**: There's a discrepancy in the original CloudFormation template. The Job Queue references `"AWSBatchComputeOld"` in the ComputeEnvironmentOrder, but the actual Compute Environment is named `"rcpAWSBatchCompute"`. In the Terraform version, I've corrected this to reference the actual compute environment created by the configuration.
