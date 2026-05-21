# Session Summary: Charger Fault Detection Pipeline

## Purpose

This session refactored the project into a more coherent machine learning pipeline for electric car charger fault detection. The goal was to make the system better match the real problem context:

- detect electrical faults in charger telemetry
- use machine learning, not only hand-written anomaly rules
- evaluate the model in a more realistic way
- present useful metrics and visualizations in the simulator UI

The final result is a clearer separation between:

- synthetic data generation for training and benchmarking
- unlabeled synthetic inference data for deployment-style scoring
- a supervised Random Forest model for fault detection
- a web UI that shows evaluation metrics and anomaly summaries

---

## What Was Changed

### 1. Replaced the original Isolation Forest approach

The original pipeline relied on `IsolationForest`, which is an unsupervised outlier detector. That approach was not a good semantic fit for the project because the objective is not simply to detect statistical outliers, but to identify electrical faults such as:

- voltage out of range
- phase imbalance
- current imbalance
- power mismatch

These faults are domain-specific and may not be isolated points in feature space. For that reason, the model was replaced with a **Random Forest classifier** trained on labeled synthetic examples.

### 2. Added optional labels to the generator

The synthetic generator in [data/generator.py](data/generator.py) was updated so that `is_anomaly` and `anomaly_type` can be optionally included or omitted during data generation.

This matters because:

- training data can be labeled
- inference data can remain unlabeled
- the same generator can support both development and deployment-style usage

This was important for keeping the simulator realistic, since the unlabeled inference dataset is what a real system would receive.

### 3. Added a benchmark-oriented generator

A new file was created: [data/generator_testing.py](data/generator_testing.py)

This module creates a more realistic benchmark setup than the base generator. It introduces several evaluation improvements:

- **charger ID holdout**: training and inference are derived from a shared base dataset, then split into disjoint charger groups
- **anomaly type holdout**: training and inference do not see the same fault families
- **subtler faults**: some anomalies are closer to decision boundaries
- **sensor noise**: voltage/current/power values are perturbed
- **missingness**: some telemetry values are dropped
- **different random seed** for inference data

This makes the evaluation less optimistic and more aligned with real-world generalization.

The benchmark generator now also accepts the anomaly-rate value from the simulator UI, so the injected fault frequency can be changed from the webapp and propagated into the synthetic benchmark.

### 4. Split training and inference datasets in the simulator

[webapp/simulator.py](webapp/simulator.py) was updated so the pipeline now generates two datasets:

- a labeled training dataset
- an unlabeled inference dataset

The training set is used to fit the model. The inference set is then scored independently.

The simulator also saves them separately as Excel files:

- [data/all_chargers_training_labeled.xlsx](data/all_chargers_training_labeled.xlsx)
- [data/all_chargers_pivoted.xlsx](data/all_chargers_pivoted.xlsx)

That makes it explicit that the inference dataset does not contain labels.

The simulator now also logs the requested benchmark split, the train/inference charger sets, and whether labels are present. This improves auditability when reviewing runs.

### 5. Added feature engineering for the Random Forest

The model no longer uses only raw telemetry values. It now also computes engineered features such as:

- voltage differences between phases
- current differences between phases
- power gap between offered and actual import
- calculated power from voltage × current
- absolute power mismatch
- voltage availability indicator

These features are better aligned with the actual fault logic and help the model learn the relevant patterns.

### 6. Improved model evaluation

The simulator now reports more useful evaluation metrics than a score histogram. The results include:

- Accuracy
- Precision
- Recall
- F1 score
- ROC AUC
- PR AUC
- Balanced accuracy
- Matthews correlation coefficient
- selected decision threshold
- confusion matrix
- feature importance ranking

The model threshold is chosen by sweeping candidate thresholds on the labeled validation split and selecting the one with the best F1 score.

### 7. Removed the old score distribution view

The previous “score distribution” output was not very informative for this use case. It was removed and replaced with more interpretable outputs:

- confusion matrix
- threshold selection summary
- feature importance bars
- anomaly count by charger

### 8. Updated the UI labels

The UI in [webapp/templates/index.html](webapp/templates/index.html) was updated so it no longer refers to Isolation Forest. It now presents the model as a Random Forest-based fault detection pipeline.

---

## Why These Changes Make More Sense

### The model now matches the problem definition

The project objective is to develop a machine learning model to detect charger electrical faults. That is not the same as generic anomaly detection.

A Random Forest trained on labeled examples is more appropriate than an unsupervised outlier detector because:

- the faults are domain-defined
- the generator can create labeled examples
- the faults are not always extreme statistical outliers
- the model can learn fault patterns directly

### The evaluation is now more honest

Earlier evaluation was overly optimistic because the model and test data were too closely aligned with the generator. The new benchmark generator makes the task harder by:

- using held-out charger IDs
- using held-out anomaly types
- adding noise and missingness
- making some faults subtler

This gives a better estimate of how the model behaves on unseen data.

### The inference dataset now looks like real deployment data

The unlabeled inference dataset is closer to what the simulator would see in production:

- no anomaly labels
- no ground truth columns
- only sensor and telemetry values

That is important because the model should predict faults from features only, not from labels present in the data.

---

## Important Caveats

### The metrics are still synthetic

Even though the benchmark is more realistic, it is still synthetic. The reported scores should be interpreted as:

- proof of concept
- best-case benchmark for the synthetic generator
- not a guarantee of real-world deployment performance

### The generator defines the fault space

The model learns the patterns produced by the generator. If the real world contains fault types that are not represented in the synthetic process, performance will likely drop.

### The benchmark is intentionally harder

The benchmark generator was designed to better test generalization. That means scores may be lower than before, but they are more meaningful.

This also explains why the anomaly injection rate in the UI does not directly translate into the model's detection rate. The anomaly-rate slider controls how many faults are injected into the synthetic data, but the model's detection rate depends on the learned threshold, the held-out chargers, the held-out anomaly families, and the added noise/missingness.

In other words:

- anomaly rate = data generation setting
- detection rate = model output on the inference set
- accuracy/precision/recall = evaluation against hidden benchmark labels

Because the benchmark is intentionally harder, a higher injected anomaly rate does not guarantee a proportionally higher detection rate.

---

## Final Architecture After the Refactor

### Training flow

1. Generate labeled synthetic training data
2. Engineer features
3. Train a Random Forest classifier
4. Tune the decision threshold on the validation split
5. Report performance metrics

### Inference flow

1. Generate unlabeled synthetic inference data
2. Apply the trained model
3. Produce anomaly predictions and probabilities
4. Summarize results per charger
5. Display results in the simulator UI

---

## Files Added

- [data/generator_testing.py](data/generator_testing.py)
- [session_changes.md](session_changes.md)

## Files Updated

- [data/generator.py](data/generator.py)
- [webapp/simulator.py](webapp/simulator.py)
- [webapp/templates/index.html](webapp/templates/index.html)

---

## Bottom Line

The session moved the project from a generic anomaly-detection setup to a more defensible **supervised machine learning fault-detection system**.

The result is more coherent with the real problem because:

- the model is trained on labeled examples
- the labels are optional and not present in inference data
- the benchmark is more realistic
- the UI now presents meaningful metrics and explanations
- the pipeline better reflects how a charger fault detection system would actually work
