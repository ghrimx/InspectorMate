# Params
param (
    [Parameter(Mandatory = $true)][string]$SectionID,
    [string]$OutputJson
)

# ====== Global variables ======
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
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
$OneNote = New-Object -ComObject OneNote.Application

# ====== Main ======

[xml]$Hierarchy = ""
$OneNote.GetHierarchy($SectionID, [Microsoft.Office.InterOp.OneNote.HierarchyScope]::hsPages, [ref]$Hierarchy)

# Fetch and process pages
foreach($i in $Hierarchy.Section.Page){
	  #DebugPrint($i.ID)

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
                $tag.Cdata = $node.T.InnerText
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
$data | ConvertTo-Json -Depth 5 

IF (![string]::IsNullOrWhitespace($OutputJson)) {
  $utf8NoBOM = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($OutputJson, ($data | ConvertTo-Json -Depth 10), $utf8NoBOM)
}
