
output "alb_dns_name" {
  description = "DNS name of the application load balancer."
  value       = module.alb.alb_dns_name
}

output "frontend_tg_arn" {
  value = module.frontend.tg_arn
}

output "backend_tg_arn" {
  value = module.backend.tg_arn
}

output "estimated_daily_cost_usd" {
  description = "Estimated daily cost (USD) for this environment."
  value       = var.estimated_daily_cost
}

output "estimated_monthly_cost_usd" {
  description = "Estimated monthly cost (USD) for this environment."
  value       = var.estimated_monthly_cost
}
