#!/bin/bash
# User data script for AWS Batch instances

# MIME-Version: 1.0
# Content-Type: multipart/mixed; boundary="==MYBOUNDARY=="

# --==MYBOUNDARY==
# Content-Type: text/cloud-config; charset="us-ascii"

# Install required packages
yum update -y
yum install -y jq aws-cli docker

# Start Docker service
systemctl start docker
systemctl enable docker

# Configure Docker authentication for private registry
export SECRET_STRING=$(/usr/bin/aws secretsmanager get-secret-value --secret-id ${batch_registry_secret} --region us-west-2 | jq -r '.SecretString')
export USERNAME=$(echo $SECRET_STRING | jq -r '.username')
export PASSWORD=$(echo $SECRET_STRING | jq -r '.password')
export REGISTRY_URL=$(echo $SECRET_STRING | jq -r '.registry_url')

# Login to Docker registry
echo $PASSWORD | docker login --username $USERNAME --password-stdin $REGISTRY_URL

# Configure ECS authentication
export AUTH=$(cat ~/.docker/config.json | jq -c .auths)
echo 'ECS_ENGINE_AUTH_TYPE=dockercfg' >> /etc/ecs/ecs.config
echo "ECS_ENGINE_AUTH_DATA=$AUTH" >> /etc/ecs/ecs.config

# --==MYBOUNDARY==--
