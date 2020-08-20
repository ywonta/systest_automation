$ErrorActionPreference = "Stop"
$ESXI_OFFLINE_DEPOT='C:\ESXi_70\VMware-ESXi-7.0.0-15843807-dev-depot.zip'
$IONIC_OFFLINE_BUNDLE = 'C:\ESXi_70\VMW-esx-7.0.0-Pensando-ionic-en-1.14-1OEM.700.1.0.15843807.zip'
$ISO_PATH = 'C:\ESXi_70'

write-host "Checking ESXi offline depot image"
if (Test-Path $ESXI_OFFLINE_DEPOT -PathType Leaf)
{
    write-host "ESXi Depot image found!"
}

write-host "Checking for IONIC driver offline bundle"
if (Test-Path $IONIC_OFFLINE_BUNDLE -PathType Leaf)
{
    write-host "IONIC Driver Offline bundle found"
}

write-host "Adding offline depot image"

Add-EsxSoftwareDepot -DepotUrl $ESXI_OFFLINE_DEPOT
#$profile_name = Get-EsxImageProfile | where {$_.Name.endswith("standard") -and $_.Description -match "ESXi"}
$profile_name = Get-EsxImageProfile | where {$_.Name -match "standard"}

write-host "Verifying that IONIC driver doesnt exist in base profile"
if ($profile_name.viblist | select-string -pattern "ionic") {
    throw "Found ionic driver on base image, unable to use this image, script will exit"
}

write-host "Selected profile is $profile_name.name"

$current_time = get-date -format "yyyy-MM-dd-hhmm"
$clone_profile = "ESXi-Clone-" + $current_time

write-host "Cloning $profile_name to $clone_profile"
New-EsxImageProfile -CloneProfile $profile_name.Name -Name $clone_profile -Vendor "Custom"

write-host "Import IONIC offline bundle to software depot"
Add-EsxSoftwareDepot $IONIC_OFFLINE_BUNDLE

$driver_name = Get-EsxSoftwarePackage | select-string -Pattern "ionic"
$driver = $driver_name -split " "
if ($driver[0]){
    write-host "Driver name is $driver[0] Version is $driver[1]"
}
else {
    throw "unable to get driver name and version"
}
Add-EsxSoftwarePackage -ImageProfile $clone_profile -SoftwarePackage $driver[0]

$profile_detail = Get-EsxImageProfile -name $clone_profile

#if (Get-EsxImageProfile -name $clone_profile | select viblist | select-pattern "ionic")
if ($profile_detail.VibList | select-string "ionic-en")
{
    write-host "successfully added ionic driver to ESXi offline depot"
}
else
{
    write-host "slip streaming driver failed, check driver name and image version"
    write-host "if problem persists, try the commands manually"
}

write-host "Exporting $clone_profile to ISO image"
$iso_file = $ISO_PATH + "\" + $clone_profile + ".iso"
Export-EsxImageProfile -ImageProfile $clone_profile -FilePath $iso_file -ExportToIso -NoSignatureCheck
 

