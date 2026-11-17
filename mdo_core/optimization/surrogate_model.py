# Gaussian Process (Kriging) surrogate model for sub-millisecond trade space evaluation

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from sklearn.metrics import r2_score

from .design_space import evaluate_design_point, generate_lhs_samples


class TradeSpaceSurrogate:
    # Multi-target Gaussian Process surrogate model for real-time aerostructural response
    def __init__(self, nu: float = 2.5, alpha: float = 1e-3, random_state: int = 42):
        self.nu = nu
        self.alpha = alpha
        self.random_state = random_state
        self.models = {}
        self.is_trained = False

    def train(self, X_train: np.ndarray, targets_dict: dict) -> dict:
        # Fits an independent Kriging regressor for each output objective
        scores = {}
        for target_name, y_values in targets_dict.items():
            kernel = Matern(nu=self.nu)
            gp = GaussianProcessRegressor(
                kernel=kernel,
                alpha=self.alpha,
                normalize_y=True,
                random_state=self.random_state,
            )
            gp.fit(X_train, y_values)
            self.models[target_name] = gp
            y_pred = gp.predict(X_train)
            scores[target_name] = float(r2_score(y_values, y_pred))

        self.is_trained = True
        return scores

    def predict(self, X_query: np.ndarray, return_std: bool = False):
        # Predicts target metrics across design points in sub-milliseconds
        if not self.is_trained:
            raise RuntimeError("Surrogate model must be trained before predicting.")

        predictions = {}
        uncertainties = {}

        for target_name, gp in self.models.items():
            if return_std:
                mean, std = gp.predict(X_query, return_std=True)
                predictions[target_name] = mean
                uncertainties[target_name] = std
            else:
                predictions[target_name] = gp.predict(X_query)

        if return_std:
            return predictions, uncertainties
        return predictions

    def evaluate_validation(self, X_val: np.ndarray, val_targets_dict: dict) -> dict:
        # Evaluates R2 determination coefficients and root-mean-square errors
        metrics = {}
        preds = self.predict(X_val)
        for target_name, y_true in val_targets_dict.items():
            y_pred = preds[target_name]
            r2 = float(r2_score(y_true, y_pred))
            rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
            metrics[target_name] = {"R2": r2, "RMSE": rmse}
        return metrics


def train_surrogate_for_mission(
    mission: dict,
    n_samples: int = 80,
    specific_energy: float = 220.0,
    degradation: float = 0.0,
    seed: int = 42,
) -> tuple:
    # Samples LHS design space, runs Picard sizing, and returns trained surrogate
    X_lhs = generate_lhs_samples(n_samples=n_samples, seed=seed)

    endur_list = []
    margin_list = []
    mtow_list = []
    stall_list = []
    valid_X = []

    for x in X_lhs:
        res = evaluate_design_point(
            aspect_ratio=x[0],
            wing_area=x[1],
            mission=mission,
            specific_energy=specific_energy,
            degradation=degradation,
        )
        if res["converged"]:
            valid_X.append(x)
            endur_list.append(res["max_endurance"])
            margin_list.append(res["energy_margin"])
            mtow_list.append(res["MTOW"])
            stall_list.append(res["V_stall"])

    X_train = np.array(valid_X)
    targets = {
        "endurance": np.array(endur_list),
        "energy_margin": np.array(margin_list),
        "mtow": np.array(mtow_list),
        "stall_speed": np.array(stall_list),
    }

    surrogate = TradeSpaceSurrogate(random_state=seed)
    train_scores = surrogate.train(X_train, targets)
    return surrogate, train_scores
