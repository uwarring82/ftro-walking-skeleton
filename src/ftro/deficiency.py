#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Pure predicates shared by FTRO deficiency-ledger views and gates."""


def result_bearing_current_defects(entries):
    """Return the entries that block the Phase-0 convergence condition.

    C12 names one positive class.  Assurance gaps, latent regressions, provider gaps and
    recorded outcomes do not become blocking merely because a new finding type exists.
    """
    return [entry for entry in entries
            if entry.get("disposition") == "open"
            and entry.get("affects") == "changes_result"
            and entry.get("finding_type") == "current_defect"]
