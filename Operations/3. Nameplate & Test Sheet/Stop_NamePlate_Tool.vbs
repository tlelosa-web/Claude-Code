' Double-click entry point: stops the NamePlate Tool's backend + frontend
' servers. See STOP_PIPELINE.ps1 for the actual stop logic.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set shell = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & scriptDir & "\STOP_PIPELINE.ps1"""
shell.Run cmd, 0, False
