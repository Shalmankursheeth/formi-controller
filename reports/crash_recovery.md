# Crash-recovery evidence

Scenario `public_02_incidents`, controller killed with TerminateProcess 5 times.

- kill #1 at sim ts 2027-01-06T01:00:00+05:30 (target minute 2231)
- kill #2 at sim ts 2027-01-07T09:00:00+05:30 (target minute 3911)
- kill #3 at sim ts 2027-01-08T18:00:00+05:30 (target minute 6745)
- kill #4 at sim ts 2027-01-09T12:00:00+05:30 (target minute 7908)
- kill #5 at sim ts 2027-01-12T16:00:00+05:30 (target minute 12104)
- final run: done in 1.3s {'scenario': 'public_02_incidents', 'sim_minute': 14400, 'ts': '2027-01-14T00:00:00+05:30', 'end_minute': 14400, 'finished': True, 'tick_minutes': 15, 'credits_remaining': 195.0, 'chunks'

Approvals by final status (sim): {'applied': 8}
Recovered 'submitting' proposals: 0
Stale-base apply conflicts: 0

| check | result |
|---|---|
| scenario finished | PASS |
| no approval left pending/approved-unapplied | PASS |
| no approval applied twice | PASS |
| no open proposals in our store | PASS |
| event cursor reached last chunk | PASS |