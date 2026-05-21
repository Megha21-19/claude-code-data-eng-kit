---
name: prompt-eval
description: Build, run, or update an evaluation harness for an LLM prompt / agent / chain used in this codebase. Use when the user asks to evaluate a prompt, score outputs, run evals, compare models, check for regression, A/B a prompt change, or build a golden dataset.
---

# prompt-eval

Use this skill when the user is working on an LLM feature and wants to evaluate
its quality, not just ship a prompt change.

## When to invoke

Trigger phrases: "eval this prompt", "score the outputs", "regression test for
the prompt", "compare models on X", "build a golden set for Y", "A/B test the
prompt".

## The pattern this kit uses

```
src/llm/
  features/<feature_name>/
    prompt.py             # the prompt under test
    runner.py             # invokes the LLM
    eval.py               # scoring functions
evals/
  <feature_name>/
    golden.jsonl          # fixed inputs + expected outputs
    run.py                # ties prompt + golden + scoring
    results/              # gitignored, run outputs land here
```

A run produces a `results/<run_id>.json` with per-example scores and aggregates.

## Steps

1. **Identify the feature.** A prompt with no obvious feature boundary is a
   smell — push back and ask what task it serves.
2. **Locate or create the golden set** at `evals/<feature>/golden.jsonl`.
   Each row: `{"input": ..., "expected": ..., "tags": [...]}`. Tags let us
   slice results (e.g. by document type, language).
3. **Choose scoring functions**. Composable, in `src/llm/features/<feature>/eval.py`:
   - Exact match (for structured outputs).
   - Field-level equality (for JSON).
   - LLM-as-judge with a rubric (for free-form). Document the judge prompt.
   - Latency and cost as separate metrics, not pass/fail.
4. **Run the eval**:
   ```bash
   python -m evals.<feature>.run --golden evals/<feature>/golden.jsonl
   ```
5. **Compare against baseline**. The runner writes `results/<run_id>.json`
   and prints a diff against the latest tagged baseline.
6. **Surface cost**. Every eval run reports total tokens in, tokens out,
   USD estimate (using checked-in pricing in `evals/pricing.yml`).

## What not to do

- Don't eval on the same examples the prompt was tuned on. Hold out at
  minimum 20% as a true test set.
- Don't ship a prompt change without a passing eval diff.
- Don't use LLM-as-judge for tasks where exact match works. It's slower,
  more expensive, and adds variance.
- Don't conflate "the eval passed" with "the feature is good." Eval scores
  are a floor, not a ceiling.
