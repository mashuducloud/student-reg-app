# Create a new IGW and attach it
resource "aws_internet_gateway" "igw" {
  vpc_id = data.aws_vpc.default.id

  tags = {
    Name = "default-vpc-igw"
  }
}

# Public subnets in the default VPC (common in default VPC)
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# Use the VPC main route table (simple approach)
data "aws_route_table" "main" {
  vpc_id = data.aws_vpc.default.id
  filter {
    name   = "association.main"
    values = ["true"]
  }
}

# Check whether the main route table already has 0.0.0.0/0
data "aws_route" "existing_default_route" {
  route_table_id         = data.aws_route_table.main.id
  destination_cidr_block = "0.0.0.0/0"
}

# Create the route only if it doesn't already exist
resource "aws_route" "default_internet_access" {
  count = try(data.aws_route.existing_default_route.id, "") == "" ? 1 : 0

  route_table_id         = data.aws_route_table.main.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}
