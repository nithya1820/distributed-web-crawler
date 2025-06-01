$ProgressPreference = 'SilentlyContinue'
$redisUrl = "https://github.com/tporadowski/redis/releases/download/v6.2.6/Redis-x64-6.2.6.msi"
$redisMsi = "redis.msi"

# Download Redis
Invoke-WebRequest -Uri $redisUrl -OutFile $redisMsi

# Install Redis
Start-Process msiexec.exe -Wait -ArgumentList "/i $redisMsi /quiet"

# Clean up
Remove-Item $redisMsi

Write-Host "Redis installation completed." -ForegroundColor Green
