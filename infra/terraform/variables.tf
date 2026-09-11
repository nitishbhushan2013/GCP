variable "project_id" {
  description = "GCP project ID."
  type        = string
  default     = "budgetsense-gcp-prod"
}

variable "region" {
  description = "GCP region (pinned for data residency)."
  type        = string
  default     = "australia-southeast1"
}