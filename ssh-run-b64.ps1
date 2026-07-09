# ssh-run-b64.ps1 - 接受 base64 编码的远端命令
# Args: host user password base64cmd [hostkey] [port]
param(
    [Parameter(Mandatory=$true)][string]$HostName,
    [Parameter(Mandatory=$true)][string]$User,
    [Parameter(Mandatory=$true)][string]$Password,
    [Parameter(Mandatory=$true)][string]$B64Cmd,
    [string]$HostKey = "",
    [int]$Port = 22
)

# decode the remote command
$remoteCmd = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($B64Cmd))

# Wrap command to source profile first (some SSH envs skip /etc/profile)
$wrappedCmd = ". /etc/profile 2>/dev/null; . /etc/bashrc 2>/dev/null; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/bin; " + $remoteCmd

# Write wrapped command to temp file and use -m
$tmpFile = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmpFile, $wrappedCmd, [System.Text.Encoding]::UTF8)

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "C:\Windows\Temp\plink.exe"
$psi.Arguments = "-ssh -P $Port -pw $Password -batch"
if ($HostKey) { $psi.Arguments += " -hostkey $HostKey" }
$psi.Arguments += " ${User}@${HostName} -m `"$tmpFile`""
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
Remove-Item $tmpFile -ErrorAction SilentlyContinue
exit $proc.ExitCode