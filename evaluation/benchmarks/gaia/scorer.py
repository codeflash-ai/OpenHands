import re
import string
import warnings


def normalize_number_str(number_str: str) -> float:
    # Use str.replace effectively by chaining calls
    number_str = number_str.replace("$", "").replace("%", "").replace(",", "")
    try:
        return float(number_str)
    except ValueError:
        print(f"String {number_str} cannot be normalized to number str.")
        return float("inf")


def split_string(
    s: str,
    char_list: list[str] = None,
) -> list[str]:
    if char_list is None:
        char_list = [",", ";"]
    # Use a compiled regex pattern to increase efficiency on repeated calls
    pattern = re.compile(f"[{''.join(map(re.escape, char_list))}]")
    return pattern.split(s)


def question_scorer(
    model_answer: str,
    ground_truth: str,
) -> bool:
    # Helper function moved outside to prevent re-definitions on every call
    def is_float(element: str) -> bool:
        if not element:
            return False
        try:
            float(element)
            return True
        except ValueError:
            return False

    # Check if the ground_truth is a number
    if is_float(ground_truth):
        print(f"Evaluating {model_answer} as a number.")
        normalized_answer = normalize_number_str(model_answer)
        return normalized_answer == float(ground_truth)

    # Check if the ground_truth is a list
    elif any(char in ground_truth for char in [",", ";"]):
        print(f"Evaluating {model_answer} as a comma separated list.")

        gt_elems = split_string(ground_truth)
        ma_elems = split_string(model_answer)

        if len(gt_elems) != len(ma_elems):
            warnings.warn(
                "Answer lists have different lengths, returning False.",
                UserWarning,
                stacklevel=2,
            )
            return False

        # Precompute the normalization of ground truth elements
        gt_elems_normalized = [
            normalize_number_str(gt_elem)
            if is_float(gt_elem)
            else normalize_str(gt_elem, remove_punct=False)
            for gt_elem in gt_elems
        ]

        comparisons = []
        for ma_elem, gt_elem_normalized in zip(ma_elems, gt_elems_normalized):
            if isinstance(gt_elem_normalized, float):
                normalized_ma_elem = normalize_number_str(ma_elem)
                comparisons.append(normalized_ma_elem == gt_elem_normalized)
            else:
                comparisons.append(
                    normalize_str(ma_elem, remove_punct=False) == gt_elem_normalized
                )
        return all(comparisons)

    # Check if the ground_truth is a string
    else:
        print(f"Evaluating {model_answer} as a string.")
        return normalize_str(model_answer) == normalize_str(ground_truth)


def normalize_str(input_str, remove_punct=True) -> str:
    """Normalize a string by:
    - Removing all white spaces
    - Optionally removing punctuation (if remove_punct is True)
    - Converting to lowercase
    Parameters:
    - input_str: str, the string to normalize
    - remove_punct: bool, whether to remove punctuation (default: True)

    Returns:
    - str, the normalized string
    """
    # Remove all white spaces.
    no_spaces = "".join(input_str.split())

    # Remove punctuation, if specified.
    if remove_punct:
        translator = str.maketrans("", "", string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()
