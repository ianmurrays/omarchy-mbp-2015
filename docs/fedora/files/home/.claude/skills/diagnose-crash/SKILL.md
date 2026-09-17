---
name: diagnose-crash
description: >
  Find why a program crashed on this Fedora machine, from a systemd-coredump core dump.
  Use when a process segfaulted, aborted, or dumped core, when the user asks why an
  application crashed or closed, or when the user clicks "Diagnose with Claude" on a
  crash notification. Triggers: crash, segfault, SIGSEGV, SIGABRT, core dump,
  coredumpctl, "why did X crash", "X keeps crashing", backtrace.
---

# Diagnose a crash

A port of the Omarchy `diagnose-crash` skill to Fedora 44. The `omadora-crash-watch`
user service sends the PID, the program name, the executable, and the signal.

Do not change the system. Do not delete core dumps. Do not report a bug unless the user
agrees.

## Procedure

1. Get the facts of the crash:
   ```
   coredumpctl info <pid>
   ```
   Record the command line, the signal, the time, and the package of the executable.
2. Find out if the crash is a one-time event or a pattern:
   ```
   coredumpctl list <program> --no-pager
   ```
3. Make sure that the kernel did not stop the process for low memory:
   ```
   journalctl -k --since "<crash time - 5 min>" --until "<crash time>" | grep -i -E 'oom|killed process'
   free -h
   ```
4. Find the package and the recent updates:
   ```
   rpm -qf <exe>
   dnf history list --reverse | tail -20
   ```
   Compare the crash time with the update times.
5. Get the backtrace of all threads. `DEBUGINFOD_URLS` is set to
   `https://debuginfod.fedoraproject.org/`, so gdb downloads the debug symbols:
   ```
   coredumpctl debug <pid> --debugger-arguments="-batch -ex 'thread apply all bt'"
   ```
   The first run can take several minutes.
6. Read the stack of each thread. Record third-party code in the process: plugins,
   `LD_PRELOAD` libraries, and proprietary drivers.
7. ABRT also records crashes on this machine. Compare with its data:
   ```
   abrt list
   ```
8. Read the journal of the program for the minutes before the crash:
   ```
   journalctl --user --since "<crash time - 5 min>" --until "<crash time>"
   ```

## Report

Give the user:

- What crashed: the program, the version, the signal, and the time.
- The mechanism. Keep the facts from the backtrace apart from your inferences.
- If the crash occurs again, and how frequently.
- If data is possibly lost.
- The next step: an update, a workaround, or a bug report.

Do not write a function name that is not in the backtrace.

## Rules

- This machine has hardware problems that other machines do not have. Before you blame
  the GPU, read `~/src/omadora/docs/electron-glitch.md` and
  `~/src/omadora/docs/gpu-kernel-args.md`.
- To stop notifications for one program, the user can disable crash capture from the
  Omadora menu (Trigger > Toggle > Crash Capture). Tell the user about this option. Do not
  do it.
- A bug report goes to Fedora (`https://bugzilla.redhat.com`, or `abrt report <id>`) or
  to the upstream project. Search for a known issue first. Ask the user before you file.
