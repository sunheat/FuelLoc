# Windows startup performance

FuelLoc paints the setup window before loading the device stack. The local web interface can start independently of Apple device initialization, so missing device prerequisites do not prevent access to the workspace.

## Implementation

- The Tk launcher completes its initial drawing work before starting background imports.
- Device-stack imports occur during the background prerequisite check or the requested device operation.
- The portable build excludes IPython and traitlets, which are used only by the optional device CLI shell. FuelLoc's device modules remain available.

The startup regression checks cover deferred device imports and importing the device modules without the optional shell packages. See [BUILDING.md](BUILDING.md) for validation commands.

## Measurement

Use `tools/measure_startup.ps1` to measure process launch to the setup window and the first successful local HTTP response. The script starts a fresh process for each run and terminates only that process; it performs no phone operations. The readiness address must be unused before the run.

```powershell
.\tools\measure_startup.ps1 -ExePath .\dist\FuelLoc\FuelLoc.exe -WindowTitle 'FuelLoc setup' -Runs 3 -MaxSeconds 2 -ReadyUrl 'http://127.0.0.1:54321/'
```

Recorded development-machine runs of the optimized launcher opened the setup window in 0.577-0.940 seconds and served the first HTTP response in 0.846-1.470 seconds. These are process-start measurements with the Windows file cache available, not reboot cold-start measurements or performance guarantees for other machines.

For a reboot cold-start measurement, restart Windows and run once with `-Runs 1` before opening or rebuilding FuelLoc. Keep measurements from different startup conditions separate.
