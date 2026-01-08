
resource "aws_budgets_budget" "monthly_env" {
  count = length(var.billing_alert_emails) > 0 ? 1 : 0

  name        = "${var.project}-${var.environment}-monthly-budget"
  budget_type = "COST"

  limit_amount      = tostring(var.monthly_budget_limit)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "FORECASTED"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    subscriber_email_addresses = var.billing_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "ACTUAL"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    subscriber_email_addresses = var.billing_alert_emails
  }
}
