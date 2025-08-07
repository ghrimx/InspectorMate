param (
    [string]$OutputPy = "onenote_tags.py"
)

# Launch OneNote COM object
try {
    $onenote = New-Object -ComObject OneNote.Application
} catch {
    Write-Error "❌ Failed to create OneNote COM object. Make sure OneNote 2016 is installed."
    exit 1
}

# Namespace
$nsUri = "http://schemas.microsoft.com/office/onenote/2013/onenote"

# Helper: Parse OneNote XML
function Get-Xml($xmlString) {
    $xml = New-Object -TypeName System.Xml.XmlDocument
    $xml.LoadXml($xmlString)
    return $xml
}

# Get notebooks
$onenote.GetHierarchy("", [ref]$notebooksXml, 0)
$notebooksDoc = Get-Xml $notebooksXml
$nsMgr = New-Object System.Xml.XmlNamespaceManager($notebooksDoc.NameTable)
$nsMgr.AddNamespace("one", $nsUri)

$notebookNodes = $notebooksDoc.SelectNodes("//one:Notebook", $nsMgr)

# Collect all tags
$allTags = @()
$allKeys = [System.Collections.Generic.HashSet[string]]::new()

foreach ($notebook in $notebookNodes) {
    $nbId = $notebook.GetAttribute("ID")

    # Get sections in notebook
    $onenote.GetHierarchy($nbId, [ref]$sectionsXml, 1)
    $sectionsDoc = Get-Xml $sectionsXml
    $sectionNodes = $sectionsDoc.SelectNodes("//one:Section", $nsMgr)

    foreach ($section in $sectionNodes) {
        $sectionId = $section.GetAttribute("ID")

        # Get pages in section
        $onenote.GetHierarchy($sectionId, [ref]$pagesXml, 2)
        $pagesDoc = Get-Xml $pagesXml
        $pageNodes = $pagesDoc.SelectNodes("//one:Page", $nsMgr)

        foreach ($page in $pageNodes) {
            $pageId = $page.GetAttribute("ID")

            # Get page content
            $onenote.GetPageContent($pageId, [ref]$contentXml, 0)
            $contentDoc = Get-Xml $contentXml

            # Extract all <one:Tag> nodes
            $tagNodes = $contentDoc.SelectNodes("//one:Tag", $nsMgr)

            foreach ($tag in $tagNodes) {
                $tagDict = @{}

                foreach ($attr in $tag.Attributes) {
                    $tagDict[$attr.Name] = $attr.Value
                    $allKeys.Add($attr.Name) | Out-Null
                }

                # Get <one:T> child if exists
                $textNode = $tag.SelectSingleNode("one:T", $nsMgr)
                $tagDict["text"] = if ($textNode) { $textNode.InnerText } else { "" }
                $allKeys.Add("text") | Out-Null

                $allTags += ,$tagDict
            }
        }
    }
}

# Generate Python dataclass
$py = "from dataclasses import dataclass`n`n@dataclass`nclass Tag:`n"
foreach ($key in $allKeys) {
    $py += "    $key : str`n"
}

# List of Tag(...)
$py += "`ntags = [`n"
foreach ($tag in $allTags) {
    $vals = $allKeys | ForEach-Object {
        $v = if ($tag.ContainsKey($_)) { $tag[$_] } else { "" }
        "'" + ($v -replace "'", "\\'") + "'"
    }
    $py += "    Tag(" + ($vals -join ", ") + "),`n"
}
$py = $py.TrimEnd("`,", "`n") + "`n]"

# Write to file
Set-Content -Path $OutputPy -Value $py -Encoding UTF8
Write-Host "✅ Python dataclass with tags exported to $OutputPy"
