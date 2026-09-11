resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal"
  project = var.project_id
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  priority  = 1000

  source_ranges = [
    "10.10.0.0/24",
    "10.10.1.0/24",
    "10.10.2.0/28",
  ]

  allow {
    protocol = "all"
  }
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "allow-health-checks"
  project = var.project_id
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  priority  = 1000

  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16",
  ]

  allow {
    protocol = "tcp"
  }
}

resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "allow-iap-ssh"
  project = var.project_id
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  priority  = 1000

  source_ranges = ["35.235.240.0/20"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "deny_all_ingress" {
  name    = "deny-all-ingress"
  project = var.project_id
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  priority  = 65534

  source_ranges = ["0.0.0.0/0"]
  deny {
    protocol = "all"
  }
}