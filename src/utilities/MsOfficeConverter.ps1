Param
    (
        [Parameter(Mandatory=$true)] [ValidateScript({Test-Path $_})] [string]$filePath,
		[Parameter(Mandatory=$true)] [string]$outputFile
    )

function ReleaseComObject {
	param([__ComObject]$Object)

	if (-not $Object) { return }

	try {
		$referenceCount = 0
		do {
			$referenceCount = [System.Runtime.InteropServices.Marshal]::ReleaseComObject($Object)
		}
		while ($referenceCount -gt 0)

		$Object = $null
	}
	finally {
		[GC]::Collect()
		[GC]::WaitForPendingFinalizers()
	}
}

# Excel
function Start-Excel {
	if ($Global:ApplicationExcel) { return $Global:ApplicationExcel }

	Add-type -AssemblyName Microsoft.Office.Interop.Excel

	$processExcel = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
	foreach ($process in $processExcel) { $process.Kill() }

	$Global:ApplicationExcel = New-Object -ComObject Excel.Application

	Start-Sleep -Seconds 2
	$Global:ApplicationExcel.Visible = $false
	$Global:ApplicationExcel.DisplayAlerts = $false
	return $Global:ApplicationExcel
}
function Close-Excel {
	if (-not $Global:ApplicationExcel) { return }

	if ($Global:ApplicationExcel.ActiveWorkbook) {
		$saveChanges = $false
		foreach ($sheet in $ApplicationExcel.ActiveWorkbook.Sheets) {
			ReleaseComObject -Object $sheet
		}
		$Global:ApplicationExcel.ActiveWorkbook.Close($saveChanges)
		ReleaseComObject -Object $Global:ApplicationExcel.ActiveWorkbook
	}

	$Global:ApplicationExcel.Workbooks.Close()
	ReleaseComObject -Object $Global:ApplicationExcel.Workbooks

	$Global:ApplicationExcel.Quit()
	ReleaseComObject -Object $Global:ApplicationExcel

	Remove-Variable -Name ApplicationExcel -Scope:Global
	Start-Sleep -Seconds 1
}
function Export-XlsToPdf {
	param(
		[System.IO.FileInfo]$InputObject,
		[System.IO.FileInfo]$Path
	)

	$ApplicationExcel = Start-Excel

	$filename = $InputObject.FullName
	$updateLinks = 3
	$readOnly = $true
	$IgnorePrintAreas = $true
	$Workbook = $ApplicationExcel.Workbooks.Open($filename, $updateLinks, $readOnly)

	$quality = [Microsoft.Office.Interop.Excel.XlFixedFormatQuality]::xlQualityStandard
	$includeDocProperties = $true
	$destinationFilename = $Path
	$Workbook.ExportAsFixedFormat([Microsoft.Office.Interop.Excel.XlFixedFormatType]::xlTypePDF, $destinationFilename, $quality, $includeDocProperties, $IgnorePrintAreas)
	
	Close-Excel

	if ( Test-Path $Path.FullName ) { return Get-Item $Path.FullName }
	return $null
}
# Excel

# Word
function Start-Word {
	if ($Global:ApplicationWord) { return $Global:ApplicationWord }

	Add-type -AssemblyName Microsoft.Office.Interop.Word

	$Global:ApplicationWord = New-Object -ComObject Word.Application
	Start-Sleep -Seconds 2
	$Global:ApplicationWord.Visible = $false
	return $Global:ApplicationWord
}
function Close-Word {

	if (-not $Global:ApplicationWord) { return }

	if ($Global:ApplicationWord.Documents) {
		$saveChanges = $false
		foreach ($document in $Global:ApplicationWord.Documents) {
			$document.Close($saveChanges)
			ReleaseComObject -Object $document
		}
	}

	$Global:ApplicationWord.Quit([ref][Microsoft.Office.Interop.Word.WdSaveOptions]::wdDoNotSaveChanges)
	ReleaseComObject -Object $Global:ApplicationWord

	Remove-Variable -Name ApplicationWord -Scope:Global
	Start-Sleep -Seconds 1
}
function Export-DocToPdf {
	param(
		[System.IO.FileInfo]$InputObject,
		[System.IO.FileInfo]$Path
	)

	$ApplicationWord = Start-Word

	$filename = $InputObject.FullName
	$confirmConversions = $false
	$readOnly = $true
	$addToRecentFiles = $false
	$passwordDocument = ""
	$passwordTemplate = ""
	$revert = $true
	$writePasswordDocument = ""
	$writePasswordTemplate = ""
	$format = [Microsoft.Office.Interop.Word.WdOpenFormat]::wdOpenFormatAuto
	$encoding = [Microsoft.Office.Core.MsoEncoding]::msoEncodingUSASCII

	$Document = $ApplicationWord.Documents.Open([ref]$filename,	[ref]$confirmConversions,	[ref]$readOnly,	[ref]$addToRecentFiles,
		[ref]$passwordDocument, [ref]$passwordTemplate, [ref]$revert, [ref]$writePasswordDocument,
		[ref]$writePasswordTemplate, [ref]$format, [ref]$encoding)

	$Document.SaveAs([ref]$Path.FullName, [ref][Microsoft.Office.Interop.Word.WdSaveFormat]::wdFormatPDF)
	
	Close-Word 
	
	if ( Test-Path $Path ) { return Get-Item $Path }
	return $null
}
# Word

# PowerPoint
function Start-Powerpoint {
	if ($Global:ApplicationPowerPoint) { return $Global:ApplicationPowerPoint }

	Add-type -AssemblyName Microsoft.Office.Interop.PowerPoint

	$Global:ApplicationPowerPoint = New-Object -ComObject PowerPoint.Application
	Start-Sleep -Seconds 2
	return $Global:ApplicationPowerPoint
}
function Close-Powerpoint {

	if (-not $Global:ApplicationPowerPoint) { return }

	if ($Global:ApplicationPowerPoint.Presentations) {
		$saveChanges = $false
		foreach ($document in $Global:ApplicationPowerPoint.Presentations) {
			$document.Close($saveChanges)
			ReleaseComObject -Object $document
		}
	}

	$Global:ApplicationPowerPoint.Quit()
	ReleaseComObject -Object $Global:ApplicationPowerPoint

	Remove-Variable -Name ApplicationPowerPoint -Scope:Global
	Start-Sleep -Seconds 1
}
function Export-PPtToPdf {
	param(
		[System.IO.FileInfo]$InputObject,
		[System.IO.FileInfo]$Path
	)

	$ApplicationPowerPoint = Start-Powerpoint

	$filename = $InputObject.FullName
	$readOnly = [Microsoft.Office.Core.MsoTriState]::msoFalse
    $untitled = [Microsoft.Office.Core.MsoTriState]::msoFalse
    $WithWindow = [Microsoft.Office.Core.MsoTriState]::msoFalse
    $format = [Microsoft.Office.Interop.PowerPoint.PpSaveAsFileType]::ppSaveAsPDF
    $EmbedFonts = [Microsoft.Office.Core.MsoTriState]::msoFalse

    $Document = $ApplicationPowerPoint.Presentations.Open($filename,[ref]$readOnly, [ref]$untitled, [ref]$WithWindow)
    $Document.SaveAs($Path, [ref]$format, [ref]$EmbedFonts)
    $Document.Close()

    Close-Powerpoint

	if ( Test-Path $Path ) { return Get-Item $Path }
	return $null
}
# End PowerPoint

$word_ext = @('.doc','.docx')
$excel_ext = @('.xls','.xlsx')
$ppt_ext = @('.ppt','.pptx')

$ext = [System.IO.Path]::GetExtension($filePath)

if ($ext -in $word_ext) {
    Export-DocToPdf $filePath $outputFile
}
elseif ($ext -in $excel_ext) {
	Export-XlsToPdf $filePath $outputFile
}
elseif ($ext -in $ppt_ext){
    Export-PPtToPdf $filePath $outputFile
}
