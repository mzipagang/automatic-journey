# Logging
For logging, we use the SRE Team's [e451 FastAPI Monitoring Package](https://github.com/8451LLC/e451-monitoring-fastapi).
We have provided a basic example of setup and usage in [main.py](../app/main.py).

Additional documentation can be found on its GitHub page.

This template outputs its logs in JSON format, which are then sent to LAWS.

You can view the logs by going to the respective Kubernetes Service in Azure Portal, clicking "Logs" on the sidebar,
and entering a query.

Example Query:
```
let startTimestamp = ago(4h);
KubePodInventory
| where TimeGenerated > startTimestamp
| where Name startswith "fastapi-template-test"
| project ContainerID, PodName=Name
| distinct ContainerID, PodName
| join
(
ContainerLog
| where TimeGenerated > startTimestamp
)
on ContainerID
// Parse JSON logs and filter based on log level
| extend replaced = replace(@"[\\]", @"", LogEntry)
| extend parsedLogs = parse_json(extract("{(.*):[^{}]*}", 0, replaced))
| where parsedLogs.level == "info" or parsedLogs.level == "warning" // debug,info,warning,error
| project TimeGenerated, PodName, LogEntry, LogEntrySource
| order by TimeGenerated desc
```
This query finds logs from any pods that begin with "fastapi-template-test" from within the past 4 hours.
It then filters those logs based on the log level and provides an output. The message can be viewed by clicking on the 
desired log and then the LogEntry.

More documentation on Azure Log Queries can be found [here](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-query-overview).