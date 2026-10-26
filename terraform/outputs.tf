output "alb_dns_name" {
  description = "DNS name of the ALB fronting the Task API."
  value       = aws_lb.main.dns_name
}

output "api_url" {
  description = "Health endpoint of the deployed API (after apply)."
  value       = "http://${aws_lb.main.dns_name}/health"
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster."
  value       = aws_ecs_cluster.main.name
}
