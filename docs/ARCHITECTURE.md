# Architecture

## High-level diagram

```
                     +-------------------+
  chest x-ray ---->  |                   |
                     |   Drafter call    | --> raw JSON
  vitals text  ---->  |  (Qwen2.5-VL-72B  |     (TriageOutput, guided)
                     |   guided JSON)    |
                     +---------+---------+
                               |
        retrieval              v                 same vLLM server
        (FAISS over    +---------------+         on a single MI300X
         ATLS / EAST   |  TriageOutput |
         / WHO /       +-------+-------+
         StatPearls)           |
            ^                  v
            |          +---------------+
        same query     |  Verifier call|
        text used      |  (notes +     |
        for retrieval  |   patches)    |
                       +-------+-------+
                               |
                               v
                       +---------------+
                       |   Renderer    | --> SBAR markdown (EN or ID)
                       +---------------+
```

## Stages

1. **Retrieval.** The dictated vitals/vignette are embedded with `BAAI/bge-m3` and the top-5 chunks from the FAISS-CPU index are pulled. The corpus is built from open or freely-licensed trauma guidelines (ACS TQIP, EAST PMG, WHO IMEESC, StatPearls). Retrieval is best-effort: if the index does not exist the pipeline still runs.

2. **Drafter.** Qwen2.5-VL-72B-Instruct is called with a system prompt that pins it to the ATLS primary survey (ABCDE), the chest X-ray as an image content block, the vitals text, and the retrieved excerpts (each with a citation_id). vLLM's `guided_json` extension constrains decoding to the `TriageOutput` schema. One retry on validation failure.

3. **Verifier.** The same model is called with a clinical-safety-reviewer prompt, the original X-ray, and the drafter's JSON. It returns `{verifier_notes, patches}`. Patches are applied to a deep copy of the draft via a small in-file path-walker (no jsonpatch dep). Verifier failure is non-fatal — we log and use the unverified draft.

4. **Renderer.** The validated `TriageOutput` is rendered to an SBAR-style markdown handoff. There are two renderers, one English and one Indonesian. They share the same data shape; only headers and labels are translated. Enum values stay in English so the schema continues to validate.

## Why this shape

- **ABCDE primary survey.** The Advanced Trauma Life Support protocol is the global standard for the first sixty seconds at a trauma. Mapping the model's output directly onto ABCDE makes the schema legible to any trauma clinician on the planet, which is the point of the use case (resource-limited deployment).
- **Drafter / Verifier split.** A single model pass can produce a confident-sounding output that contains an internal contradiction (e.g. claiming class III shock with a normal blood pressure). The verifier exists to catch exactly those patterns and patch them. Both calls share the same vLLM server, so the cost of the second call is small.
- **Guided JSON.** vLLM's `guided_json` extension constrains decoding to the schema, which removes the entire class of "model returned JSON-shaped text that doesn't validate" failures. The Pydantic model is the contract.
- **FAISS over CPU.** The corpus is small (a few thousand chunks). CPU FAISS is more than fast enough and keeps the GPU free for the model.
- **Multilingual.** `bge-m3` is a strong multilingual embedder and Qwen2.5-VL has good Indonesian. Bahasa Indonesia is a credible second language for a global trauma tool: Indonesia has 280M people and high road-trauma incidence. Adding it costs us only a system prompt and a renderer.

## Single-MI300X constraint

The model runs on **one MI300X**. Qwen2.5-VL-72B-Instruct in BF16 is roughly 144 GB of weights; with 192 GB HBM3 we have ~48 GB headroom for KV cache. We do not use tensor parallelism (`--tensor-parallel-size > 1`) — the entire pitch is single-GPU 72B BF16 on the most cost-accessible 192GB-class GPU.
