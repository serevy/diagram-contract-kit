# Fictional request triage — specification v1

This is an invented software flow, not a description of Semantic Decision Lab,
a research measurement, or an implementation of a real authorization system.

A request enters a semantic classifier. It emits a typed result including a
category, uncertainty, and an abstain flag. This result is data and cannot
authorize anything. Independent policy rules control a separate deterministic
gate, which consumes the typed result and produces hold, review, or eligible.
Eligible means a simulated next-step candidate, never a real dispatch.

The policy gate blocks every candidate when policy is closed. With policy open,
abstain leads to hold, uncertainty leads to review, and a supported category
may be eligible. No numeric probabilities or calibrated thresholds are claimed.
A common API shape does not establish semantic equivalence across providers.

The diagram must show labelled software boxes, directed arrows, and visibly
separate semantic and deterministic boundaries. No hardware metaphor is needed.
English and Japanese labels describe the same entity and edge identifiers.
