# LeakLens Architecture Contract

## Product loop

LeakLens follows:

1. Observe merchant transaction events.
2. Detect statistically meaningful revenue leakage.
3. Investigate the leakage using auditable data tools.
4. Form a hypothesis rather than claiming unsupported causality.
5. Propose a bounded intervention.
6. Run or simulate an experiment.
7. Measure incremental revenue impact.

## V1 scope

Leak families:

- payment-method degradation
- checkout abandonment
- high-intent customer leakage

V1 actions:

- `PAYMENT_METHOD_EXPERIMENT`
- `RECOVERY_PAYMENT_LINK`
- `DO_NOT_INTERVENE`

## Agent boundary

The LLM will never receive unrestricted database access or arbitrary payment API access. It will call typed analytics tools. Tool outputs are structured evidence. A deterministic policy layer validates proposed interventions before execution.

## Core entities

### Merchant
Represents a merchant whose transaction stream is analyzed.

### Customer
Represents a customer and their historical transaction behavior.

### Transaction
Represents a checkout/payment attempt, including amount, status, payment method, device, timestamp, and failure metadata.

### LeakageFinding
Represents an observed revenue anomaly with measured baseline, affected cohort, estimated revenue at risk, evidence, and confidence.

### Hypothesis
Represents an explanation generated from evidence. Hypotheses are explicitly probabilistic and are not treated as facts.

### Intervention
Represents a bounded action tied to a finding/hypothesis and an expected outcome.

### Experiment
Represents control/treatment allocation and measured incremental lift.

## Reliability requirements

- Idempotent event ingestion.
- Event IDs are unique.
- Duplicate events do not create duplicate analytical records.
- Analytics are reproducible from stored events.
- Interventions have explicit policy constraints.
- Every intervention has an audit record.

## Evaluation principle

Synthetic data will contain known injected leakage patterns. The agent is not told the location of the injected leak. We evaluate detection, evidence quality, intervention choice, recovery/lift, and false interventions against the known ground truth.
