import os
import joblib
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.tree import DecisionTreeClassifier, plot_tree

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "features.csv")
OUT_PATH = os.path.join(os.path.dirname(__file__), "object_classifier.joblib")

CLASSES  = ["einhorn", "katze", "kreis", "quadrat"]
FEATURES = ["hu_0", "hu_3"]

# Daten laden
df = pd.read_csv(CSV_PATH)
X  = df[FEATURES].values.astype(np.float32)
y  = np.array([CLASSES.index(l) for l in df["label"]], dtype=np.int64)
print(f"[TRAIN] {len(X)} Samples | Features: {FEATURES}")

# Modell + Kreuzvalidierung
model = DecisionTreeClassifier(max_depth=5, random_state= 1)
cv    = StratifiedKFold(n_splits=10, shuffle=True, random_state= 1)

scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
print(f"[TRAIN] Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

y_pred = cross_val_predict(model, X, y, cv=cv)
print(classification_report(y, y_pred, target_names=CLASSES))

# Plot: Konfusionsmatrix + Baum
model.fit(X, y)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ConfusionMatrixDisplay(confusion_matrix(y, y_pred), display_labels=CLASSES).plot(
    ax=axes[0], colorbar=False, cmap="Blues")
axes[0].set_title("Konfusionsmatrix (10-fold CV)")
plot_tree(model, feature_names=FEATURES, class_names=CLASSES,
          filled=True, rounded=True, ax=axes[1], fontsize=9)
axes[1].set_title("Decision Tree (max_depth=5)")
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(OUT_PATH), "confusion_matrix.png"), dpi=130)
plt.close()

# Modell speichern
joblib.dump(model, OUT_PATH)
print(f"[TRAIN] Modell gespeichert: {OUT_PATH}")