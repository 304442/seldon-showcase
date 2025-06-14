---
description: Learn how to implement A/B testing and model experiments in Seldon Core, including traffic splitting, version control, and real-time model switching.
---

# Experiments

An Experiment defines an http traffic split between Models or Pipelines.

Experiments also allow a mirror model or pipeline to be tested where some
percentage of the traffic to the main model is sent to the mirror but the result is not returned.

Further details are given [here](kubernetes/resources/experiment.md).
