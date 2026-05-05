# Serving Qwen2.5-VL-72B in full BF16 on a single MI300X for trauma decision support

_TODO: lede paragraph — set up the use case (global trauma triage in resource-limited settings), the model (Qwen2.5-VL-72B), and the punchline (it fits in BF16 on a single MI300X with no quantization, no tensor parallelism, no CPU offload)._

## 1. Why we picked AMD

_TODO: one paragraph on the cost-accessibility argument. 192 GB HBM3 on a single MI300X is the most cost-accessible 192GB-class GPU. H100 (80 GB) and H200 (141 GB) cannot fit Qwen2.5-VL-72B in BF16. B200 can but costs 3-5x. MI325X / MI355X are larger but harder to access. For a global health use case, the cost-accessibility argument is the use case._

## 2. The use case in 60 seconds

_TODO: chest X-ray + dictated vitals -> ATLS primary survey + SBAR handoff. Multilingual (English + Indonesian). Decision support, not diagnosis. Built around the global ATLS protocol from the American College of Surgeons._

## 3. The single-GPU 72B argument

_TODO: do the math. Qwen2.5-VL-72B in BF16 is roughly 144 GB of weights. Add KV cache for `--max-model-len 16384` and `--max-num-seqs 4` and you're at ~170-180 GB. H100 cannot. H200 cannot. MI300X can with margin. Tensor parallelism is the workaround if you have multiple smaller GPUs, but tensor-parallel adds collective overhead and operational complexity. Single GPU is simpler._

## 4. Bring-up: ROCm + vLLM + Qwen2.5-VL-72B

_TODO: walk through the docker invocation in `scripts/serve_vllm.sh prod`. Mention the env vars (VLLM_ROCM_USE_AITER, VLLM_ROCM_USE_AITER_MHA, MIOPEN_FIND_MODE=FAST). Mention the gotchas you hit during bring-up — link to ROCM_FEEDBACK.md for the long version._

## 5. Numbers

_TODO: pull representative TTFT, tokens/sec, and peak VRAM from `docs/BENCHMARKS.md`. Highlight the median and p95 for the three scenarios._

See [`docs/BENCHMARKS.md`](BENCHMARKS.md).

## 6. Drafter / Verifier and clinical safety

_TODO: explain the two-pass structure. Drafter produces a strictly-shaped TriageOutput via vLLM guided JSON. Verifier (same model, different prompt, same image) returns notes + patches. Show one or two examples of what the verifier catches: pneumothorax with laterality "n/a", class III shock with normal BP, etc. Tie this to the case_05 credibility test — the model must NOT invent pathology when the X-ray is normal._

## 7. The 235B-AWQ spike

_TODO: report on the Day 1 stretch experiment (Qwen2.5-VL-235B AWQ on a single MI300X). Whether it loaded, what crashed, the proceed/revert decision. Link to `docs/SPIKE_235B_AWQ.md`._

## 8. What we'd want from AMD next

_TODO: friction summary. Pull the highest-severity items from `docs/ROCM_FEEDBACK.md`._

## 9. Repo and demo

- Repo: TODO link to GitHub
- Live demo: TODO link to HF Space
- Demo video: TODO link
