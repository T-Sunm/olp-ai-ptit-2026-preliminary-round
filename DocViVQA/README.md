# DocViVQA

Workspace for the TACVU2 visual document question-answering task.

## Project structure

- `notebooks/`: dataset exploration, training, and submission generation.
- `scripts/`: command-line tools for evaluating predictions.
- `data/`: local training, public test, and private test data.
- `artifacts/models/`: model checkpoints.
- `artifacts/analysis/`: samples and analysis results.
- `outputs/`: predictions and submission archives.

Run local notebooks with `DocViVQA/notebooks` as the working directory. The Colab notebook uses the root working directory of the Colab runtime.

## Pipeline

1. `notebooks/explore_dataset.ipynb`: explore the dataset and reasoning types.
2. `notebooks/train_bold_pair_local.ipynb`: train the visual-bold model locally.
3. `notebooks/train_bold_pair_colab.ipynb`: train the same model in Colab instead.
4. `notebooks/submission_pipeline.ipynb`: generate predictions and package a submission.
5. `scripts/evaluate_predictions.py`: evaluate predictions when labels are available.

`notebooks/baseline.ipynb` is retained as a reference baseline and is not part of the main pipeline.

```text
data/ -> notebooks/ -> artifacts/models/
                    -> outputs/
```

The two training notebooks target different environments; run only the one you need.
