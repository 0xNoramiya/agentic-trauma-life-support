# Spike — Qwen2.5-VL-235B AWQ on a single MI300X

A Day 1 time-boxed experiment. The question: can we serve a 235B-class vision-language model in AWQ on a single MI300X? If yes, the demo upgrades. If no, we revert to the safer 72B BF16 path and report the failure mode in `docs/ROCM_FEEDBACK.md`.

**Outcome: skipped.** Decision recorded below. The 72B BF16 single-MI300X path is the production demo and the pitch is intact (single accessible GPU, full precision, no quantization).

## Hypothesis (the bet, if we'd taken it)

Qwen2.5-VL-235B in AWQ-int4 should fit in ~120-130 GB, leaving ~60 GB headroom on the 192 GB MI300X for KV cache and the multimodal vision tower. We expected TTFT in the 5-10 s range (worse than 72B BF16) but tokens/sec in the same order of magnitude on the AITER + AITER-MHA paths. The dramatic upside: a 235B vision model running on **one** MI300X is a much louder claim than 72B BF16 — H100 (80 GB) and H200 (141 GB) cannot fit either of these workloads in BF16 or AWQ at this scale.

## Sources surveyed (without downloading)

Investigated but did not pull weights for:

- `Qwen/Qwen3-VL-235B-A22B-Instruct` — the official Qwen 235B vision MoE. As of survey date, the official Qwen org does not publish an AWQ variant; only BF16 weights are shipped, which exceed single-MI300X VRAM in dense-equivalent terms.
- `swift/Qwen3-VL-235B-A22B-Instruct-AWQ` — a community AWQ on HuggingFace and ModelScope (per playbook). Did not attempt download.
- `casperhansen/Qwen2.5-VL-72B-Instruct-AWQ` — exists for 72B; the same author has not (yet) shipped a 235B AWQ.

## What we did NOT try (and why)

We chose not to attempt the spike at all. The reasons, in order:

1. **Day 1 bring-up budget already overran.** Roughly 2 hours of the originally-budgeted 4-hour spike window were consumed by an SSH/networking issue: the developer's Indonesian ISP transparently intercepts SSH on port 22 to public DO IPs (host-key MITM), and a Tailscale overlay had to be brought up before the laptop could reach the droplet at all. See `docs/ROCM_FEEDBACK.md` finding #5. Once that path was established, the realistic remaining spike window was ~2 hours — below the playbook's hard cap of 4 hours for "go/no-go," and well below the realistic time needed to download (~150 GB AWQ shards), load, and stress-test a 235B on first run with first-run AITER JIT compilation also in the loop (see `docs/ROCM_FEEDBACK.md` finding #2).

2. **Risk profile is wrong for a 5-day single-developer hackathon.** The downside of a failed spike is consuming the rest of Day 1 and then the morning of Day 2 in error-mode rather than driving the 72B path forward. The upside is a flashier slide — but the 72B BF16 single-MI300X claim is *already* the load-bearing pitch (H100 and H200 cannot fit it; this is the entire AMD-cost-accessibility argument). A 235B headline doesn't make the demo safer or more clinical; it just makes the GPU-memory story bigger, marginally.

3. **Spike failure is a deliverable; an unstarted spike is also a deliverable.** This document, as a write-up of "we considered the bet, time-boxed it, and consciously skipped it," is itself a reasonable artifact for the ROCm feedback / engineering-blog story. It demonstrates the discipline of shipping a working floor over chasing a stretch ceiling.

## Decision

**Revert to BF16 72B.** Reason: time-box already partially consumed by network bring-up; risk-adjusted return on a fresh 235B-AWQ landing within the remaining Day 1 window was negative; the 72B BF16 single-MI300X argument is intact and unique; the engineering blog and ROCm feedback document gain *more* by depth-of-finish on the 72B path than by a cosmetic 235B headline.

If the rest of the hackathon runs ahead of schedule (Day 4 with a comfortable margin), the spike can be revived as a "post-floor" experiment and added to the blog post as a follow-on. `scripts/serve_vllm.sh spike` is intentionally left as a stub for that case.

## Time spent

Roughly 30 minutes total — surveying community AWQ candidates, reasoning about feasibility under the partially-consumed Day 1 budget, and writing this document.
