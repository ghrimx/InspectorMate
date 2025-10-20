# version 2.2
# ====== Params ======
param (
    [Parameter(Mandatory = $true)][string]$SectionID,
    [string]$OutputJson
)

# ====== Global settings ======
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$InformationPreference = 'SilentlyContinue'

# --- Force UTF-8 output for both Windows PowerShell and PowerShell 7+ ---
# --- Safe UTF-8 output setup ---
$utf8 = New-Object System.Text.UTF8Encoding $false
try {
    if ([Console]::Out -ne $null) {
        [Console]::OutputEncoding = $utf8
    }
} catch {
    # no valid console handle; ignore
}
$OutputEncoding = $utf8


[bool]$global:debug = $false

# ====== Debug function ======
function DebugPrint {
    param ([string]$what)
    if ($global:debug -eq $true) {
        Write-Verbose $what
    }
}

# ====== Encoding defaults ======
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Get-Content:Encoding'] = 'utf8'

# ====== Classes ======
Class cTag {
    [string] $TypeName
    [string] $Text
    [string] $Link
    [string] $ID
    [string] $PageID
    [string] $PageName
    [string] $CreationTime
    [string] $LastModifiedTime
    [string] $TypeIndex
}

Class cPage {
    [string] $Name
    [string] $ID
    [string] $Link
    [string] $LastModifiedTime
    [string] $DateTime
    [System.Collections.ArrayList]$tags = @()

    [void]AddItem([cTag]$item) {
        $this.tags.Add($item)
    }
}

# ====== Function ======
function Remove-HtmlTags {
    param (
        [Parameter(Mandatory=$true)][string]$Text
    )
    Add-Type -AssemblyName System.Web
    # Remove all remaining tags
    # Decode HTML entities (&nbsp;, &amp;, etc.)
    $clean = [System.Web.HttpUtility]::HtmlDecode(($text -replace '<[^>]+>', ''))

    # Trim excessive whitespace
    $clean = ($clean -replace '\s{2,}', ' ').Trim()

    return $clean
}

# ====== Main ======
$data = [System.Collections.ArrayList]@()
[string]$sLink = ""

try {
    $OneNote = New-Object -ComObject OneNote.Application
} catch {
    Write-Error "Fail to init OneNote COM object: $_"
    exit 1
}

[xml]$Hierarchy = ""
try {
    $OneNote.GetHierarchy($SectionID, [Microsoft.Office.Interop.OneNote.HierarchyScope]::hsPages, [ref]$Hierarchy)
} catch {
    Write-Error "Fail to get Hierarchy: $_"
    exit 1
}

foreach ($i in $Hierarchy.Section.Page) {
    $page = [cPage]::new()
    $page.ID = $i.ID
    $page.Name = $i.name
    $page.Link = $i.link
    $page.LastModifiedTime = $i.lastModifiedTime
    $page.DateTime = $i.dateTime

    $NewPageXML = ""
    $OneNote.GetPageContent($i.ID, [ref]$NewPageXML, [Microsoft.Office.Interop.OneNote.PageInfo]::piAll)
    $xDoc = New-Object -TypeName System.Xml.XmlDocument
    $xDoc.LoadXml($NewPageXML)

    $ns = [System.Xml.XmlNamespaceManager]::new($xDoc.NameTable)
    $ns.AddNamespace('one', 'http://schemas.microsoft.com/office/onenote/2013/onenote')

    # Build TagDef lookup
    $tagDefs = @{}
    foreach ($node in $xDoc.SelectNodes("//one:TagDef", $ns)) {
        if (-not $tagDefs.Contains($node.index)) {
            $tagDefs[$node.index] = $node.name
        }
    }

    # Process OE tags
    foreach ($node in $xDoc.SelectNodes("//one:OE", $ns)) {
        if ($node.Tag.index) {
            $OneNote.GetHyperLinkToObject($i.ID, $node.objectID, [ref]$sLink)
            $tag = [cTag]::new()
            $tag.ID = $node.objectID
            $tag.TypeName = $tagDefs[$node.Tag.index]
            try {
                $rawText = $node.T.InnerText
                $normalized = $rawText.Normalize([System.Text.NormalizationForm]::FormC)
                $cleanText = $normalized -replace '[^\u0000-\uFFFF]', ''
                $cleanHtml = Remove-HtmlTags $cleanText
                $tag.Text = $cleanHtml
            } catch {
                DebugPrint "Invalid characters in page '$($i.name)'"
            }

            $tag.Link = $sLink
            $tag.PageName = $i.name
            $tag.PageID = $i.ID
            $tag.CreationTime = $node.creationTime
            $tag.LastModifiedTime = $node.lastModifiedTime
            $tag.TypeIndex = $node.Tag.index

            [void]$data.Add($tag)
        }
    }
}

# ====== Export ======
try {
    $json = $data | ConvertTo-Json -Depth 10

    # Output ONLY JSON to stdout (no newline, no extra text)
    [Console]::Write($json)

    # Optional: also write to file if requested
    if (![string]::IsNullOrWhiteSpace($OutputJson)) {
        [System.IO.File]::WriteAllText($OutputJson, $json, [System.Text.UTF8Encoding]::new($false))
    }
} catch {
    Write-Error "Failed to export JSON: $_"
    exit 1
}
