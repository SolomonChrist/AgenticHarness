# n8n Harness

This folder contains optional utilities for letting n8n participate in an
Agentic Harness install through the same shared files.

## Folder Mirror

`folder_mirror.py` keeps two folders synchronized:

- the main local Agentic Harness folder
- a mirror folder, such as a Google Drive synced folder that n8n can access

Basic setup:

1. Run setup.
2. Choose any source Agentic Harness folder.
3. Choose any mirror folder, such as a Google Drive synced folder.
4. Let setup create the first cloned copy.
5. Keep the mirror daemon running while n8n is active.

Interactive setup:

```powershell
py n8n_harness\setup_folder_mirror.py
```

Windows setup helper:

```powershell
n8n_harness\setup_folder_mirror.bat
```

The setup writes `n8n_harness\mirror_config.local.json`. That file is
machine-specific and optional; recreate it on each user's machine.

Example:

```powershell
py n8n_harness\folder_mirror.py --left "C:\Users\info\OneDrive\Desktop\AgenticHarness\TESTING" --right "G:\My Drive\AgenticHarness_MainSystem"
```

After setup, you can start from the saved config:

```powershell
py n8n_harness\folder_mirror.py --config n8n_harness\mirror_config.local.json
```

Windows helper:

```powershell
n8n_harness\start_folder_mirror.bat "C:\Users\info\OneDrive\Desktop\AgenticHarness\TESTING" "G:\My Drive\AgenticHarness_MainSystem"
```

After setup, the Windows helper can run without arguments:

```powershell
n8n_harness\start_folder_mirror.bat
```

By default, deletion propagation is off. Add `--delete` only after confirming
both paths are correct and the initial mirror looks right.

The mirror state file is stored outside both mirrored folders under
`LOCALAPPDATA`, so mirror bookkeeping does not create sync loops.

## Workflow JSON

No n8n workflow JSON is bundled yet. Add exported workflow JSON files here when
they are ready to ship.
