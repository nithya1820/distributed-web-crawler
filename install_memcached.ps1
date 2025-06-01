$ProgressPreference = 'SilentlyContinue'
$memcachedUrl = "https://github.com/memcached/memcached/releases/download/1.6.22/memcached-1.6.22-64bit.msi"
$memcachedMsi = "memcached.msi"

# Download Memcached
Invoke-WebRequest -Uri $memcachedUrl -OutFile $memcachedMsi

# Install Memcached
Start-Process msiexec.exe -Wait -ArgumentList "/i $memcachedMsi /quiet"

# Clean up
Remove-Item $memcachedMsi

Write-Host "Memcached installation completed." -ForegroundColor Green
