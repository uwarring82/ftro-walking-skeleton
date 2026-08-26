#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Render ledgers/deficiency-log.json to Markdown.
# Task card section 3: "Human and machine views share one source of truth."
# The Markdown is generated, never hand-edited.

import collections
import json

d = json.load(open("ledgers/deficiency-log.json", encoding="utf-8"))
e = d["entries"]
L = []
w = L.append

w(f"# {d['ledger']}\n")
w("> **Generated file — do not edit.** Source of truth is "
  "[`deficiency-log.json`](deficiency-log.json); regenerate with "
  "`python3 src/ftro/render_deficiencies.py`.\n")
w(f"**Version:** {d['version']}  ")
w(f"**Opened:** {d['opened']}  ")
w(f"**Phase:** {d['phase']}  ")
w(f"**Task card:** {d['card']}\n")

w("## Summary\n")
for label, key in (("Class", "class"), ("Severity", "severity"), ("Domain", "domain"),
                   ("Disposition", "disposition"), ("Responsible party", "responsible_party"),
                   ("Finding type", "finding_type"), ("Affects", "affects")):
    c = collections.Counter(x[key] for x in e)
    w(f"**By {label.lower()}:** " + ", ".join(f"{k} ({v})" for k, v in sorted(c.items())) + "  ")
sd = [x["id"] for x in e if x.get("self_directed")]
w(f"\n**Total entries:** {len(e)} · **self-directed:** {len(sd)}\n")
blocking = [x for x in e if x["disposition"] == "open" and x.get("affects") == "changes_result"
            and x.get("finding_type") not in ("external_evidence_gap", "recorded_outcome")]
w("> **Convergence measure.** An append-only count can only rise, so totals cannot show "
  "progress. The measure is: **open entries that could change the Phase-0 result and are "
  "not external evidence gaps.**\n>\n"
  f"> Currently: **{len(blocking)}**"
  + (" — " + ", ".join(f"`{x['id']}`" for x in blocking) if blocking else
     " — the remaining result-bearing entries are provider evidence gaps and the "
     "recorded null itself, which are the deliverable rather than software failures.") + "\n")

w("| ID | Class | Sev. | Type | Affects | Party | Title |")
w("| --- | --- | --- | --- | --- | --- | --- |")
order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
for x in sorted(e, key=lambda y: (order.get(y["severity"], 9), y["id"])):
    party = "**self**" if x.get("self_directed") else x.get("responsible_party", "provider")
    w(f"| [`{x['id']}`](#{x['id'].lower()}) | {x['class']} | {x['severity']} "
      f"| {x.get('finding_type', '-')} | {x.get('affects', '-')} | {party} | {x['title']} |")
w("")

w("## Entries\n")
for x in e:
    w(f"### {x['id']}\n")
    w(f"**{x['title']}**\n")
    w(f"| Field | Value |")
    w(f"| --- | --- |")
    w(f"| Class | `{x['class']}` |")
    w(f"| Severity | {x['severity']} |")
    w(f"| Domain | {x['domain']} |")
    w(f"| Dataset | `{x['dataset']}` |")
    w(f"| Disposition | `{x['disposition']}` |")
    w(f"| Finding type | `{x.get('finding_type', '-')}` |")
    w(f"| Affects | `{x.get('affects', '-')}` |")
    w(f"| Responsible party | `{x.get('responsible_party', 'provider')}`"
      f"{' — **self-directed**' if x.get('self_directed') else ''} |")
    w(f"| Version | {x['version']} |")
    w("")
    w(f"**Failed step.** {x['failed_step']}\n")
    w(f"**Known fact or required evidence.** {x['known_fact']}\n")
    w(f"**Observed.** {x['observed']}\n")
    w("**Evidence.**\n")
    for ev in x["evidence"]:
        w(f"- `{ev}`")
    w("")
    w(f"**Impact.** {x['impact']}\n")
    w(f"**Workaround.** {x['workaround']}\n")
    w(f"**Proposed response.** {x['proposed_response']}\n")
    w("---\n")

open("ledgers/deficiency-log.md", "w", encoding="utf-8").write("\n".join(L))
print(f"wrote ledgers/deficiency-log.md ({len(e)} entries)")
