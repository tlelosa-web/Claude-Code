' Double-click entry point: launches the NamePlate Tool with no visible
' console windows. See RUN_PIPELINE_HIDDEN.ps1 for the actual launch logic.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set shell = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & scriptDir & "\RUN_PIPELINE_HIDDEN.ps1"""
shell.Run cmd, 0, False
