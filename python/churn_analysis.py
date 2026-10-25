"""
Customer Churn Analysis — standalone reproducible script.

Reproduces the full analysis performed interactively:
  Phase 1  Range/sanity checks on the raw dataset
  Phase 2  Data quality assessment (duplicates, categorical consistency,
           complaint_type missingness investigation)
  Phase 3  Cleaning (adds complaint_type_clean and two mismatch flag columns;
           writes a new cleaned CSV, never overwrites the raw file)
  Phase 4  Churn-driver analysis by category (Customer Profile,
           Product Usage, Billing & Payment, Customer Support,
           Engagement & Feedback) — group means/rates + significance tests
  Phase 5  Cross-category summary chart of the significant drivers

Requires: pandas, scipy, matplotlib
Usage:    python python/churn_analysis.py   (run from the project folder)
Input:    data/customer_churn_business_dataset.csv
Outputs:  data/customer_churn_business_dataset_cleaned.csv  (Phase 3 result)
          outputs/churn_drivers_chart.png                     (Phase 5 chart)
"""

import os
import sys

import pandas as pd
from scipy import stats

RAW_PATH = "data/customer_churn_business_dataset.csv"
CLEANED_PATH = "data/customer_churn_business_dataset_cleaned.csv"
CHART_PATH = "outputs/churn_drivers_chart.png"

pd.set_option("display.width", 120)


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
# Phase 1 — range / sanity checks
# ---------------------------------------------------------------------------
def phase1_checks(df):
    section("PHASE 1 — Range checks")
    checks = {
        "nps_score": (-100, 100),
        "csat_score": (1, 5),
        "age": (10, 100),
    }
    for col, (lo, hi) in checks.items():
        actual_lo, actual_hi = df[col].min(), df[col].max()
        out_of_range = ((df[col] < lo) | (df[col] > hi)).sum()
        print(f"{col:12s} requested [{lo}, {hi}]  actual [{actual_lo}, {actual_hi}]  "
              f"out-of-range rows: {out_of_range}")
        
    print("\nMin and max of every numeric column:")
    print(df.describe().T[["min", "max"]])
    print(f"\nRows x cols: {df.shape[0]} x {df.shape[1]}")
    missing = df.isna().sum()
    missing = missing[missing > 0]
    print("Columns with missing values:")
    for col, n in missing.items():
        print(f"  {col}: {n} ({n / len(df):.2%})")


# ---------------------------------------------------------------------------
# Phase 2 — data quality assessment
# ---------------------------------------------------------------------------
def phase2_checks(df):
    section("PHASE 2 — Data quality assessment")

    dup_ids = df["customer_id"].duplicated().sum()
    dup_rows = df.duplicated().sum()
    print(f"Duplicate customer_id values: {dup_ids}")
    print(f"Fully duplicate rows: {dup_rows}")

    for col in ["discount_applied", "price_increase_last_3m", "survey_response"]:
        print(f"\n{col} value counts:")
        print(df[col].value_counts())

    # complaint_type missingness vs. support_tickets
    missing_mask = df["complaint_type"].isna()
    with_tickets = ((missing_mask) & (df["support_tickets"] >= 1)).sum()
    zero_tickets_missing = ((missing_mask) & (df["support_tickets"] == 0)).sum()
    present_no_tickets = ((~missing_mask) & (df["support_tickets"] == 0)).sum()
    print(f"\ncomplaint_type missing: {missing_mask.sum()} ({missing_mask.mean():.2%})")
    print(f"  of which support_tickets == 0: {zero_tickets_missing}")
    print(f"  of which support_tickets >= 1: {with_tickets}  <- inconsistent with 'no complaint'")
    print(f"complaint_type present but support_tickets == 0: {present_no_tickets}  <- also inconsistent")


# ---------------------------------------------------------------------------
# Phase 3 — cleaning
# ---------------------------------------------------------------------------
def phase3_clean(df):
    section("PHASE 3 — Cleaning")
    cleaned = df.copy()

    # Decision: keep complaint_type untouched; add a cleaned copy with
    # missing values labeled "Unknown" rather than imputing/dropping.
    cleaned["complaint_type_clean"] = cleaned["complaint_type"].fillna("Unknown")

    # Decision: flag the two inconsistency patterns found in Phase 2 as
    # separate boolean columns rather than altering complaint_type_clean.
    cleaned["complaint_missing_with_tickets"] = (
        cleaned["complaint_type"].isna() & (cleaned["support_tickets"] >= 1)
    )
    cleaned["complaint_present_no_tickets"] = (
        cleaned["complaint_type"].notna() & (cleaned["support_tickets"] == 0)
    )

    print(f"Rows: {len(df)} -> {len(cleaned)} (no rows dropped)")
    print(f"Columns: {df.shape[1]} -> {cleaned.shape[1]}")
    print("\ncomplaint_type_clean distribution:")
    print(cleaned["complaint_type_clean"].value_counts())
    print(f"\ncomplaint_missing_with_tickets = True: {cleaned['complaint_missing_with_tickets'].sum()}")
    print(f"complaint_present_no_tickets = True:   {cleaned['complaint_present_no_tickets'].sum()}")

    cleaned.to_csv(CLEANED_PATH, index=False)
    print(f"\nSaved: {CLEANED_PATH}  (raw file left untouched)")
    return cleaned


# ---------------------------------------------------------------------------
# Phase 4 — churn-driver analysis by category
# ---------------------------------------------------------------------------
CATEGORIES = {
    "Customer Profile": {
        "numeric": ["tenure_months", "age"],
        "categorical": ["contract_type", "gender", "city", "country",
                         "signup_channel", "customer_segment"],
    },
    "Product Usage": {
        "numeric": ["monthly_logins", "last_login_days_ago", "weekly_active_days",
                    "avg_session_time", "features_used", "usage_growth_rate"],
        "categorical": [],
    },
    "Billing & Payment": {
        "numeric": ["total_revenue", "payment_failures", "monthly_fee"],
        "categorical": ["payment_method", "discount_applied", "price_increase_last_3m"],
    },
    "Customer Support": {
        "numeric": ["csat_score", "escalations", "support_tickets", "avg_resolution_time"],
        "categorical": ["complaint_type_clean"],
    },
    "Engagement & Feedback": {
        "numeric": ["email_open_rate", "nps_score", "referral_count", "marketing_click_rate"],
        "categorical": ["survey_response"],
    },
}

ALPHA = 0.05


def analyze_category(df, name, spec):
    churned = df[df["churn"] == 1]
    retained = df[df["churn"] == 0]

    results = []
    for col in spec["numeric"]:
        cm, rm = churned[col].mean(), retained[col].mean()
        diff = cm - rm
        pct = diff / rm * 100 if rm else float("nan")
        t, p = stats.ttest_ind(churned[col].dropna(), retained[col].dropna(), equal_var=False)
        results.append((col, "numeric", cm, rm, diff, pct, p))

    for col in spec["categorical"]:
        ct = pd.crosstab(df[col], df["churn"])
        chi2, p, dof, exp = stats.chi2_contingency(ct)
        rate_min = df.groupby(col)["churn"].mean().min() * 100
        rate_max = df.groupby(col)["churn"].mean().max() * 100
        results.append((col, "categorical", rate_min, rate_max, None, None, p))

    section(f"Category: {name}")
    for col, kind, a, b, diff, pct, p in results:
        sig = "SIGNIFICANT" if p < ALPHA else "not significant"
        if kind == "numeric":
            print(f"  {col:22s} churned={a:9.3f}  retained={b:9.3f}  "
                  f"diff={diff:+9.3f} ({pct:+6.1f}%)  p={p:.2e}  [{sig}]")
        else:
            print(f"  {col:22s} churn-rate range {a:.1f}%-{b:.1f}%  "
                  f"chi2 p={p:.2e}  [{sig}]")
    return results


def run_all_categories(df):
    section("PHASE 4 — churn-driver analysis by category")
    overall_rate = df["churn"].mean()
    print(f"Overall churn rate: {overall_rate:.2%} "
          f"({(df['churn']==1).sum()} churned / {(df['churn']==0).sum()} retained "
          f"of {len(df)})")

    all_results = {}
    for name, spec in CATEGORIES.items():
        all_results[name] = analyze_category(df, name, spec)
    return all_results


# ---------------------------------------------------------------------------
# Phase 5 — cross-category chart of significant drivers
# ---------------------------------------------------------------------------
# The five factors that were statistically significant (p < 0.05) with a
# non-trivial effect size across all five categories. total_revenue is also
# significant but is left out of the headline chart because it is highly
# correlated with tenure_months (churners simply have less time to accrue
# revenue) rather than an independent driver — see the discussion in the
# written summary.
SIGNIFICANT_FACTORS = [
    "tenure_months",
    "monthly_logins",
    "last_login_days_ago",
    "payment_failures",
    "csat_score",
]


def build_chart(df):
    import numpy as np
    import matplotlib.pyplot as plt

    churned = df[df["churn"] == 1]
    retained = df[df["churn"] == 0]

    labels, neg_log10_p, pct_effect = [], [], []
    for col in SIGNIFICANT_FACTORS:
        cm, rm = churned[col].mean(), retained[col].mean()
        pct = (cm - rm) / rm * 100
        t, p = stats.ttest_ind(churned[col].dropna(), retained[col].dropna(), equal_var=False)
        labels.append(col)
        neg_log10_p.append(-np.log10(p))
        pct_effect.append(pct)

    # order by strength of significance, strongest first
    order = np.argsort(neg_log10_p)[::-1]
    labels = [labels[i] for i in order]
    neg_log10_p = [neg_log10_p[i] for i in order]
    pct_effect = [pct_effect[i] for i in order]

    BLUE = "#2a78d6"
    INK = "#0b0b0b"
    MUTED = "#898781"
    GRID = "#e1e0d9"

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("#fcfcfb")

    # Panel 1: statistical significance (-log10 p)
    ax = axes[0]
    ax.set_facecolor("#fcfcfb")
    y = np.arange(len(labels))
    ax.barh(y, neg_log10_p, height=0.55, color=BLUE, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("-log10(p-value)  (higher = stronger evidence)", color=MUTED, fontsize=9)
    ax.set_title("Statistical significance", color=INK, fontsize=11, loc="left")
    ax.axvline(-np.log10(0.05), color=MUTED, linestyle="--", linewidth=1, zorder=2)
    ax.text(-np.log10(0.05), len(labels) - 0.3, " p=0.05", color=MUTED, fontsize=8, va="top")
    for i, v in enumerate(neg_log10_p):
        ax.text(v + max(neg_log10_p) * 0.02, i, f"p={10**-v:.1e}", va="center", fontsize=8, color=INK)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(left=False)

    # Panel 2: effect size (% difference, churned vs retained)
    ax = axes[1]
    ax.set_facecolor("#fcfcfb")
    ax.barh(y, pct_effect, height=0.55, color=BLUE, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.axvline(0, color=MUTED, linewidth=1, zorder=2)
    ax.set_xlabel("% difference, churned vs. retained", color=MUTED, fontsize=9)
    ax.set_title("Effect size", color=INK, fontsize=11, loc="left")
    span = max(pct_effect) - min(pct_effect)
    ax.set_xlim(min(pct_effect) - span * 0.35, max(pct_effect) + span * 0.2)
    for i, v in enumerate(pct_effect):
        offset = span * 0.04
        ha = "left" if v >= 0 else "right"
        x = v + offset if v >= 0 else v - offset
        ax.text(x, i, f"{v:+.1f}%", va="center", ha=ha, fontsize=8, color=INK)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(left=False)

    fig.suptitle("Churn drivers with statistically significant differences (p < 0.05)",
                 color=INK, fontsize=12, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(CHART_PATH, dpi=150, facecolor=fig.get_facecolor())
    print(f"\nSaved: {CHART_PATH}")


# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(RAW_PATH):
        sys.exit(f"Raw dataset not found: {RAW_PATH}")

    df_raw = pd.read_csv(RAW_PATH)
    phase1_checks(df_raw)
    phase2_checks(df_raw)
    df_clean = phase3_clean(df_raw)
    run_all_categories(df_clean)
    build_chart(df_clean)

    section("DONE")
    print(f"Cleaned dataset: {CLEANED_PATH}")
    print(f"Chart:           {CHART_PATH}")


if __name__ == "__main__":
    main()
