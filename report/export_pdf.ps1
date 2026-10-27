param([string]$Docx, [string]$Pdf)
$ErrorActionPreference = "Stop"
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
    $d = $w.Documents.Open($Docx)
    $d.Repaginate()
    foreach ($i in 1..2) {
        foreach ($t in $d.TablesOfContents) { $t.Update() }
        foreach ($t in $d.TablesOfFigures) { $t.Update() }
        $d.Fields.Update() | Out-Null
        $d.Repaginate()
    }
    $d.Save()
    $d.ExportAsFixedFormat($Pdf, 17)
    Write-Output ("pages: " + $d.ComputeStatistics(2))
    $d.Close($false)
} finally {
    $w.Quit()
}
