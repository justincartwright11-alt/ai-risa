# Changelog

## v1.1-ops-visibility
- added latest-run failure detection based on canonical run history and stage summaries
- added daily health summary artifacts in JSON and Markdown
- added scheduler wrappers for ops visibility jobs
- no core pipeline behavior changes

## v1.1-ops-visibility-slice-2
- added shared read-only aggregation module for daily, weekly, and operator summary artifacts
- added weekly health rollup artifacts in JSON and Markdown
- added lightweight operator summary artifacts in JSON and Markdown
- added weekly rollup scheduler wrapper and task registration
- updated daily/weekly wrappers to refresh operator summary artifact
- no core pipeline behavior changes
