param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$WindowTitle,
    [int]$Runs = 3,
    [double]$MaxSeconds = 0,
    [string]$ReadyUrl = ''
)

$ErrorActionPreference = 'Stop'
$resolvedExe = (Resolve-Path -LiteralPath $ExePath).Path
$results = @()
Add-Type -AssemblyName System.Net.Http
$httpClient = [System.Net.Http.HttpClient]::new()
$httpClient.Timeout = [TimeSpan]::FromMilliseconds(200)
for ($run = 1; $run -le $Runs; $run++) {
    if ($ReadyUrl) {
        $existingResponse = $null
        try { $existingResponse = $httpClient.GetAsync($ReadyUrl).GetAwaiter().GetResult() } catch {}
        if ($null -ne $existingResponse) { throw 'Readiness URL is already served by another process' }
    }
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $process = Start-Process -FilePath $resolvedExe -WorkingDirectory (Split-Path $resolvedExe) -PassThru
    try {
        while ($timer.Elapsed.TotalSeconds -lt 30) {
            $process.Refresh()
            if ($process.HasExited) { throw 'Application exited before showing its startup window' }
            if ($process.MainWindowTitle.Contains($WindowTitle)) { break }
            Start-Sleep -Milliseconds 20
        }
        if (-not $process.MainWindowTitle.Contains($WindowTitle)) { throw 'Startup window did not appear within 30 seconds' }
        $windowSeconds = $timer.Elapsed.TotalSeconds
        $serverSeconds = $null
        if ($ReadyUrl) {
            while ($timer.Elapsed.TotalSeconds -lt 30) {
                try {
                    $response = $httpClient.GetAsync($ReadyUrl).GetAwaiter().GetResult()
                    $ready = $response.StatusCode -eq 200
                    $response.Dispose()
                    if ($ready) { $serverSeconds = $timer.Elapsed.TotalSeconds; break }
                } catch {}
                Start-Sleep -Milliseconds 20
            }
            if ($null -eq $serverSeconds) { throw 'Local interface did not respond within 30 seconds' }
        }
        $results += [pscustomobject]@{
            run = $run
            seconds = [math]::Round($windowSeconds, 3)
            server_seconds = if ($null -ne $serverSeconds) { [math]::Round($serverSeconds, 3) } else { $null }
            cpu_seconds = [math]::Round($process.TotalProcessorTime.TotalSeconds, 3)
            title = $process.MainWindowTitle
        }
    } finally {
        if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
    }
}
$httpClient.Dispose()
$results | ConvertTo-Json
if ($MaxSeconds -gt 0 -and ($results | Where-Object { $_.seconds -ge $MaxSeconds -or $_.server_seconds -ge $MaxSeconds })) {
    throw "Startup exceeded the $MaxSeconds second budget"
}
