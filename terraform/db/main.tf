resource "aws_db_subnet_group" "this" {
  name       = "student-reg-${var.env_name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "student-reg-${var.env_name}-db-subnet-group"
  }
}

resource "aws_security_group" "db" {
  name        = "student-reg-${var.env_name}-db-sg"
  description = "Security group for RDS SQL Server"
  vpc_id      = var.vpc_id

  # Allow SQL Server (port 1433) from inside the VPC only
  ingress {
    description = "SQL Server from VPC"
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "student-reg-${var.env_name}-db-sg"
  }
}

resource "aws_db_instance" "this" {
  identifier = "student-reg-${var.env_name}-db"

  engine         = "sqlserver-ex"
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage

  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]

  backup_retention_period = var.backup_retention_period
  multi_az                = var.multi_az

  publicly_accessible = false
  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name = "student-reg-${var.env_name}-db"
  }
}

output "db_endpoint" {
  description = "RDS SQL Server endpoint"
  value       = aws_db_instance.this.address
}
