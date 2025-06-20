from typing import Callable, Dict, List, Union

import numpy as np


def _hinge_loss(
    softmax: Union[np.ndarray, List[np.ndarray]],
) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Computes the hinge loss nonconformity score for all classes.

    The hinge loss for a class is defined as 1 minus the predicted probability assigned to that class.

    Args:
        softmax (Union[np.ndarray, List[np.ndarray]]): Predicted softmax probabilities.
            - Shape (B, C) for single-task, where B is the batch size and C is the number of classes.
            - List of arrays for multi-task, each of shape (B, C_t).

    Returns:
        np.ndarray: Hinge loss values for each class.
            - Shape (B, C) for single-task.
            - List of arrays for multi-task, each of shape (B, C_t).
    """
    if isinstance(softmax, list):
        return [1 - s for s in softmax]
    else:
        return 1 - softmax


def _margin_score(
    softmax: Union[np.ndarray, List[np.ndarray]],
) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Computes the margin nonconformity score for all classes.

    The margin for each class is defined as the highest incorrect class probability
    minus the predicted probability for that class.

    Args:
        softmax (Union[np.ndarray, List[np.ndarray]]): Predicted softmax probabilities.
            - Shape (B, C) for single-task, where B is the batch size and C is the number of classes.
            - List of arrays for multi-task, each of shape (B, C_t).

    Returns:
        Union[np.ndarray, List[np.ndarray]]: Margin scores for each class.
            - Shape (B, C) for single-task.
            - List of arrays for multi-task, each of shape (B, C_t).
    """

    def compute_margin(s: np.ndarray) -> np.ndarray:
        B, C = s.shape
        margins = np.empty((B, C))
        for j in range(C):
            mask = np.ones(C, dtype=bool)
            mask[j] = False
            margins[:, j] = np.max(s[:, mask], axis=1) - s[:, j]
        return margins

    if isinstance(softmax, list):
        return [compute_margin(s) for s in softmax]
    else:
        if softmax.ndim == 1:
            softmax = softmax[np.newaxis, :]
        return compute_margin(softmax)


def _pip_score(
    softmax: Union[np.ndarray, List[np.ndarray]],
) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Computes the PIP (Penalized Inverse Probability) nonconformity score for all classes.

    The PIP score for each class is defined as 1 minus the predicted probability,
    plus a penalty term based on the cumulative inverse-rank weighted probabilities
    of the top-ranked classes (excluding the current class).

    Args:
        softmax (Union[np.ndarray, List[np.ndarray]]): Predicted softmax probabilities.
            - Shape (B, C) for single-task, where B is the batch size and C is the number of classes.
            - List of arrays for multi-task, each of shape (B, C_t).

    Returns:
        Union[np.ndarray, List[np.ndarray]]: PIP scores for each class.
            - Shape (B, C) for single-task.
            - List of arrays for multi-task, each of shape (B, C_t).
    """

    def compute_pip(s: np.ndarray) -> np.ndarray:
        B, C = s.shape
        hinge = 1 - s
        sorted_indices = np.argsort(s, axis=1)[:, ::-1]
        sorted_probs = np.take_along_axis(s, sorted_indices, axis=1)
        cum_penalty = np.cumsum(sorted_probs / np.arange(1, C + 1), axis=1)
        # Map each class to its rank and gather penalties
        ranks = np.argsort(sorted_indices, axis=1)
        penalties = np.take_along_axis(cum_penalty, ranks, axis=1)

        return hinge + penalties

    if isinstance(softmax, list):
        return [compute_pip(s) for s in softmax]
    else:
        if softmax.ndim == 1:
            softmax = softmax[np.newaxis, :]
        return compute_pip(softmax)


# Dictionary mapping names to nonconformity functions
NONCONFORMITY_FN_DIC: Dict[str, Callable[..., np.ndarray]] = {
    "hinge": _hinge_loss,
    "margin": _margin_score,
    "pip": _pip_score,
}
