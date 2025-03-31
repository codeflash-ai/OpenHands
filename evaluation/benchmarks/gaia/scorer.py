import re
import string
import warnings


def normalize_number_str(number_str: str) -> float:
    """Converts a number string with common units like '$', '%', ',' to a float."""
    number_str = number_str.replace('$', '').replace('%', '').replace(',', '')
    try:
        return float(number_str)
    except ValueError:
        print(f'String {number_str} cannot be normalized to number str.')
        return float('inf')


def split_string(
    s: str,
    char_list: list[str] = None,
) -> list[str]:
    """Splits a string on specified characters."""
    if char_list is None:
        char_list = [',', ';']
    # Precompile the regex pattern for faster execution
    pattern = re.compile(f"[{''.join(char_list)}]")
    return pattern.split(s)


def question_scorer(
    model_answer: str,
    ground_truth: str,
) -> bool:
    """Scores a question by comparing the model answer to the ground truth."""
    def is_float(element: any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    # If ground truth is a number
    if is_float(ground_truth):
        print(f'Evaluating {model_answer} as a number.')
        normalized_answer = normalize_number_str(model_answer)
        return normalized_answer == float(ground_truth)

    # If ground truth is a list
    if any(char in ground_truth for char in [',', ';']):
        print(f'Evaluating {model_answer} as a comma separated list.')
        gt_elems = split_string(ground_truth)
        ma_elems = split_string(model_answer)

        # Check if lengths are different early
        if len(gt_elems) != len(ma_elems):
            warnings.warn(
                'Answer lists have different lengths, returning False.',
                UserWarning,
                stacklevel=2,
            )
            return False

        # Compare each element as float or str
        for ma_elem, gt_elem in zip(ma_elems, gt_elems):
            if is_float(gt_elem):
                normalized_ma_elem = normalize_number_str(ma_elem)
                if normalized_ma_elem != float(gt_elem):
                    return False
            else:
                if normalize_str(ma_elem, remove_punct=False) != normalize_str(gt_elem, remove_punct=False):
                    return False
        return True

    # If ground truth is a string
    print(f'Evaluating {model_answer} as a string.')
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
    # Remove all white spaces. Required e.g for seagull vs. sea gull
    no_spaces = re.sub(r'\s', '', input_str)

    # Remove punctuation, if specified.
    if remove_punct:
        translator = str.maketrans('', '', string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()
