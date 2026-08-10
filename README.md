# Event Platform

Event Platform is a lightweight framework for monitoring changing data from external platforms and notifying subscribers when relevant changes occur.

Golf is the first use case, but the core architecture is designed to remain independent of golf-specific logic.

## Current Status

**Current production release: v1.1.0**

The platform has been verified in real-world operation with both live event monitoring and daily monitoring.

## Current Connectors

### GolfBox Leaderboard

`connectors/golfbox_leaderboard.py`

Monitors live GolfBox competition leaderboards.

Verified with:

- Haninge Golfklubb
- Strängnäs Golfklubb
- Hole-by-hole live scoring
- Position changes
- Multi-round tournaments
- Transition between rounds
- Completed tournament results

### SGF Ranking

`connectors/sgf_ranking.py`

Monitors Swedish Golf Federation ranking data.

Verified with daily monitoring and real ranking changes following completed competitions.

## Architecture

High-level flow:

```text
External data source
        ↓
     Connector
        ↓
    watcher.py
        ↓
    state.json
        ↓
 Change detection
        ↓
       ntfy
        ↓
Subscriber devices
