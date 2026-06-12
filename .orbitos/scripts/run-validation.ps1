param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

function Read-JsonLikeFile {
  param([string]$Path)
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  $document = [System.Text.Json.JsonDocument]::Parse($raw)
  try {
    return Convert-JsonElement $document.RootElement
  } finally {
    $document.Dispose()
  }
}

function Convert-JsonElement {
  param([System.Text.Json.JsonElement]$Element)

  switch ($Element.ValueKind) {
    "Object" {
      $map = @{}
      foreach ($property in $Element.EnumerateObject()) {
        if ($property.Value.ValueKind -eq [System.Text.Json.JsonValueKind]::Array) {
          $items = New-Object System.Collections.Generic.List[object]
          foreach ($item in $property.Value.EnumerateArray()) {
            $items.Add((Convert-JsonElement $item)) | Out-Null
          }
          $map[$property.Name] = [object[]]$items.ToArray()
        } else {
          $map[$property.Name] = Convert-JsonElement $property.Value
        }
      }
      return $map
    }
    "Array" {
      $items = New-Object System.Collections.Generic.List[object]
      foreach ($item in $Element.EnumerateArray()) {
        $items.Add((Convert-JsonElement $item)) | Out-Null
      }
      return ,$items.ToArray()
    }
    "String" {
      return $Element.GetString()
    }
    "Number" {
      $longValue = 0L
      if ($Element.TryGetInt64([ref]$longValue)) { return $longValue }
      return $Element.GetDouble()
    }
    "True" {
      return $true
    }
    "False" {
      return $false
    }
    "Null" {
      return $null
    }
    default {
      return $null
    }
  }
}

function Has-Property {
  param($Object, [string]$Name)
  if ($Object -is [System.Collections.IDictionary]) {
    return $Object.Contains($Name)
  }
  return $null -ne $Object.PSObject.Properties[$Name]
}

function Get-PropertyValue {
  param($Object, [string]$Name)
  if ($Object -is [System.Collections.IDictionary]) {
    if ($Object.Contains($Name)) {
      $value = $Object[$Name]
      if ($value -is [System.Array]) { return ,$value }
      return $value
    }
    return $null
  }
  $prop = $Object.PSObject.Properties[$Name]
  if ($null -eq $prop) { return $null }
  if ($prop.Value -is [System.Array]) { return ,$prop.Value }
  return $prop.Value
}

function Get-AllowedTypes {
  param($Schema)
  if (-not (Has-Property $Schema "type")) { return @() }
  $type = Get-PropertyValue $Schema "type"
  if ($type -is [System.Array]) { return @($type) }
  return @($type)
}

function Test-Type {
  param($Value, [string[]]$AllowedTypes)
  if ($AllowedTypes.Count -eq 0) { return $true }

  foreach ($type in $AllowedTypes) {
    switch ($type) {
      "null" {
        if ($null -eq $Value) { return $true }
      }
      "string" {
        if ($Value -is [string]) { return $true }
      }
      "boolean" {
        if ($Value -is [bool]) { return $true }
      }
      "integer" {
        if (($Value -is [int]) -or ($Value -is [long])) { return $true }
      }
      "number" {
        if (($Value -is [int]) -or ($Value -is [long]) -or ($Value -is [double]) -or ($Value -is [decimal])) { return $true }
      }
      "array" {
        if (($Value -is [System.Array]) -or ($Value -is [System.Collections.IList])) { return $true }
      }
      "object" {
        if (($Value -is [pscustomobject]) -or ($Value -is [System.Collections.IDictionary])) { return $true }
      }
    }
  }

  return $false
}

function Test-Enum {
  param($Value, $EnumValues)
  foreach ($enumValue in @($EnumValues)) {
    if ($null -eq $enumValue -and $null -eq $Value) { return $true }
    if ($Value -eq $enumValue) { return $true }
  }
  return $false
}

function Add-ValidationError {
  param([System.Collections.Generic.List[object]]$Errors, [string]$Path, [string]$Message)
  $Errors.Add([pscustomobject]@{ path = $Path; message = $Message }) | Out-Null
}

function Test-ValueAgainstSchema {
  param(
    $Value,
    $Schema,
    [string]$Path,
    [System.Collections.Generic.List[object]]$Errors
  )

  $allowedTypes = Get-AllowedTypes $Schema
  if (-not (Test-Type $Value $allowedTypes)) {
    Add-ValidationError $Errors $Path ("type mismatch; expected " + ($allowedTypes -join "|"))
    return
  }

  if (Has-Property $Schema "enum") {
    if (-not (Test-Enum $Value (Get-PropertyValue $Schema "enum"))) {
      Add-ValidationError $Errors $Path "value is not in enum"
    }
  }

  if (($allowedTypes -contains "object") -and (($Value -is [pscustomobject]) -or ($Value -is [System.Collections.IDictionary]))) {
    $properties = if (Has-Property $Schema "properties") { Get-PropertyValue $Schema "properties" } else { $null }
    $required = if (Has-Property $Schema "required") { @(Get-PropertyValue $Schema "required") } else { @() }

    foreach ($requiredName in $required) {
      if (-not (Has-Property $Value $requiredName)) {
        Add-ValidationError $Errors "$Path.$requiredName" "missing required field"
      }
    }

    if ((Has-Property $Schema "additionalProperties") -and ((Get-PropertyValue $Schema "additionalProperties") -eq $false) -and $null -ne $properties) {
      $valueNames = if ($Value -is [System.Collections.IDictionary]) { @($Value.Keys) } else { @($Value.PSObject.Properties.Name) }
      foreach ($propName in $valueNames) {
        if (-not (Has-Property $properties $propName)) {
          Add-ValidationError $Errors "$Path.$propName" "additional property is not allowed"
        }
      }
    }

    if ($null -ne $properties) {
      $schemaNames = if ($properties -is [System.Collections.IDictionary]) { @($properties.Keys) } else { @($properties.PSObject.Properties.Name) }
      foreach ($schemaName in $schemaNames) {
        if (Has-Property $Value $schemaName) {
          Test-ValueAgainstSchema (Get-PropertyValue $Value $schemaName) (Get-PropertyValue $properties $schemaName) "$Path.$schemaName" $Errors
        }
      }
    }
  }

  if (($allowedTypes -contains "array") -and (($Value -is [System.Array]) -or ($Value -is [System.Collections.IList])) -and (Has-Property $Schema "items")) {
    for ($i = 0; $i -lt $Value.Count; $i++) {
      Test-ValueAgainstSchema $Value[$i] (Get-PropertyValue $Schema "items") "$Path[$i]" $Errors
    }
  }
}

function Test-LifecycleTransition {
  param($Value, $Schema, [System.Collections.Generic.List[object]]$Errors)
  $from = if (Has-Property $Value "previous_status") { Get-PropertyValue $Value "previous_status" } else { $null }
  $to = Get-PropertyValue $Value "status"
  $fromKey = if ($null -eq $from) { "" } else { "$from" }
  $pair = "$fromKey|$to"
  $allowedPairs = @(
    "|raw",
    "raw|triaged",
    "triaged|confirmed",
    "confirmed|processed",
    "processed|archived",
    "raw|archived"
  )
  if ($allowedPairs -contains $pair) { return }

  Add-ValidationError $Errors '$.status' "illegal lifecycle transition: $from -> $to"
}

$schemaRoot = Join-Path $Root ".orbitos\schemas"
$caseRoot = Join-Path $Root ".orbitos\evals\cases"

$schemas = @{
  "event" = Read-JsonLikeFile (Join-Path $schemaRoot "event.schema.yaml")
  "inbox-triage" = Read-JsonLikeFile (Join-Path $schemaRoot "inbox-triage.schema.yaml")
  "lifecycle" = Read-JsonLikeFile (Join-Path $schemaRoot "lifecycle.schema.yaml")
  "core-change" = Read-JsonLikeFile (Join-Path $schemaRoot "core-change.schema.yaml")
}

$failureCount = 0
$cases = Get-ChildItem -LiteralPath $caseRoot -Filter "*.yaml" | Sort-Object Name

foreach ($case in $cases) {
  $name = $case.Name
  $schemaName = if ($name.StartsWith("inbox-triage.")) {
    "inbox-triage"
  } elseif ($name.StartsWith("core-change.")) {
    "core-change"
  } elseif ($name.StartsWith("event.")) {
    "event"
  } elseif ($name.StartsWith("lifecycle.")) {
    "lifecycle"
  } else {
    throw "Cannot infer schema for case: $name"
  }

  $expectedValid = $name -like "*.valid.*"
  $data = Read-JsonLikeFile $case.FullName
  $schema = $schemas[$schemaName]
  $errors = New-Object System.Collections.Generic.List[object]

  Test-ValueAgainstSchema $data $schema '$' $errors
  if ($schemaName -eq "lifecycle") {
    Test-LifecycleTransition $data $schema $errors
  }

  $actualValid = $errors.Count -eq 0
  if ($actualValid -ne $expectedValid) {
    $failureCount += 1
  }

  $status = if ($actualValid -eq $expectedValid) { "PASS" } else { "FAIL" }
  Write-Host "$status $name"
  foreach ($err in $errors) {
    Write-Host "  - $($err.path): $($err.message)"
  }
}

if ($failureCount -gt 0) {
  Write-Host ""
  Write-Host "Validation eval failed: $failureCount case(s)."
  exit 1
}

Write-Host ""
Write-Host "Validation eval passed: $($cases.Count) case(s)."
