from collections import Counter


def precision_recall_f1(predicted, expected):
    predicted, expected = set(predicted), set(expected)
    overlap = len(predicted & expected)
    precision = overlap / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = overlap / len(expected) if expected else (1.0 if not predicted else 0.0)
    return {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def macro_f1(expected, predicted):
    labels = sorted(set(expected) | set(predicted))
    matrix = {label: dict(Counter(pred for actual, pred in zip(expected, predicted) if actual == label)) for label in labels}
    scores = []
    for label in labels:
        scores.append(precision_recall_f1([index for index, value in enumerate(predicted) if value == label],
                                         [index for index, value in enumerate(expected) if value == label])["f1"])
    return {"macro_f1": sum(scores) / len(scores) if scores else None, "confusion_matrix": matrix}
