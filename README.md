# TelcoPulse: Real-Time Network Metrics Dashboard

This project implements a Streamlit dashboard for visualizing real-time network metrics for the TelcoPulse telecommunications analytics project. The dashboard connects to AWS Athena to query data from two tables: `average_by_operator` and `status_by_postal_code`, and displays key performance indicators (KPIs) for network monitoring.

## Architecture Overview

![Architecture Diagram](assets/images/Architecture.png)

## Features

- **Real-time metrics visualization** for mobile network operators
  - Average Signal Strength by Operator
  - Average GPS Precision by Operator
  - Network Status Distribution by Postal Code
- **Time-based filtering** from 1 hour to 7 days
- **Automatic refresh** at configurable intervals
- **Responsive design** with interactive charts and tables
- **AWS-native** integration with Athena for data querying

## Project Structure

```
project-9/
├── app/                     # Application code
│   ├── dashboard.py         # Streamlit dashboard implementation
├── assets/                  # Static assets
│   └── images/              # Architecture and dashboard images
├── data/                    # Sample data files
├── docs/                    # Documentation
├── module/                  # Terraform modules for AWS resources
│   ├── ecs/                 # ECS module
│   ├── s3/                  # S3 module
│   ├── glue/                # Glue module
│   ├── kinesis/             # Kinesis module
│   └── vpc/                 # VPC module
├── notebooks/               # Jupyter notebooks for data exploration
├── problem/                 # Problem statement and related files
├── scripts/                 # Utility scripts
├── Dockerfile               # Docker configuration
├── terraform.tf             # Terraform configuration
└── README.md                # Project documentation
```

## Core Technologies

- **Streamlit**: Interactive web application framework for the dashboard
- **AWS ECS**: Hosting the dashboard as a containerized application
- **AWS Athena**: Querying data from the S3 data lake
- **AWS Glue**: ETL jobs for processing streaming data
- **AWS Kinesis**: Real-time data streaming
- **Terraform**: Infrastructure as Code (IaC) for AWS resource provisioning
- **Docker**: Containerization for local development and deployment

## Deployment Instructions

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with access keys
- Docker and Docker Compose installed
- S3 bucket for Athena query results

## Terraform Setup

This project uses Terraform to provision AWS resources. Follow these steps to set up the infrastructure:

1. **Initialize Terraform:**

   ```bash
   terraform init
   ```

2. **Validate the Configuration:**

   ```bash
   terraform validate
   ```

3. **Plan the Deployment:**

   ```bash
   terraform plan
   ```

4. **Apply the Configuration:**

   ```bash
   terraform apply
   ```

   Confirm the changes when prompted. This will create the necessary AWS resources.

5. **Destroy the Infrastructure (if needed):**

   ```bash
   terraform destroy
   ```

   This will remove all resources created by Terraform.

---

### Local Development

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/telcopulse-dashboard.git
   cd telcopulse-dashboard
   ```

2. Set up environment variables:

   ```bash
   export AWS_REGION=us-east-1
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

3. Run with Docker Compose:

   ```bash
   docker-compose up --build
   ```

4. Access the dashboard at http://localhost:8501

### AWS ECS Deployment

1. Build and push the Docker image to Amazon ECR:

   ```bash
   aws ecr create-repository --repository-name telcopulse-dashboard
   aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
   docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/telcopulse-dashboard:latest .
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/telcopulse-dashboard:latest
   ```

2. Create an ECS cluster and task definition:

   ```bash
   aws ecs create-cluster --cluster-name telcopulse-cluster
   ```

3. Create a task definition JSON file named `task-definition.json`:

   ```json
   {
     "family": "telcopulse-dashboard",
     "networkMode": "awsvpc",
     "executionRoleArn": "arn:aws:iam::your-account-id:role/ecsTaskExecutionRole",
     "taskRoleArn": "arn:aws:iam::your-account-id:role/ecsTaskRole",
     "containerDefinitions": [
       {
         "name": "telcopulse-dashboard",
         "image": "your-account-id.dkr.ecr.your-region.amazonaws.com/telcopulse-dashboard:latest",
         "essential": true,
         "portMappings": [
           {
             "containerPort": 8501,
             "hostPort": 8501,
             "protocol": "tcp"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/telcopulse-dashboard",
             "awslogs-region": "your-region",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ],
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048"
   }
   ```

4. Register the task definition:

   ```bash
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   ```

5. Create a service:

   ```bash
   aws ecs create-service \
     --cluster telcopulse-cluster \
     --service-name telcopulse-dashboard \
     --task-definition telcopulse-dashboard:1 \
     --desired-count 1 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678],assignPublicIp=ENABLED}"
   ```

6. Access the dashboard through the public IP assigned to the Fargate task or through an Application Load Balancer.

## Configuration

The dashboard can be configured through the sidebar:

- **AWS Region**: The AWS region where your Athena database is located
- **Athena Database**: The name of your Athena database
- **Athena Output Location**: S3 bucket for Athena query results
- **Time Window**: Filter data by time window (1 hour to 7 days)
- **Auto-refresh Interval**: Set how often the dashboard refreshes data

## Required IAM Permissions

The AWS role used for this dashboard requires the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::your-athena-results-bucket",
        "arn:aws:s3:::your-athena-results-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetDatabase",
        "glue:GetDatabases"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

- **Connection Issues**: Ensure your AWS credentials have the appropriate permissions
- **Missing Data**: Verify that your Athena tables are populated and the partitions are correctly formatted
- **Performance Issues**: Consider optimizing your Athena queries or increasing the refresh interval

📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

👥 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

📧 **Contact**

For any questions or concerns, please open an issue in the repository.
