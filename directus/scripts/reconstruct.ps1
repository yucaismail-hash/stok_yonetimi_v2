param(
    [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$composeFile = Join-Path $repositoryRoot "directus\docker-compose.reconstruction.yml"
$snapshotFile = Join-Path $repositoryRoot "directus\schema\schema.snapshot.json"
$python = Join-Path $repositoryRoot "venv\Scripts\python.exe"

function Wait-DirectusReady {
    $ready = $false
    for ($attempt = 1; $attempt -le 90; $attempt++) {
        try {
            $response = Invoke-WebRequest `
                -Uri "http://127.0.0.1:18055/server/ping" `
                -Method Get `
                -TimeoutSec 2 `
                -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            # The image bootstraps and migrates its system schema before serving.
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "Directus did not become ready after bootstrap." }
}

if (-not (Test-Path -LiteralPath $snapshotFile)) {
    throw "Directus schema snapshot is missing."
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Repository Python virtual environment is unavailable."
}

try {
    docker compose -f $composeFile up -d --wait
    if ($LASTEXITCODE -ne 0) { throw "Disposable Directus startup failed." }

    Wait-DirectusReady

    docker compose -f $composeFile exec -T directus `
        node /directus/cli.js schema apply --yes /directus/schema/schema.snapshot.json
    if ($LASTEXITCODE -ne 0) { throw "Directus schema apply failed." }

    # The running API process must reload schema and permission caches after the
    # out-of-process CLI applies the snapshot.
    docker compose -f $composeFile restart directus
    if ($LASTEXITCODE -ne 0) { throw "Directus restart after schema apply failed." }
    Wait-DirectusReady

    & $python (Join-Path $repositoryRoot "directus\scripts\verify_reconstruction.py")
    if ($LASTEXITCODE -ne 0) { throw "Directus reconstruction verification failed." }
}
finally {
    if (-not $KeepRunning) {
        docker compose -f $composeFile down --volumes --remove-orphans
    }
}
