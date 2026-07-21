# Vision & Roadmap

This diagram shows where the Azure Updates Agent is **today** and where it can go. Status is colour-coded so it's clear what already works versus what's planned.

- 🟢 **Live now** — working in the current pilot
- 🟡 **Next** — near-term, already designed
- ⚪ **Future** — possible direction, not yet started

```mermaid
flowchart TD
    subgraph LIVE["🟢 Live now — working pilot"]
        WL["Our service watchlist"]
        AZ["Microsoft Azure<br/>official release feed"]
        AGENT["Azure Updates Agent<br/>(fetch · scope · verify)"]
        MEM["Remembers what it<br/>already reported"]
        REP["Accurate report<br/>every item linked to Microsoft"]
        WL --> AGENT
        AZ --> AGENT
        AGENT --> MEM
        AGENT --> REP
    end

    subgraph NEXT["🟡 Next — near-term"]
        SCHED["Automatic weekly run<br/>(no manual step)"]
        DELIVER["Delivered to the team"]
        EMAIL["Email"]
        TEAMS["Microsoft Teams"]
        TESTS["Automated tests + CI<br/>(enterprise reliability)"]
        REP --> SCHED
        SCHED --> DELIVER
        DELIVER --> EMAIL
        DELIVER --> TEAMS
    end

    subgraph FUTURE["⚪ Future — possible direction"]
        GCP["Google Cloud<br/>release notes"]
        UNIFIED["Unified multi-cloud<br/>report"]
        AI["Optional plain-language<br/>'what this means for us'<br/>summary (source-cited)"]
        GCP -.-> UNIFIED
        REP -.-> UNIFIED
        REP -.-> AI
    end

    style LIVE fill:#e6f4ea,stroke:#34a853,color:#000
    style NEXT fill:#fef7e0,stroke:#f5a623,color:#000
    style FUTURE fill:#f1f3f4,stroke:#9aa0a6,color:#000

    style WL fill:#e8f0fe,stroke:#4285f4,color:#000
    style AZ fill:#e8f0fe,stroke:#4285f4,color:#000
    style AGENT fill:#fff4e5,stroke:#f5a623,color:#000
    style MEM fill:#ffffff,stroke:#34a853,color:#000
    style REP fill:#e6f4ea,stroke:#34a853,color:#000

    style SCHED fill:#ffffff,stroke:#f5a623,color:#000
    style DELIVER fill:#ffffff,stroke:#f5a623,color:#000
    style EMAIL fill:#ffffff,stroke:#f5a623,color:#000
    style TEAMS fill:#ffffff,stroke:#f5a623,color:#000
    style TESTS fill:#ffffff,stroke:#f5a623,color:#000

    style GCP fill:#ffffff,stroke:#9aa0a6,color:#000,stroke-dasharray: 4 4
    style UNIFIED fill:#ffffff,stroke:#9aa0a6,color:#000,stroke-dasharray: 4 4
    style AI fill:#ffffff,stroke:#9aa0a6,color:#000,stroke-dasharray: 4 4
```

## In words

**Today**, the pilot reliably answers one question: *"What changed in the Azure services we depend on — and can I trust it?"* It does this with no risk of invented information, because every fact links back to Microsoft's official announcement.

**Next**, the same tool runs on a schedule and delivers itself to the team (via email, Microsoft Teams, or both), with an automated test suite backing its reliability — turning a manual check into a hands-off weekly briefing.

**In future**, the identical approach can extend to Google Cloud, giving a single unified view across the clouds we use. An optional plain-language summary layer could add a "what this means for us" note to each update — always grounded in the official source, never replacing the verifiable facts.
