param([string]$Pptx, [string]$Pdf)
$ErrorActionPreference = "Stop"
$p = New-Object -ComObject PowerPoint.Application
try {
    $d = $p.Presentations.Open($Pptx, $true, $false, $false)
    $d.SaveAs($Pdf, 32)
    Write-Output ("slides: " + $d.Slides.Count)
    $d.Close()
} finally {
    $p.Quit()
}
