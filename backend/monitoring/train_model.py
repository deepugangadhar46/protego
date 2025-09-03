import argparse
import csv
import os
from typing import List, Tuple

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from .ml_model import build_default_pipeline, save_model


def read_csv_dataset(path: str) -> Tuple[List[str], List[str]]:
    texts: List[str] = []
    labels: List[str] = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Expect columns: text,label
        for row in reader:
            t = (row.get('text') or '').strip()
            y = (row.get('label') or '').strip()
            if t and y:
                texts.append(t)
                labels.append(y)
    return texts, labels


def main():
    parser = argparse.ArgumentParser(description='Train threat classification model from CSV')
    parser.add_argument('--data', required=True, help='Path to CSV with columns: text,label')
    parser.add_argument('--out', default=None, help='Output model path (optional)')
    args = parser.parse_args()

    texts, labels = read_csv_dataset(args.data)
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)

    pipeline = build_default_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))

    out_path = args.out or None
    if out_path is None:
        from .ml_model import DEFAULT_MODEL_PATH
        out_path = DEFAULT_MODEL_PATH

    unique_labels = sorted(set(labels))
    save_model(pipeline, unique_labels, out_path)
    print(f"Model saved to: {out_path}")


if __name__ == '__main__':
    main()


