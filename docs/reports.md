# Reports

Watchtower stores every executed command, tool output, and confirmed finding in a local SQLite file, `pentest_memory.db`. Each scan is recorded as a separate run, and its run id is logged when the scan starts.

## Export a PDF

Export the findings of the most recent run without re-running the scan:

```bash
python -m watchtower.main --report "pentest_report.pdf"
```

To report on an earlier run, pass its id:

```bash
python -m watchtower.main --report "pentest_report.pdf" --run 20261113-224923-f666dd
```

The report includes an executive summary with the run's target and start time, then each finding with its severity, description, and evidence.

<div align="center">
  <img width="792" alt="Example PDF report" src="https://github.com/user-attachments/assets/7264ec48-b48f-4419-8f44-5cc7ab821aaa">
</div>

!!! note
    Databases created by versions before run scoping still work: the columns are added on first use, and older rows stay readable.
