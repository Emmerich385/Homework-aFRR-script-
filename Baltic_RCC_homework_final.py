import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ============================================================
# SETTINGS
# ============================================================

START_DATE = "2025-09-22T00:00"
END_DATE = "2025-09-23T00:00"

COUNTRY = "Estonia"       # Estonia, Latvia, or Lithuania

# Choose how the graph time should be displayed:
#
# "UTC"               -> display UTC
# "Europe/Tallinn"    -> display Tallinn local time
#
DISPLAY_TIMEZONE = "UTC"


# ============================================================
# API
# ============================================================

url = "https://api-baltic.transparency-dashboard.eu/api/v1/export"


# ============================================================
# GET aFRR ACTIVATION DATA
# ============================================================

afrr_params = {
    "id": "activations_afrr",
    "start_date": START_DATE,
    "end_date": END_DATE,
    "output_time_zone": "UTC",
    "output_format": "json",
    "json_header_groups": 0
}

response = requests.get(url, params=afrr_params)
response.raise_for_status()

afrr_result = response.json()

if afrr_result["error"]:
    print("aFRR API returned an error:")
    print(afrr_result)
    exit()

afrr_data = afrr_result["data"]


# ============================================================
# CONVERT aFRR DATA TO DATAFRAME
# ============================================================

df = pd.DataFrame(afrr_data["timeseries"])

df[[
    "Estonia_Upward",
    "Estonia_Downward",
    "Latvia_Upward",
    "Latvia_Downward",
    "Lithuania_Upward",
    "Lithuania_Downward"
]] = pd.DataFrame(
    df["values"].tolist(),
    index=df.index
)

df["from"] = pd.to_datetime(df["from"])
df["to"] = pd.to_datetime(df["to"])

df = df.drop(columns=["values"])


# ============================================================
# GET IMBALANCE VOLUME DATA
# ============================================================

imbalance_params = {
    "id": "imbalance_volumes_v2",
    "start_date": START_DATE,
    "end_date": END_DATE,
    "output_time_zone": "UTC",
    "output_format": "json",
    "json_header_groups": 0
}

response = requests.get(url, params=imbalance_params)
response.raise_for_status()

imbalance_result = response.json()

if imbalance_result["error"]:
    print("Imbalance API returned an error:")
    print(imbalance_result)
    exit()

imbalance_data = imbalance_result["data"]


# ============================================================
# CONVERT IMBALANCE DATA TO DATAFRAME
# ============================================================

imbalance_df = pd.DataFrame(
    imbalance_data["timeseries"]
)

imbalance_df[[
    "Estonia_Imbalance",
    "Latvia_Imbalance",
    "Lithuania_Imbalance"
]] = pd.DataFrame(
    imbalance_df["values"].tolist(),
    index=imbalance_df.index
)

imbalance_df["from"] = pd.to_datetime(
    imbalance_df["from"]
)

imbalance_df["to"] = pd.to_datetime(
    imbalance_df["to"]
)

imbalance_df = imbalance_df.drop(
    columns=["values"]
)


# ============================================================
# CONVERT DISPLAY TIMEZONE
# ============================================================

df["from"] = df["from"].dt.tz_convert(
    DISPLAY_TIMEZONE
)

df["to"] = df["to"].dt.tz_convert(
    DISPLAY_TIMEZONE
)

imbalance_df["from"] = imbalance_df["from"].dt.tz_convert(
    DISPLAY_TIMEZONE
)

imbalance_df["to"] = imbalance_df["to"].dt.tz_convert(
    DISPLAY_TIMEZONE
)


# ============================================================
# SELECT COUNTRY
# ============================================================

upward_column = COUNTRY + "_Upward"
downward_column = COUNTRY + "_Downward"
imbalance_column = COUNTRY + "_Imbalance"

if upward_column not in df.columns:
    print("Unknown country:", COUNTRY)
    print("Choose Estonia, Latvia, or Lithuania.")
    exit()

if imbalance_column not in imbalance_df.columns:
    print("Unknown country:", COUNTRY)
    print("Choose Estonia, Latvia, or Lithuania.")
    exit()


# ============================================================
# COMBINE THE DATA
# ============================================================

combined = pd.merge(
    df[
        [
            "from",
            upward_column,
            downward_column
        ]
    ],
    imbalance_df[
        [
            "from",
            imbalance_column
        ]
    ],
    on="from",
    how="inner"
)
# ============================================================
# Descriptive statistics and aFRR activation frequency
# ============================================================

print("\nDescriptive statistics")
print("----------------------")

for name, column in [
    ("Upward aFRR", upward_column),
    ("Downward aFRR", downward_column),
    ("Imbalance", imbalance_column)
]:
    series = combined[column].dropna()

    print(f"\n{name}:")
    print(f"  Mean:              {series.mean():.3f}")
    print(f"  Median:            {series.median():.3f}")
    print(f"  Standard deviation:{series.std():.3f}")
    print(f"  Minimum:           {series.min():.3f}")
    print(f"  Maximum:           {series.max():.3f}")


# ============================================================
# aFRR activation frequency
# ============================================================

upward = combined[upward_column].dropna()
downward = combined[downward_column].dropna()

upward_active = upward > 0
downward_active = downward > 0

print("\naFRR activation frequency")
print("-------------------------")

print(f"Upward activation:")
print(f"  Active periods:       {upward_active.mean() * 100:.2f}%")
print(f"  Average when active:  {upward[upward > 0].mean():.3f}")

print(f"\nDownward activation:")
print(f"  Active periods:       {downward_active.mean() * 100:.2f}%")
print(f"  Average when active:  {downward[downward > 0].mean():.3f}")

# ============================================================
# CORRELATION BETWEEN aFRR ACTIVATION AND IMBALANCE VOLUME
# ============================================================

for direction, column in [
    ("Upward", upward_column),
    ("Downward", downward_column)
]:

    pearson = combined[column].corr(
        combined[imbalance_column],
        method="pearson"
    )

    spearman = combined[column].corr(
        combined[imbalance_column],
        method="spearman"
    )

print()
print("Correlations")
print("-----------------------------------------------")

for direction, column in [
    ("Upward", upward_column),
    ("Downward", downward_column)
]:
    pearson = combined[column].corr(
        combined[imbalance_column],
        method="pearson"
    )
    
    spearman = combined[column].corr(
        combined[imbalance_column],
        method="spearman"
    )

    print(f"{direction} aFRR:")
    print(f"  Pearson:  {pearson:.3f}")
    print(f"  Spearman: {spearman:.3f}")
    print()
# ============================================================
# LAGGED CORRELATION
# ============================================================

LAG_MINUTES = -15

# Your data has 15-minute resolution
LAG_PERIODS = LAG_MINUTES // 15

# Imbalance at time t
# compared with aFRR at time t + LAG_MINUTES

upward_corr_pearson = (
    combined[upward_column]
    .shift(-LAG_PERIODS)
    .corr(
        combined[imbalance_column],
        method="pearson"
    )
)

upward_corr_spearman = (
    combined[upward_column]
    .shift(-LAG_PERIODS)
    .corr(
        combined[imbalance_column],
        method="spearman"
    )
)

downward_corr_pearson = (
    combined[downward_column]
    .shift(-LAG_PERIODS)
    .corr(
        combined[imbalance_column],
        method="pearson"
    )
)

downward_corr_spearman = (
    combined[downward_column]
    .shift(-LAG_PERIODS)
    .corr(
        combined[imbalance_column],
        method="spearman"
    )
)

print()
print(f"Correlation with {LAG_MINUTES}-minute aFRR lag")
print("-----------------------------------------------")

print("Upward aFRR:")
print(f"  Pearson:  {upward_corr_pearson:.3f}")
print(f"  Spearman: {upward_corr_spearman:.3f}")

print("Downward aFRR:")
print(f"  Pearson:  {downward_corr_pearson:.3f}")
print(f"  Spearman: {downward_corr_spearman:.3f}")
# ============================================================
# INFORMATION
# ============================================================

print()
print("COMBINED DATA")
print("-------------")
print("Country:", COUNTRY)
print("Display timezone:", DISPLAY_TIMEZONE)
print("From:", combined["from"].iloc[0])
print("To:", combined["from"].iloc[-1])
print("Number of measurements:", len(combined))



# ============================================================
# PLOT
# ============================================================

fig, ax1 = plt.subplots(figsize=(14, 6))


# ------------------------------------------------------------
# aFRR BARS
# ------------------------------------------------------------

bar_width = 0.008

ax1.bar(
    combined["from"],
    combined[upward_column],
    width=bar_width,
    label="aFRR Upward"
)

ax1.bar(
    combined["from"],
    -combined[downward_column],
    width=bar_width,
    label="aFRR Downward"
)

ax1.axhline(
    0,
    linewidth=0.8
)

ax1.set_xlabel("Time")
ax1.set_ylabel("aFRR activation")


# ------------------------------------------------------------
# IMBALANCE LINE
# ------------------------------------------------------------

ax2 = ax1.twinx()

ax2.plot(
    combined["from"],
    combined[imbalance_column],
    label="Imbalance volume",
    linewidth=2,
    color="red"
)

ax2.set_ylabel("Imbalance volume")


# ============================================================
# ALIGN ZERO POSITIONS OF BOTH Y-AXES
# ============================================================

# Get the actual aFRR limits
y1_min, y1_max = ax1.get_ylim()

# Find the minimum and maximum imbalance values
imbalance_min = combined[imbalance_column].min()
imbalance_max = combined[imbalance_column].max()

# Add 5% headroom above and below the imbalance data
margin = 0.05

imbalance_range = imbalance_max - imbalance_min

imbalance_min_with_margin = (
    imbalance_min - imbalance_range * margin
)

imbalance_max_with_margin = (
    imbalance_max + imbalance_range * margin
)


# Position of zero on the aFRR axis
zero_position = (
    0 - y1_min
) / (
    y1_max - y1_min
)


# ------------------------------------------------------------
# Both positive and negative imbalance values
# ------------------------------------------------------------

if (
    imbalance_min_with_margin < 0
    and imbalance_max_with_margin > 0
):

    negative_limit = abs(
        imbalance_min_with_margin
    )

    positive_limit = (
        imbalance_max_with_margin
    )

    # Adjust limits so that zero has exactly the
    # same vertical position on both axes.

    negative_from_positive = (
        positive_limit
        * zero_position
        / (1 - zero_position)
    )

    positive_from_negative = (
        negative_limit
        * (1 - zero_position)
        / zero_position
    )

    negative_limit = max(
        negative_limit,
        negative_from_positive
    )

    positive_limit = max(
        positive_limit,
        positive_from_negative
    )

    ax2.set_ylim(
        -negative_limit,
        positive_limit
    )


# ------------------------------------------------------------
# Imbalance values only positive
# ------------------------------------------------------------

elif imbalance_min_with_margin >= 0:

    positive_limit = imbalance_max_with_margin

    negative_limit = (
        positive_limit
        * zero_position
        / (1 - zero_position)
    )

    ax2.set_ylim(
        -negative_limit,
        positive_limit
    )


# ------------------------------------------------------------
# Imbalance values only negative
# ------------------------------------------------------------

elif imbalance_max_with_margin <= 0:

    negative_limit = abs(
        imbalance_min_with_margin
    )

    positive_limit = (
        negative_limit
        * (1 - zero_position)
        / zero_position
    )

    ax2.set_ylim(
        -negative_limit,
        positive_limit
    )
# ------------------------------------------------------------
# HOURLY TIME LABELS
# ------------------------------------------------------------

ax1.xaxis.set_major_locator(
    mdates.HourLocator(interval=1)
)

ax1.xaxis.set_major_formatter(
    mdates.DateFormatter(
        "%H:%M",
        tz=DISPLAY_TIMEZONE
    )
)


# ------------------------------------------------------------
# COMBINED LEGEND
# ------------------------------------------------------------

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc="lower left"
)


# ------------------------------------------------------------
# TITLE
# ------------------------------------------------------------

plt.title(
    COUNTRY + "'s"
    + " aFRR activation and imbalance volume\n"
    + START_DATE
    + " → "
    + END_DATE
    + " ("
    + DISPLAY_TIMEZONE
    + ")"
)

plt.grid(True, axis="y", alpha=0.3)

fig.tight_layout()

plt.show()