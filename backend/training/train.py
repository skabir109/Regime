import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

DATA_PATH = Path("data/prices_daily.csv")
MODEL_DIR = Path("model")
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"

# --- Regime labeling rules ---
# HighVol: volatility stress, regime instability, or sharp drawdown behavior
# RiskOn: positive trend with contained volatility and cross-asset confirmation
# RiskOff: negative trend, defensive leadership, or poor confirmation
VIX_HIGH = 25.0
VIX_ELEVATED = 20.0
SPY_VOL_HIGH = 0.02
SPY_VOL_EXTREME = 0.025

def load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df = df.sort_index().ffill()
    return df

def make_features(prices: pd.DataFrame) -> pd.DataFrame:
    col_spy = "SPY"
    col_gld = "GLD" if "GLD" in prices.columns else None
    col_uso = "USO" if "USO" in prices.columns else None
    col_tlt = "TLT" if "TLT" in prices.columns else None
    col_bito = "BITO" if "BITO" in prices.columns else None
    col_vix = "VIX" if "VIX" in prices.columns else ("VIX" if "VIX" in prices.columns else None)
    col_gbp = "GBPUSD=X" if "GBPUSD=X" in prices.columns else ("GBPUSD=X" if "GBPUSD=X" in prices.columns else None)

    if col_spy not in prices.columns:
        raise ValueError(f"Missing SPY column. Found columns: {list(prices.columns)}")

    aligned = prices.ffill()
    rets = aligned.pct_change()

    feats = pd.DataFrame(index=prices.index)

    spy_ma_20 = aligned[col_spy].rolling(20).mean()
    spy_ma_50 = aligned[col_spy].rolling(50).mean()
    spy_roll_high_20 = aligned[col_spy].rolling(20).max()
    spy_roll_high_60 = aligned[col_spy].rolling(60).max()

    feats["spy_ret_1d"] = rets[col_spy]
    feats["spy_mom_5d"] = aligned[col_spy].pct_change(5)
    feats["spy_mom_20d"] = aligned[col_spy].pct_change(20)
    feats["spy_mom_60d"] = aligned[col_spy].pct_change(60)
    feats["spy_vol_10d"] = rets[col_spy].rolling(10).std()
    feats["spy_vol_20d"] = rets[col_spy].rolling(20).std()
    feats["spy_trend_gap_20d"] = (aligned[col_spy] / spy_ma_20) - 1.0
    feats["spy_trend_gap_50d"] = (aligned[col_spy] / spy_ma_50) - 1.0
    feats["spy_drawdown_20d"] = (aligned[col_spy] / spy_roll_high_20) - 1.0
    feats["spy_drawdown_60d"] = (aligned[col_spy] / spy_roll_high_60) - 1.0

    if col_gld:
        feats["gld_ret_1d"] = rets[col_gld]
        feats["gld_mom_20d"] = aligned[col_gld].pct_change(20)

    if col_uso:
        feats["uso_ret_1d"] = rets[col_uso]
        feats["uso_mom_20d"] = aligned[col_uso].pct_change(20)

    if col_tlt:
        feats["tlt_ret_1d"] = rets[col_tlt]
        feats["tlt_mom_20d"] = aligned[col_tlt].pct_change(20)

    if col_bito:
        feats["bito_ret_1d"] = rets[col_bito]
        feats["bito_mom_20d"] = aligned[col_bito].pct_change(20)

    if col_gbp:
        feats["gbp_ret_1d"] = rets[col_gbp]
        feats["gbp_mom_20d"] = aligned[col_gbp].pct_change(20)

    if col_vix and col_vix in prices.columns:
        feats["vix_level"] = aligned[col_vix]
        feats["vix_chg_5d"] = aligned[col_vix].pct_change(5)
        feats["vix_gap_20d"] = (aligned[col_vix] / aligned[col_vix].rolling(20).mean()) - 1.0

    if col_gld:
        feats["gld_vs_spy_20d"] = aligned[col_gld].pct_change(20) - aligned[col_spy].pct_change(20)
    if col_uso:
        feats["uso_vs_spy_20d"] = aligned[col_uso].pct_change(20) - aligned[col_spy].pct_change(20)
    if col_tlt:
        feats["tlt_vs_spy_20d"] = aligned[col_tlt].pct_change(20) - aligned[col_spy].pct_change(20)
    if col_vix and col_vix in prices.columns:
        feats["vix_spy_stress"] = aligned[col_vix].pct_change(5) - aligned[col_spy].pct_change(5)

    required = [
        "spy_ret_1d",
        "spy_mom_5d",
        "spy_mom_20d",
        "spy_mom_60d",
        "spy_vol_10d",
        "spy_vol_20d",
        "spy_trend_gap_20d",
        "spy_trend_gap_50d",
        "spy_drawdown_20d",
        "spy_drawdown_60d",
    ]
    feats = feats.dropna(subset=required)
    return feats.ffill().fillna(0.0)


def label_regimes(prices: pd.DataFrame, feats: pd.DataFrame) -> pd.Series:
    """
    Label using the same cleaned index as feats to avoid NaNs from rolling windows.
    """
    y = pd.Series(index=feats.index, dtype="object")

    highvol = pd.Series(False, index=feats.index)
    if "vix_level" in feats.columns:
        highvol = highvol | (feats["vix_level"] >= VIX_HIGH)
    highvol = highvol | (feats["spy_vol_20d"] >= SPY_VOL_HIGH)
    if "vix_chg_5d" in feats.columns:
        highvol = highvol | (feats["vix_chg_5d"] > 0.12)
    if "vix_gap_20d" in feats.columns:
        highvol = highvol | (feats["vix_gap_20d"] > 0.18)
    highvol = highvol | ((feats["spy_drawdown_20d"] <= -0.05) & (feats["spy_vol_20d"] >= 0.018))
    highvol = highvol | ((feats["spy_ret_1d"].abs() >= 0.02) & (feats["spy_vol_10d"] >= 0.018))

    support_score = pd.Series(0.0, index=feats.index)
    support_score = support_score + (feats["spy_mom_20d"] > 0).astype(float)
    support_score = support_score + (feats["spy_mom_5d"] > 0).astype(float)
    support_score = support_score + (feats["spy_mom_60d"] > 0).astype(float)
    support_score = support_score + (feats["spy_trend_gap_20d"] > 0).astype(float)
    support_score = support_score + (feats["spy_trend_gap_50d"] > 0).astype(float)
    support_score = support_score + (feats["spy_drawdown_20d"] > -0.03).astype(float)
    support_score = support_score + (feats["spy_drawdown_60d"] > -0.08).astype(float)

    if "uso_mom_20d" in feats.columns:
        support_score = support_score + (feats["uso_mom_20d"] > 0).astype(float)
    if "bito_mom_20d" in feats.columns:
        support_score = support_score + (feats["bito_mom_20d"] > 0).astype(float)
    if "gbp_mom_20d" in feats.columns:
        support_score = support_score + (feats["gbp_mom_20d"] > 0).astype(float)
    if "gld_mom_20d" in feats.columns:
        support_score = support_score - (feats["gld_mom_20d"] > 0.03).astype(float)
    if "gld_vs_spy_20d" in feats.columns:
        support_score = support_score + (feats["gld_vs_spy_20d"] < 0).astype(float)
    if "uso_vs_spy_20d" in feats.columns:
        support_score = support_score + (feats["uso_vs_spy_20d"] > -0.05).astype(float)
    if "vix_level" in feats.columns:
        support_score = support_score + (feats["vix_level"] < VIX_ELEVATED).astype(float)

    defensive_score = pd.Series(0.0, index=feats.index)
    defensive_score = defensive_score + (feats["spy_mom_20d"] < 0).astype(float)
    defensive_score = defensive_score + (feats["spy_mom_5d"] < 0).astype(float)
    defensive_score = defensive_score + (feats["spy_mom_60d"] < 0).astype(float)
    defensive_score = defensive_score + (feats["spy_trend_gap_20d"] < 0).astype(float)
    defensive_score = defensive_score + (feats["spy_trend_gap_50d"] < 0).astype(float)
    defensive_score = defensive_score + (feats["spy_drawdown_20d"] <= -0.04).astype(float)
    defensive_score = defensive_score + (feats["spy_drawdown_60d"] <= -0.10).astype(float)
    if "gld_mom_20d" in feats.columns:
        defensive_score = defensive_score + (feats["gld_mom_20d"] > 0).astype(float)
    if "tlt_mom_20d" in feats.columns:
        defensive_score = defensive_score + (feats["tlt_mom_20d"] > 0).astype(float)
    if "uso_mom_20d" in feats.columns:
        defensive_score = defensive_score + (feats["uso_mom_20d"] < 0).astype(float)
    if "gbp_mom_20d" in feats.columns:
        defensive_score = defensive_score + (feats["gbp_mom_20d"] < 0).astype(float)
    if "gld_vs_spy_20d" in feats.columns:
        defensive_score = defensive_score + (feats["gld_vs_spy_20d"] > 0.03).astype(float)
    if "uso_vs_spy_20d" in feats.columns:
        defensive_score = defensive_score + (feats["uso_vs_spy_20d"] < -0.08).astype(float)
    if "vix_level" in feats.columns:
        defensive_score = defensive_score + (feats["vix_level"] >= VIX_ELEVATED).astype(float)
    if "vix_spy_stress" in feats.columns:
        defensive_score = defensive_score + (feats["vix_spy_stress"] > 0.08).astype(float)

    risk_on = (
        (~highvol)
        & (support_score >= 4.0)
        & (feats["spy_vol_20d"] < SPY_VOL_HIGH)
        & (feats["spy_drawdown_20d"] > -0.04)
    )
    risk_off = (
        (~highvol)
        & (
            (defensive_score >= 4.0)
            | (feats["spy_mom_20d"] < -0.03)
            | ((feats["spy_trend_gap_50d"] < 0) & (feats["spy_vol_20d"] >= 0.015))
            | (feats["spy_drawdown_60d"] <= -0.12)
        )
    )

    y[highvol] = "HighVol"
    y[risk_on] = "RiskOn"
    y[risk_off] = "RiskOff"
    y[y.isna() & (support_score >= defensive_score)] = "RiskOn"
    y[y.isna()] = "RiskOff"

    return y

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    prices = load_prices()
    feats = make_features(prices)
    y = label_regimes(prices, feats)

    # Encode labels
    classes = ["RiskOff", "RiskOn", "HighVol"]
    y_cat = pd.Categorical(y, categories=classes)
    if y_cat.isna().any():
        raise RuntimeError("Labeling produced NaNs; check thresholds and data alignment.")
    y_enc = y_cat.codes

    X = feats.values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, shuffle=False
    )
    class_counts = np.bincount(y_train, minlength=len(classes))
    class_weights = {
        index: len(y_train) / (len(classes) * max(count, 1))
        for index, count in enumerate(class_counts)
    }
    sample_weights = np.array([class_weights[int(label)] for label in y_train], dtype=float)

    model = XGBClassifier(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=len(classes),
        reg_lambda=1.0,
        random_state=42,
        n_jobs=4,
        eval_metric="mlogloss",
    )

    model.fit(X_train, y_train, sample_weight=sample_weights)

    probs = model.predict_proba(X_test)
    preds = probs.argmax(axis=1)
    report = classification_report(y_test, preds, target_names=classes, output_dict=True)

    print("Classification report:")
    print(classification_report(y_test, preds, target_names=classes))

    joblib.dump(model, MODEL_PATH)

    meta = {
        "classes": classes,
        "features": feats.columns.tolist(),
        "thresholds": {
            "VIX_HIGH": VIX_HIGH,
            "VIX_ELEVATED": VIX_ELEVATED,
            "SPY_VOL_HIGH": SPY_VOL_HIGH,
            "SPY_VOL_EXTREME": SPY_VOL_EXTREME,
        },
        "training": {
            "rows": int(len(feats)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "date_range": {
                "start": str(feats.index.min().date()),
                "end": str(feats.index.max().date()),
            },
            "class_distribution": {
                label: int((y == label).sum()) for label in classes
            },
            "class_weights": {
                classes[index]: round(float(weight), 4)
                for index, weight in class_weights.items()
            },
            "metrics": {
                "accuracy": round(float(report["accuracy"]), 4),
                "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
                "weighted_f1": round(float(report["weighted avg"]["f1-score"]), 4),
            },
        },
        "feature_importance": {
            feature: round(float(score), 4)
            for feature, score in sorted(
                zip(feats.columns.tolist(), model.feature_importances_),
                key=lambda item: item[1],
                reverse=True,
            )
        },
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved meta to {META_PATH}")


if __name__ == "__main__":
    main()
