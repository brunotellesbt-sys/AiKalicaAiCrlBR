param([string]$Destination = "$PSScriptRoot\..\..\.local\windows-validation")
$ErrorActionPreference = 'Stop'
trap {
    $message = $_.Exception.Message.Replace("`r", ' ').Replace("`n", ' ')
    Write-Output "::error::$message"
    throw
}
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$report = Join-Path $repo '.local\windows-report'
New-Item -ItemType Directory -Force $report | Out-Null
python "$repo\tools\install_portable.py" --destination $Destination
if ($LASTEXITCODE -ne 0) { throw 'Portable installation failed' }
$Destination = (Resolve-Path $Destination).Path
$runtimes = & "$Destination\dotnet\dotnet.exe" --list-runtimes
if ($LASTEXITCODE -ne 0 -or !($runtimes -match 'Microsoft.WindowsDesktop.App 6.0.36') -or !($runtimes -match 'Microsoft.NETCore.App 6.0.36')) {
    throw 'Windows desktop/core runtime validation failed'
}
$runtimes | Set-Content "$report\runtimes.txt"
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class DesktopProbe {
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr window, out Rect rect);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr window, uint message, IntPtr wparam, IntPtr lparam);
    [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left, Top, Right, Bottom; }
}
'@
$rom = Join-Path $repo 'Pokemon - Leaf Green Version (U) (V1.1).gba'
$expected = '2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825'
if ((Get-FileHash $rom -Algorithm SHA256).Hash.ToLower() -ne $expected) { throw 'Unexpected original ROM hash' }
$copy = Join-Path $report 'working.gba'
Copy-Item $rom $copy -Force
$results = @()
try {
    foreach ($tool in @('HexManiacAdvance', 'AdvanceMap', 'XSE')) {
        # Launch the actual distributed .cmd, so quoting, working directory and the local runtime are exercised.
        $arguments = '/d /s /c ""' + (Join-Path $Destination "$tool.cmd") + '"'
        if ($tool -eq 'HexManiacAdvance') { $arguments += ' "' + $copy + '"' }
        $arguments += '"'
        $launcher = Start-Process $env:ComSpec -ArgumentList $arguments -PassThru
        $pattern = @{ HexManiacAdvance = 'Hex Maniac Advance'; AdvanceMap = 'Advance.?Map'; XSE = 'eXtreme Script Editor|XSE' }[$tool]
        $process = $null
        $deadline = (Get-Date).AddSeconds(60)
        while ((Get-Date) -lt $deadline) {
            $candidates = if ($tool -eq 'HexManiacAdvance') { @(Get-Process dotnet -ErrorAction SilentlyContinue) } else { @(Get-Process $tool -ErrorAction SilentlyContinue) }
            foreach ($candidate in $candidates) {
                $candidate.Refresh()
                if ($candidate.MainWindowHandle -ne [IntPtr]::Zero -and [DesktopProbe]::IsWindowVisible($candidate.MainWindowHandle) -and $candidate.MainWindowTitle -match $pattern) {
                    $process = $candidate
                    break
                }
            }
            if ($process) { break }
            $launcher.Refresh()
            if ($launcher.HasExited) { throw "$tool launcher exited before displaying its interface: $($launcher.ExitCode)" }
            Start-Sleep -Milliseconds 500
        }
        if (!$process) { throw "$tool did not display a visible window within 60 seconds" }
        Start-Sleep -Seconds 3
        $process.Refresh()
        if ($process.HasExited -or !$process.Responding) { throw "$tool exited or stopped responding" }
        $title = $process.MainWindowTitle
        if ($title -notmatch $pattern) { throw "$tool opened an unexpected window: $title" }
        $rect = New-Object DesktopProbe+Rect
        if (![DesktopProbe]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) { throw 'Cannot capture application window' }
        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top
        Write-Host "$tool screenshot: $width x $height ($title)"
        if ($width -lt 50 -or $height -lt 50) { throw "$tool has no usable window rectangle: $width x $height" }
        $bitmap = [Drawing.Bitmap]::new([int]$width, [int]$height)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
            $bitmap.Save((Join-Path $report "$tool.png"), [Drawing.Imaging.ImageFormat]::Png)
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
        $results += [pscustomobject]@{ tool = $tool; title = $title; pid = $process.Id; visible = $true; responding = $true }
        [DesktopProbe]::PostMessage($process.MainWindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
        if (!$launcher.WaitForExit(10000)) { throw "$tool launcher did not finish after closing the window" }
        if ($launcher.ExitCode -ne 0) { throw "$tool launcher returned $($launcher.ExitCode)" }
    }
} finally {
    $results | ConvertTo-Json -Depth 3 | Set-Content "$report\results.json"
    if ((Get-FileHash $rom -Algorithm SHA256).Hash.ToLower() -ne $expected) { throw 'Original ROM changed' }
    Remove-Item $copy -ErrorAction SilentlyContinue
}
Write-Host 'PASS: all three Windows launchers displayed responsive application windows; original ROM preserved.'
