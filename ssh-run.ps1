# ssh-run.ps1 - 自动密码登录 + 执行命令 (PowerShell 5.1 兼容)
param(
    [Parameter(Mandatory=$true)][string]$HostName,
    [Parameter(Mandatory=$true)][string]$User,
    [Parameter(Mandatory=$true)][string]$Password,
    [Parameter(Mandatory=$true)][string]$Command,
    [string]$HostKey = "",
    [int]$Port = 22
)

# Build Arguments string carefully
$sb = New-Object System.Text.StringBuilder
[void]$sb.Append("-ssh -P $Port -pw $Password -batch")
if ($HostKey) {
    # plink -hostkey value (no quotes needed when no spaces)
    [void]$sb.Append(" -hostkey $HostKey")
}
[void]$sb.Append(" ${User}@${HostName}")
# Command 需要单引号包起来, 命令内部的双引号转义
$cmdEscaped = $Command -replace '"', '\"'
[void]$sb.Append(" `"$cmdEscaped`"")

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "C:\Windows\Temp\plink.exe"
$psi.Arguments = $sb.ToString()
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

$proc = [System.Diagnostics.Process]::Start($psi)
$outTask = $proc.StandardOutput.ReadToEndAsync()
$errTask = $proc.StandardError.ReadToEndAsync()
$proc.WaitForExit()
$stdout = $outTask.Result
$stderr = $errTask.Result
if ($stdout) { Write-Output $stdout }
if ($stderr) { Write-Output $stderr }
exit $proc.ExitCode