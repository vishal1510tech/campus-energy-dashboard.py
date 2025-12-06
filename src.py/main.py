
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from models import Building, MeterReading, BuildingManager

DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data(data_dir: Path) -> pd.DataFrame:
    all_rows = []
    for csv_file in data_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
        except FileNotFoundError:
            print(f"Missing file: {csv_file}")
            continue
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue

        
        if "timestamp" not in df or "kwh" not in df:
            print(f"Skipping {csv_file}: required columns missing")
            continue

        
        if "building" not in df:
            df["building"] = csv_file.stem  #

        
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp", "kwh"])

        all_rows.append(df)

    if not all_rows:
        raise ValueError("No valid CSV files found in data/")

    df_combined = pd.concat(all_rows, ignore_index=True)
    return df_combined



def calculate_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index("timestamp").sort_index()
    daily = df.resample("D")["kwh"].sum().reset_index()
    return daily

def calculate_weekly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index("timestamp").sort_index()
    weekly = df.resample("W")["kwh"].sum().reset_index()
    return weekly

def building_wise_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("building")["kwh"]
        .agg(["mean", "min", "max", "sum"])
        .rename(columns={"sum": "total"})
        .reset_index()
    )
    return summary



def create_dashboard(daily: pd.DataFrame,
                     weekly: pd.DataFrame,
                     df: pd.DataFrame,
                     building_summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))


    for bld, g in df.groupby("building"):
        g2 = g.set_index("timestamp").resample("D")["kwh"].sum()
        axes[0].plot(g2.index, g2.values, label=bld)
    axes[0].set_title("Daily Consumption per Building")
    axes[0].set_ylabel("kWh")
    axes[0].legend()


    weekly_bld = (
        df.set_index("timestamp")
          .groupby("building")["kwh"]
          .resample("W").sum()
          .groupby("building").mean()
    )
    axes[1].bar(weekly_bld.index, weekly_bld.values)
    axes[1].set_title("Average Weekly Usage per Building")
    axes[1].set_ylabel("kWh")
    axes[1].set_xticklabels(weekly_bld.index, rotation=45)

    
    df["hour"] = df["timestamp"].dt.hour
    peak = df.groupby(["building", "hour"])["kwh"].max().reset_index()
    scatter = axes[2].scatter(
        peak["hour"], peak["kwh"], c=peak["hour"], cmap="viridis"
    )
    axes[2].set_title("Peak-hour Consumption")
    axes[2].set_xlabel("Hour of Day")
    axes[2].set_ylabel("kWh")
    fig.colorbar(scatter, ax=axes[2], label="Hour")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "dashboard.png")


def save_outputs(df: pd.DataFrame,
                 building_summary: pd.DataFrame,
                 daily: pd.DataFrame,
                 weekly: pd.DataFrame) -> None:
    cleaned_path = OUTPUT_DIR / "cleaned_energy_data.csv"
    summary_path = OUTPUT_DIR / "building_summary.csv"
    report_path = OUTPUT_DIR / "summary.txt"

    df.to_csv(cleaned_path, index=False)
    building_summary.to_csv(summary_path, index=False)

    total_campus = df["kwh"].sum()
    highest_bld_row = building_summary.sort_values("total", ascending=False).iloc[0]
    highest_bld = highest_bld_row["building"]
    peak_time = df.loc[df["kwh"].idxmax(), "timestamp"]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Total campus consumption: {total_campus:.2f} kWh\n")
        f.write(f"Highest-consuming building: {highest_bld}\n")
        f.write(f"Peak load time: {peak_time}\n")
        f.write("Daily trend: see dashboard.png and cleaned_energy_data.csv\n")
        f.write("Weekly trend: see dashboard.png and building_summary.csv\n")



def main():
    df = load_data(DATA_DIR)

    daily = calculate_daily_totals(df)
    weekly = calculate_weekly_aggregates(df)
    bld_summary = building_wise_summary(df)


    manager = BuildingManager()
    for _, row in df.iterrows():
        manager.add_reading(
            row["building"],
            MeterReading(timestamp=row["timestamp"], kwh=row["kwh"])
        )

    
    for building in manager.buildings.values():
        print(building.generate_report())

    
    create_dashboard(daily, weekly, df, bld_summary)
    save_outputs(df, bld_summary, daily, weekly)

if __name__ == "__main__":
    main()
