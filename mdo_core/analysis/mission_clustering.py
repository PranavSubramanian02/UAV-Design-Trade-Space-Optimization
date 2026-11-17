# Unsupervised K-Means clustering and configuration family archetype synthesis

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def prepare_clustering_features(pareto_records: list) -> tuple:
    # Extracts and standardizes physical aircraft features for clustering
    features = []
    for r in pareto_records:
        ar = r.get("aspect_ratio", (r["span"] ** 2) / (r["W0"] / r["wing_loading"]))
        ws = r["wing_loading"]
        mtow = r["MTOW"]
        endur = r["max_endurance"]
        payload = r["m_payload"]
        features.append([ar, ws, mtow, endur, payload])

    features = np.array(features)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    return features, scaled_features, scaler


def evaluate_silhouette_scores(
    scaled_features: np.ndarray, k_range: range = range(2, 6)
) -> dict:
    # Evaluates silhouette cluster separation scores across cluster counts
    scores = {}
    n_samples = scaled_features.shape[0]
    for k in k_range:
        if k >= n_samples:
            continue
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(scaled_features)
        score = float(silhouette_score(scaled_features, labels))
        scores[k] = score
    return scores


def cluster_mission_configurations(
    pareto_records: list,
    n_clusters: int = 3,
    random_state: int = 42,
) -> dict:
    # Partitions Pareto-optimal UAV configurations into distinct airframe families
    if len(pareto_records) < n_clusters:
        return {"error": "Insufficient Pareto points for clustering", "clusters": {}}

    raw_features, scaled_features, scaler = prepare_clustering_features(pareto_records)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(scaled_features)
    score = float(silhouette_score(scaled_features, labels))

    family_names = [
        "Family Alpha (Long-Endurance ISR)",
        "Family Beta (Heavy-Payload Transport)",
        "Family Gamma (Agile Tactical Dash)",
    ]

    clusters = {}
    for c in range(n_clusters):
        idx = np.where(labels == c)[0]
        c_pts = raw_features[idx]

        # Identify representative baseline aircraft closest to the cluster centroid
        c_center = kmeans.cluster_centers_[c]
        dists = np.linalg.norm(scaled_features[idx] - c_center, axis=1)
        best_rep_idx = idx[np.argmin(dists)]

        name = family_names[c] if c < len(family_names) else f"Family_{c + 1}"
        clusters[name] = {
            "n_designs": len(idx),
            "avg_aspect_ratio": float(c_pts[:, 0].mean()),
            "avg_wing_loading": float(c_pts[:, 1].mean()),
            "avg_mtow": float(c_pts[:, 2].mean()),
            "avg_endurance": float(c_pts[:, 3].mean()),
            "avg_payload": float(c_pts[:, 4].mean()),
            "representative_design": pareto_records[best_rep_idx],
        }

    return {
        "silhouette_score": score,
        "n_clusters": n_clusters,
        "clusters": clusters,
        "labels": labels.tolist(),
    }
