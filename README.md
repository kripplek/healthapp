# HealthApp

Replacement for New Relic's deprecated server health monitoring solution. MIT licensed.

Three components:

## API Server

- stateless falcon app
- listens for updates from server agents
- provides api access to list servers and alerts
- provides web UI (a single page app) which pulls from the API endpoints
  and displays them nicely

## Alert Processor

- stateful service. only run one of these at once (until i add leader election)
- periodically poll redis for the latest server statuses, and intelligently
  create, maintain, and close alerts as events change
- handles notifications (currently email based) for alert state transitions

## Agent

- run this on each server that needs to be monitored
