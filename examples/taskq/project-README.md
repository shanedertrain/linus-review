# taskq

A small task list CLI. `taskq export` writes the list as CSV (default) or JSON for other tools:

    taskq export > tasks.csv
    taskq export --format json | jq .
