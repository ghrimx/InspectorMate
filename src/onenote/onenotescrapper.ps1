# version 2.1
# Params
param (
    [Parameter(Mandatory = $true)][string]$SectionID,
    [string]$OutputJson
)

# ====== Global variables ======
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[bool]$global:debug = $false


function DebugPrint {
    param ([string]$what)
    if($global:debug -eq $true) {
        Write-Host $what
    }
}


try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
} catch {
    DebugPrint "Console output encoding could not be set: $_"
}


$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Get-Content:Encoding'] = 'utf8'

# ====== Class ======
Class cTag {
  # Define variables
  [string] $Name
  [string] $Cdata
  [string] $Link
  [string] $ID # ID of the parent OE
  [string] $PageID
  [string] $PageName
  [string] $creationTime
  [string] $lastModifiedTime
  [string] $index

  # Class contructor
  cTag() {
  }

  # Define methods
  DisplayProperties() {
    write-host "Name:" $this.name
    write-host "Link:" $this.link
    write-host "ID:" $this.ID
    write-host "Page ID:" $this.pageID
  }
} # End of Class 'cTag'


Class cPage {
  # Define variables
  [string] $Name
  [string] $ID
  [string] $Link
  [string] $lastModifiedTime
  [string] $dateTime
  [System.Collections.ArrayList]$tags = @()

  # Class contructor
  cPage() {
  }

  [void]AddItem([cTag]$item) {
    $this.tags.Add($item)
  }

  # Define methods
  DisplayProperties() {
    write-host "Name:" $this.name
    write-host "Link:" $this.link
    write-host "ID:" $this.ID
    write-host "lastModifiedTime:" $this.lastModifiedTime
  }
} # End of Class 'cPage'

# ====== Housekeeping ======
# Declaration
$data = @{}
[string]$sLink = ""

# Init OneNote object
try {
    $OneNote = New-Object -ComObject OneNote.Application
} catch {
    DebugPrint "Fail to init ComObject"
}


# ====== Main ======

[xml]$Hierarchy = ""
try {
    $OneNote.GetHierarchy($SectionID, [Microsoft.Office.InterOp.OneNote.HierarchyScope]::hsPages, [ref]$Hierarchy)
} catch {
    DebugPrint "Fail to get Hierarchy"
}



# Fetch and process pages
foreach($i in $Hierarchy.Section.Page){

    DebugPrint "Page_id: $($i.Name)"
	
    $page = New-Object cPage
    $page.ID = $i.ID
    $page.Name = $i.name
    $page.Link = $i.link
    $page.lastModifiedTime = $i.lastModifiedTime
    $page.dateTime = $i.dateTime
	
    $NewPageXML = ""
    $OneNote.GetPageContent($i.ID,[ref]$NewPageXML,[Microsoft.Office.Interop.OneNote.PageInfo]::piAll)
    $xDoc = New-Object -TypeName System.Xml.XmlDocument
    $xDoc.LoadXml($NewPageXML)
    

    $namespaceManager = [System.Xml.XmlNamespaceManager]::new($xDoc.NameTable)
    $namespaceManager.AddNamespace('one', 'http://schemas.microsoft.com/office/onenote/2013/onenote')
    
    # Create TagDef hastable
    $hashtable = @{}
    $nodes = $xDoc.SelectNodes("//one:TagDef",$namespaceManager)
    if($nodes.Count -ge 1){
        foreach ($node in $nodes){
            if (-not $hashtable.Contains($node.index)) {
            $hashtable.Add($node.index, $node.Name)
            }
        }
    }

    # Go thru each OE node and get Tag
    $nodes = $xDoc.SelectNodes("//one:OE",$namespaceManager)
    if($nodes.Count -ge 1){
        foreach ($node in $nodes){
            if ($node.Tag.index){
                $OneNote.GetHyperLinkToObject($i.ID,$node.objectID,[ref]$sLink) 
                $tag = New-Object cTag
                $tag.ID = $node.objectID
                $tag.Name = $hashtable[$node.Tag.index]
                
                
                try {
                    $rawText = $node.T.InnerText
                    
                    if ($rawText -match '\\u[0-9A-Fa-f]{4}') {
                        DebugPrint "Escaped Unicode found in page '$($i.name)'"
                    }

                    $normalizedText = [System.Text.NormalizationForm]::FormC
                    $rawText.Normalize($normalizedText)
                    $decodedText = [System.Text.RegularExpressions.Regex]::Unescape($rawText)
                    $cleanText = $rawText -replace '[^\u0000-\uFFFF]', ''  # Removes characters outside valid
                    $tag.Cdata = $cleanText
                } catch {
                    DebugPrint "Invalid characters in page '$($i.name)' (ID: $($i.ID))"
                }

                $tag.Link = $sLink
                $tag.PageName = $i.name
                $tag.PageID = $i.ID
                $tag.creationTime = $node.creationTime
                $tag.lastModifiedTime = $node.lastModifiedTime
                $tag.index = $node.Tag.index

                $page.AddItem($tag)
                
            }   
        }
    }
    $data.Add($page.Name, $page)
}

# Export

$timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
try {
    $json = $data | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($OutputJson, $json, $utf8NoBom)
} catch {
    DebugPrint "Failed to export JSON: $_"
}

