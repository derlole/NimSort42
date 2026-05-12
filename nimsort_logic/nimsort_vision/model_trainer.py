"""
model_trainer.py
----------------
Trainiert den Decision-Tree-Klassifikator (max_depth=5) auf hu_0 + fourier_2
und speichert das Modell als 'object_classifier.joblib'.

Einfach in VSCode auf den Play-Button drücken – keine weiteren Argumente nötig.
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.tree import DecisionTreeClassifier, plot_tree


CSV_PATH = os.path.join(os.path.dirname(__file__), "features.csv")
OUT_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")
# ──────────────────────────────────────────────────────────────────────────────
# Konfiguration – muss mit FeatureDetection.LABEL_MAP übereinstimmen
# ──────────────────────────────────────────────────────────────────────────────
CLASSES  = ["einhorn", "katze", "kreis", "quadrat"]   # Index 0–3
FEATURES = ["hu_0", "fourier_2"]

# ──────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────────────────────────

def load_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        sys.exit(f"[TRAIN] Fehlende Spalten: {missing}")
    if "label" not in df.columns:
        sys.exit("[TRAIN] Spalte 'label' fehlt.")
    unknown = set(df["label"].unique()) - set(CLASSES)
    if unknown:
        sys.exit(f"[TRAIN] Unbekannte Labels: {unknown}")
    X = df[FEATURES].values.astype(np.float32)
    y = np.array([CLASSES.index(l) for l in df["label"]], dtype=np.int64)
    return X, y


def evaluate(model, X, y, out_dir):
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    print(f"\n[TRAIN] 10-fache Kreuzvalidierung:")
    print(f"        Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

    y_pred = cross_val_predict(model, X, y, cv=cv)
    print("\n[TRAIN] Klassifikationsreport:")
    print(classification_report(y, y_pred, target_names=CLASSES))

    cm = confusion_matrix(y, y_pred)
    print("[TRAIN] Konfusionsmatrix:")
    print(cm)

    # Plot: Konfusionsmatrix + Entscheidungsbaum
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ConfusionMatrixDisplay(cm, display_labels=CLASSES).plot(
        ax=axes[0], colorbar=False, cmap="Blues"
    )
    axes[0].set_title("Konfusionsmatrix (10-fold CV)")

    # Baum visualisieren (auf allen Daten trainiertes Modell)
    model.fit(X, y)
    plot_tree(
        model, feature_names=FEATURES, class_names=CLASSES,
        filled=True, rounded=True, ax=axes[1], fontsize=9
    )
    axes[1].set_title("Decision Tree (max_depth=5)")

    plt.tight_layout()
    plot_path = os.path.join(out_dir, "confusion_matrix.png")
    plt.savefig(plot_path, dpi=130)
    print(f"[TRAIN] Plot gespeichert: {plot_path}")
    plt.close()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print(f"[TRAIN] Lade Daten: {CSV_PATH}")
    X, y = load_csv(CSV_PATH)
    print(f"[TRAIN] {len(X)} Samples | Merkmale: {FEATURES}")
    print(f"[TRAIN] Klassen: { {i: CLASSES[i] for i in range(len(CLASSES))} }")

    model = DecisionTreeClassifier(max_depth=5, random_state=42)

    out_dir = os.path.dirname(os.path.abspath(OUT_PATH))
    os.makedirs(out_dir, exist_ok=True)
    evaluate(model, X, y, out_dir)

    model.fit(X, y)
    joblib.dump(model, OUT_PATH)
    print(f"\n[TRAIN] Modell gespeichert: {OUT_PATH}")


if __name__ == "__main__":
    main()