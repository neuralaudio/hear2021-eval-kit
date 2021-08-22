#!/usr/bin/env python3
"""
Runs evaluation on the test predictions for predictions on a HEAR task.
"""

import json
import pickle
from pathlib import Path
from typing import Collection, Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

from heareval.score import available_scores, label_vocab_as_dict


def get_scene_based_prediction_files(task_path: Path) -> Tuple[np.ndarray, List]:
    # Predictions are currently torch tensors -- should we convert to np arrays before
    # pickling?
    predictions = pickle.load(
        task_path.joinpath("test.predicted-labels.pkl").open("rb")
    )
    if isinstance(predictions, torch.Tensor):
        predictions = predictions.detach().numpy()
    elif isinstance(predictions, np.ndarray):
        pass
    else:
        raise TypeError(
            "Expected predictions to be a numpy array or a torch tensor. "
            f"Received: {type(predictions)}."
        )

    targets = pickle.load(task_path.joinpath("test.target-labels.pkl").open("rb"))

    # What other types could we receive as targets?
    assert isinstance(targets, list)

    # Make sure we have the same number of predictions as targets
    assert len(predictions) == len(targets)

    return predictions, targets


def get_event_based_prediction_files(task_path: Path) -> Tuple[Dict, Dict]:
    # For event based embeddings we load JSON files of the labeled sound events
    predictions = json.load(task_path.joinpath("test.predictions.json").open())
    targets = json.load(task_path.joinpath("test.json").open())
    assert isinstance(predictions, dict)
    assert isinstance(targets, dict)
    for filename in predictions:
        assert filename in targets

    return predictions, targets


def task_evaluation(task_path: Path):

    metadata = json.load(task_path.joinpath("task_metadata.json").open())
    label_vocab = pd.read_csv(task_path.joinpath("labelvocabulary.csv"))

    if "evaluation" not in metadata:
        print(f"Task {task_path.name} has no evaluation config.")
        return

    embedding_type = metadata["embedding_type"]
    predictions: Collection = []
    targets: Collection = []
    if embedding_type == "scene":
        predictions, targets = get_scene_based_prediction_files(task_path)
    elif embedding_type == "event":
        predictions, targets = get_event_based_prediction_files(task_path)
    else:
        raise ValueError(f"Unknown embedding type received: {embedding_type}")

    label_to_idx = label_vocab_as_dict(label_vocab, key="label", value="idx")

    scores = metadata["evaluation"]
    results = {}
    for score in scores:
        print("  -", score)
        # score_function = available_scores[score](metadata, label_to_idx)
        score_function = available_scores[score](label_to_idx=label_to_idx)
        new_results = score_function(np.array(predictions), np.array(targets))
        results.update({score: new_results})

    return results
