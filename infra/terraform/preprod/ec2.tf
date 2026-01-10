locals {
  common_user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker

    systemctl enable amazon-ssm-agent || true
    systemctl start amazon-ssm-agent || true
  EOF
}

resource "aws_instance" "frontend" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.frontend_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.common_user_data

  tags = { Name = "${var.project}-${var.env}-frontend" }
}

resource "aws_instance" "backend" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.backend_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.common_user_data

  tags = { Name = "${var.project}-${var.env}-backend" }
}

resource "aws_instance" "flyway" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.flyway_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  user_data              = local.common_user_data

  tags = { Name = "${var.project}-${var.env}-flyway" }
}
