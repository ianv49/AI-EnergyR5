#!/usr/bin/env python3
import csv, math
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

ml_output_file = Path("data/MLoutput.txt")
collect_file   = Path("data/collect1.txt")
ml_res_file    = Path("data/MLres1.txt")

def load_csv_skip_comments(file_path):
    with open(file_path, newline="") as f:
        lines = [line for line in f if not line.strip().startswith("#") and not line.strip().startswith("[")]
        reader = csv.DictReader(lines)
        rows = []
        for row in reader:
            clean = {k.strip(): v.strip() for k,v in row.items()}
            rows.append(clean)
        return rows, [h.strip() for h in reader.fieldnames]

def aggregate_daily(rows, schema_type):
    daily = defaultdict(list)
    for row in rows:
        date = row["timestamp"].split()[0]
        if "2025-04-01" <= date <= "2025-04-07":
            daily[date].append(row)

    results = []
    for i, date in enumerate(sorted(daily.keys()), start=1):
        rows = daily[date]
        if schema_type == "ML":
            wind_min = min(float(r["wind-min"]) for r in rows)
            wind_avg = sum(float(r["wind-avg"]) for r in rows)/len(rows)
            wind_max = max(float(r["wind-max"]) for r in rows)
            solar_min = min(float(r["solar-min"]) for r in rows)
            solar_avg = sum(float(r["solar-avg"]) for r in rows)/len(rows)
            solar_max = max(float(r["solar-max"]) for r in rows)
            source = "sim-ML"
        else:  # API
            wind_vals = [float(r["wind_speed"]) for r in rows]
            solar_vals = [float(r["irradiance"]) for r in rows]
            wind_min = min(wind_vals)
            wind_avg = sum(wind_vals)/len(wind_vals)
            wind_max = max(wind_vals)
            solar_min = min(solar_vals)
            solar_avg = sum(solar_vals)/len(solar_vals)
            solar_max = max(solar_vals)
            source = "sim-API"

        results.append({
            "id": str(i),
            "timestamp": date,
            "wind-min": f"{wind_min:.2f}",
            "wind-avg": f"{wind_avg:.2f}",
            "wind-max": f"{wind_max:.2f}",
            "solar-min": f"{solar_min:.2f}",
            "solar-avg": f"{solar_avg:.2f}",
            "solar-max": f"{solar_max:.2f}",
            "source": source
        })
    return results

def main():
    ml_data, _ = load_csv_skip_comments(ml_output_file)
    api_data, _ = load_csv_skip_comments(collect_file)

    ml_daily = aggregate_daily(ml_data, "ML")
    api_daily = aggregate_daily(api_data, "API")

    with open(ml_res_file, "w", newline="") as f:
        f.write("# ML page output last updated: 2025-03-31 23:59:59\n")
        f.write(f"# Summary: sim actual = {len(api_daily)} | sim predict = {len(ml_daily)}\n")
        f.write("[sim]\n")

        writer = csv.writer(f)
        schema = ["id","timestamp","wind-min","wind-avg","wind-max","solar-min","solar-avg","solar-max","source"]

        f.write("\n# Data-A: ML Predictions (Apr 1–7)\n")
        writer.writerow(schema)
        for row in ml_daily:
            writer.writerow([row[h] for h in schema])

        f.write("\n# Data-B: Actual API Daily Averages (Apr 1–7)\n")
        writer.writerow(schema)
        for row in api_daily:
            writer.writerow([row[h] for h in schema])

        f.write("\n# Metrics: Prediction vs Actual (Apr 1–7)\n")
        pred_map   = {r["timestamp"]: r for r in ml_daily}
        actual_map = {r["timestamp"]: r for r in api_daily}
        common_dates = sorted(set(pred_map.keys()) & set(actual_map.keys()))

        if not common_dates:
            f.write("No overlapping dates between ML predictions and API data.\n")
        else:
            y_pred = [float(pred_map[d]["wind-avg"]) for d in common_dates]
            y_true = [float(actual_map[d]["wind-avg"]) for d in common_dates]
            mae  = mean_absolute_error(y_true, y_pred)
            rmse = math.sqrt(mean_squared_error(y_true, y_pred))
            r2   = r2_score(y_true, y_pred)
            corr = np.corrcoef(y_true, y_pred)[0,1]
            f.write(f"MAE (wind-avg): {mae:.3f}\n")
            f.write(f"RMSE: {rmse:.3f}\n")
            f.write(f"R²: {r2:.3f}\n")
            f.write(f"Correlation: {corr:.3f}\n")

    print(f"✅ MLres1.txt built at {ml_res_file}")

if __name__ == "__main__":
    main()
