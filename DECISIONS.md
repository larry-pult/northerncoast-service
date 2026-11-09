# Implementation decisions and evaluation

## Candidate-directed design

- Use OpenAI because it is the available credential; default to `gpt-6-luna`
  for inexpensive, bounded classification. The credential was verified with a
  minimal structured-output request before the live evaluations.
- Keep one zero-shot assessment call. The candidate preferred this over the
  assistant's initial proposal to extract signals and score deterministically.
  Pydantic/SDK Structured Outputs remove the need for a separate parsing layer.
- After reviewing the numeric output requirement, adopt a 35/25/20/20 rubric
  for volume, credibility, product fit, and readiness. These are provisional
  business priorities, not weights learned from conversion data. The model
  applies them; Python validates the output instead of calculating the score.
- Keep license evidence soft and self-reported. Missing confirmation does not
  establish inability to import. Claims of an active license are not verification.
- Treat routing as a next action. The brief's Warm/KAM output conflicts with its
  simpler prose mapping; preserve the example by allowing actionable Warm leads
  to reach a KAM.
- Configure a ten-second elapsed deadline, expandable to 25 seconds, and no
  retries. The SDK's defaults were confirmed to be a 600-second timeout and two
  retries; neither fits this endpoint's budget. `asyncio.timeout` bounds the
  complete model operation, including parsing, rather than relying only on
  transport inactivity timeouts.
- Keep authentication and application rate limiting outside this take-home.
  Reject malformed input; report provider failures instead of inventing scores.

## What evaluation changed

The nine synthetic cases were written before the implementation and stored with
proposed labels for candidate review. Four brief examples are separate fixtures.
Neither dataset is inserted into the scorer prompt.

The first live run matched 11/13 expected tiers and all routing labels. Both
mistakes rated licensed, moderate-volume importers Hot rather than Warm, including
the brief's output example. General point anchors were added for approximately
one FCL/month and limited operating evidence; no lead IDs or case-specific
exceptions were introduced.

A subsequent run underscored missing-readiness information as if it were an
explicit blocker, moving the brief's Hot lead to Warm. Readiness calibration now
treats unknown information neutrally, while explicit blockers count against it.
The candidate suggested few-shot prompting if needed; the final scorer remains
zero-shot because the clarified rubric passed these cases.

The optional judge initially produced false positives because it lacked business
context and score bands. It now receives the actual qualification policy and
reviews factual grounding and whether the rationale supports the tier/action.
Numeric consistency is checked in code. This illustrates why a second LLM's
verdict needs investigation rather than automatic acceptance as truth.

## Verified results and limits

- 46 offline tests pass, covering schema boundaries, malformed JSON, configuration,
  ID preservation, safe provider errors, refusal/incomplete outputs, and deadline
  cancellation. Offline tests do not need a credential.
- Final live run: all 13 cases matched expected tiers and acceptable routing;
  all 13 rationale judgments passed. Scoring latency was 1.77–4.25 seconds
  (mean 3.05 seconds), excluding judge execution and app initialization.
- A separate Uvicorn/localhost HTTP smoke test completed successfully in
  2.34 seconds. This is not a hosted Vercel test.
- The [raw final report](test/eval/results.json) records each output, latency,
  judgment, model, and scorer prompt hash. Scores are deliberately not asserted
  to equal a particular integer within a tier.

These cases were used during calibration. They are a small regression set, not
an unseen benchmark or a calibrated estimate of real-world accuracy. The
default judge uses the same model as the scorer, so shared errors remain
possible. Future work should use human-reviewed held-out leads, repeated runs,
and model comparisons before making stronger reliability claims.

GitHub pushing, Vercel deployment, public-URL verification, and the candidate's
actual time-spent report remain manual delivery steps.

References: [OpenAI model](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[SDK timeout/retry behavior](https://developers.openai.com/api/reference/python).
