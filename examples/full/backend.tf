terraform {
  backend "s3" {
    bucket         = "sbeacon-terraform-states"
    key            = "sbeacon"
    region         = "ap-southeast-2"
    dynamodb_table = "terraform-state-locks"
  }
}
