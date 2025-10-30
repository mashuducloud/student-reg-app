param(
  [string]$Region = 'us-east-1',                                   # Private ECR region
  [string]$PrivateRepo = 'mashkenneth/student-reg-app',             # Private app repo
  [string]$PublicRepoName = 'mashkenneth-public-student-reg-app',   # Public mirror repo
  [switch]$Recreate,                                                # Re-create repos after purge
  [switch]$Yes                                                      # Required to actually delete
)

$ErrorActionPreference = 'Stop'
$SigRepo = "$PrivateRepo-sig"
$PublicRegion = 'us-east-1' # ECR Public API endpoint

function Require-AwsCli {
  if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI not found. Install it and ensure 'aws' is on PATH."
  }
}

function Test-PrivateRepo([string]$repo) {
  & aws ecr describe-repositories --region $Region --repository-names $repo *> $null
  return ($LASTEXITCODE -eq 0)
}
function Test-PublicRepo([string]$repo) {
  & aws ecr-public describe-repositories --region $PublicRegion --repository-names $repo *> $null
  return ($LASTEXITCODE -eq 0)
}

function Remove-PrivateRepo([string]$repo) {
  if (Test-PrivateRepo $repo) {
    Write-Host "Deleting PRIVATE repo: $repo (region $Region)"
    & aws ecr delete-repository --region $Region --repository-name $repo --force | Out-Null
  } else {
    Write-Host "PRIVATE repo not found, skipping: $repo"
  }
}
function Remove-PublicRepo([string]$repo) {
  if (Test-PublicRepo $repo) {
    Write-Host "Deleting PUBLIC repo: $repo (region $PublicRegion)"
    & aws ecr-public delete-repository --region $PublicRegion --repository-name $repo --force | Out-Null
  } else {
    Write-Host "PUBLIC repo not found, skipping: $repo"
  }
}

function Create-PrivateRepo([string]$repo) {
  if (-not (Test-PrivateRepo $repo)) {
    Write-Host "Creating PRIVATE repo: $repo"
    & aws ecr create-repository --region $Region --repository-name $repo | Out-Null
  }
}
function Create-PublicRepo([string]$repo) {
  if (-not (Test-PublicRepo $repo)) {
    Write-Host "Creating PUBLIC repo: $repo"
    & aws ecr-public create-repository --region $PublicRegion --repository-name $repo | Out-Null
  }
}

# ---- main ----
Require-AwsCli

if (-not $Yes) {
  Write-Host @"
This will DELETE the following ECR repositories (and all images/tags):

  Private ($Region):
    - $PrivateRepo
    - $SigRepo

  Public ($PublicRegion):
    - $PublicRepoName

Usage examples:
  # dry-run prompt
  .\ecr-purge.ps1

  # actually delete
  .\ecr-purge.ps1 -Yes

  # delete and recreate
  .\ecr-purge.ps1 -Yes -Recreate

  # override names/region
  .\ecr-purge.ps1 -Yes -Region us-east-1 -PrivateRepo 'mashkenneth/student-reg-app' -PublicRepoName 'mashkenneth-public-student-reg-app'
"@
  exit 1
}

Remove-PrivateRepo $PrivateRepo
Remove-PrivateRepo $SigRepo
Remove-PublicRepo  $PublicRepoName

if ($Recreate) {
  Create-PrivateRepo $PrivateRepo
  Create-PrivateRepo $SigRepo
  Create-PublicRepo  $PublicRepoName
}

Write-Host "✅ Done."
