variable "aws_region" {
  description = "AWS region for the ECS deployment."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for all resources."
  type        = string
  default     = "ecs-fargate-task-api"
}

variable "image" {
  description = "Container image for the task API (set to your Docker Hub/ECR image)."
  type        = string
  default     = "giriboinar/ecs-fargate-task-api:latest"
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Number of Fargate tasks to run."
  type        = number
  default     = 1
}
