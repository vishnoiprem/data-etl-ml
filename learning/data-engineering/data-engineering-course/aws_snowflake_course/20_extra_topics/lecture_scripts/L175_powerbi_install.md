---
l_id: L175
title: Download & install Power BI
duration: "4:30"
prereqs: ["L174"]
---

# L175 — Download & install Power BI

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 6. BI Tools
> **Duration:** 4:30

## Prereqs

L174 — Data Visualization (Power BI/Tableau). High-level
concepts only; today is the install.

## Key terms

- **Power BI Desktop** — the free, Windows-only desktop
  application for authoring dashboards.
- **Power BI Service** — the cloud-hosted platform for
  publishing and sharing dashboards.
- **Power BI Report Server** — the on-premises variant for
  organizations that can't use the cloud service.

## Lecture

Welcome back. Today's lecture is the install of **Power BI
Desktop**, Microsoft's free authoring tool. By the end of
this lecture you should have Power BI Desktop running on
your machine, ready to connect to Snowflake.

### The install

1. Go to `https://powerbi.microsoft.com/desktop/`.
2. Click **Download free**. (You'll need a Microsoft
   account; sign in or create one.)
3. Run the installer. The default options are fine.
4. Launch Power BI Desktop. Sign in with the same
   Microsoft account.

The install is Windows-only. On macOS, your options are:

- Use a Windows VM (Parallels, VirtualBox).
- Use Power BI Service in a browser (no local authoring).
- Skip Power BI and use Tableau instead (L178).

### What's in the install

Power BI Desktop is a single application with three
panels:

- **Data** pane (left) — tables and fields.
- **Canvas** (center) — where you build visuals.
- **Visualizations** pane (right) — chart types and
  formatting.

The bottom of the canvas has the "Get Data" button — that's
where we'll add the Snowflake connection in L176.

### The version

Power BI Desktop updates monthly. The "Get Data" experience
is stable, but new features appear in newer versions. If you
hit a connector issue, the first thing to try is updating
to the latest version.

### A free vs paid

- **Free**: Power BI Desktop, all authoring features,
  publish to "My workspace" in Power BI Service (1 GB
  storage).
- **Pro**: publish to other workspaces, share dashboards,
  schedule refreshes ($10/user/month).
- **Premium per user**: same as Pro with higher storage and
  more frequent refresh.

For personal use, free is enough. For sharing dashboards
across a team, Pro is required.

### The "publish" workflow

```text
author in Power BI Desktop → publish to Power BI Service → share with team
```

We'll cover the publish step after we connect to Snowflake
in L176.

## Hands-on

1. Download Power BI Desktop from
   `https://powerbi.microsoft.com/desktop/`.
2. Install with default options.
3. Launch and sign in.

If you're on macOS, install a Windows VM or use Power BI
Service in a browser; the rest of this sub-group assumes
Power BI Desktop on Windows.

## Key takeaways

- Power BI Desktop is free, Windows-only.
- Three panels: data, canvas, visualizations.
- Pro is required for sharing dashboards across a team.
- The next lecture connects it to Snowflake.

## What's next

L176 — Connect Power BI & Snowflake. The actual connection.