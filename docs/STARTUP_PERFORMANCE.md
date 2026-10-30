# Windows startup measurements

Measured on the same Windows machine with `tools/measure_startup.ps1`. Every run starts a new process and terminates only that measured process after collecting results. No iPhone connection or location operation is performed.

The window metric runs from process launch until Windows exposes the expected startup window title. The HTTP metric runs from the same launch until the local interface returns HTTP 200. The final launcher paints its widgets before starting background imports.

## Results

Times are seconds. A new-directory first launch uses a complete copy of the portable folder at a previously unused path. Subsequent runs use that same path.

| Build | New-directory first window | Subsequent windows | First HTTP response |
| --- | ---: | --- | ---: |
| Adjacent iOSLocationTrack app | 1.618 | 0.779, 0.866 | Not measured: its setup screen gates server startup |
| FuelLoc before this optimization | 1.411 | 1.073, 1.887 | Not measured in this comparison |
| Final FuelLoc | 0.940 | 0.739, 0.877 | 1.361 |

Five additional final-build runs in the normal distribution directory produced window times of `0.882, 0.577, 0.673, 0.639, 0.671` and HTTP times of `1.388, 0.846, 1.332, 1.317, 1.327`. All eight final-build runs passed the two-second budget for both metrics. The other two HTTP times in the new-directory copy were `1.326, 1.470`.

The previous 10.7-second observation was a first launch after a build, not a controlled Windows reboot cold-start measurement. It did not reproduce reliably. Windows was not rebooted and its file cache was not cleared for this comparison. Copying a folder also reads its files, so a new-directory first launch is **not** a substitute for an empty-cache cold start. These results cannot guarantee a two-second launch after reboot or on another machine.

## Changes and evidence

- The launcher previously started the import worker before Tk had painted the window. It now completes the initial idle drawing work first.
- The HTTP interface previously imported the full phone stack during module initialization. Those imports now happen during the background device check or the requested device operation. A subprocess regression test rejects any phone-stack import before the local page can be served.
- IPython and traitlets are used only by the optional interactive device CLI shell. Excluding them reduced the portable package from **8,007 files / 97,013,551 bytes** to **2,447 files / 80,176,682 bytes**, chiefly removing 5,536 Jedi completion-data files. A subprocess test verifies all device modules used by FuelLoc can import when these shell packages are unavailable.
- Excluding IPython alone was insufficient: that experimental build measured `3.262, 4.036, 3.518` seconds to its window and failed the two-second gate. The final measurements include the paint ordering and deferred device imports as well. The experiment does not establish package size as the sole cause of startup delay.

An additional splash screen is not needed for the measured final runs. Reconsider it if a reboot cold-start measurement repeatedly exceeds four seconds before the setup window appears; a splash would provide earlier feedback without making device initialization faster.

## Repeat after a Windows restart

Run once before opening FuelLoc, without rebuilding or copying the app first:

```powershell
.\tools\measure_startup.ps1 -ExePath .\dist\FuelLoc\FuelLoc.exe -WindowTitle 'FuelLoc setup' -Runs 1 -MaxSeconds 2 -ReadyUrl 'http://127.0.0.1:54321/'
```

The readiness address must be unused before the run. The script rejects an already running server so it cannot accidentally time another instance. Use `-Runs 3` for repeated process-start measurements. `-MaxSeconds 4` applies the fallback budget.
