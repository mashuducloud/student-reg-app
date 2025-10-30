terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region
}

# Use default VPC and a default subnet to stay in free tier basics
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu_2204" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

module "ec2_app" {
  source            = "./modules/ec2_docker_app"
  name_prefix       = var.name_prefix
  instance_type     = var.instance_type
  vpc_id            = data.aws_vpc.default.id
  subnet_id         = data.aws_subnets.default.ids[0]
  ssh_public_key    = var.ssh_public_key
  ami_id            = data.aws_ami.ubuntu_2204.id
  allowed_ssh_cidr  = var.allowed_ssh_cidr
  allocate_eip      = true
}

output "public_ip" {
  value       = module.ec2_app.public_ip
  description = "Public IP of the EC2 host"
}

output "ssh_command" {
  value       = "ssh ${module.ec2_app.ssh_user}@${module.ec2_app.public_ip}"
  description = "Convenience SSH command"
}
