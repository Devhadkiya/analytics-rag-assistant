# Reporting conventions

## Timezone
All daily reports are built in **Europe/Berlin** local time. Events are stored
in UTC and converted at query time. A day runs 00:00–23:59:59 Europe/Berlin,
which means two days a year are 23 or 25 hours long.

## Date grain
Weekly reporting uses ISO weeks, starting Monday. Monthly reporting uses
calendar months. Do not mix ISO weeks with calendar months in the same chart.

## Restatements
Figures older than 90 days are frozen. If a correction is needed after that,
it is published as a restatement note alongside the metric rather than by
silently changing the historical value.
