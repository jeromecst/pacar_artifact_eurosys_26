import pandas as pd
import re
import sys


def parse_file_to_csv(file_path):
    patch_pattern = re.compile(r'^patch: (0|1)')
    bandwidth_pattern = re.compile(r'(\w+)\W+:\W+(\d+\.?\d*)\W+micros\/op\W+(\d+\.?\d*)\W+ops/sec\W+(\d+\.?\d*)\W+seconds\W+(\d+)\W+operations;\W+(\d+\.?\d*)\W*MB/s')

    current_patch = 'base'
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            patch_match = patch_pattern.match(line)
            if patch_match:
                patch = patch_match.group(1)
                current_patch = 'PaCaR' if patch == "1" else "Linux"
                continue

            bandwidth_match = bandwidth_pattern.match(line)
            if bandwidth_match:
                bench, microsop, opssec, seconds, operations, bandwidth = bandwidth_match.groups()
                exp = {
                    "patch": current_patch,
                    "benchmark": bench,
                    "ops/sec": float(opssec),
                    "seconds": float(seconds),
                    "operations": float(operations),
                    "bandwidth": float(bandwidth),
                }
                data.append(exp)

    df = pd.DataFrame(data)

    return df


if len(sys.argv) < 2:
    print("Please provide a filename.")
    sys.exit(1)

filename = sys.argv[1]
df = parse_file_to_csv(filename)

df2 = df[df['benchmark'] == 'appendrandom']

# Group by 'patch' and calculate the mean for each numerical column
df2 = df2.groupby('patch').agg({
    'benchmark': 'first',  # Keep the 'benchmark' value as it will be the same within each group
    'ops/sec': 'mean',
    'seconds': 'mean',
    'operations': 'mean',
    'bandwidth': 'mean'
}).reset_index()

df = df[df['benchmark'] != 'appendrandom']

df = pd.concat([df, df2], ignore_index=True)

base = 'Linux'
other = 'PaCaR'

# split Linux and PaCaR
linux = df[df["patch"] == "Linux"].set_index("benchmark")
pacar = df[df["patch"] == "PaCaR"].set_index("benchmark")

# only keep numeric columns
numeric_cols = ["ops/sec", "seconds", "operations", "bandwidth"]

# calculate % difference (PaCaR vs Linux)
diff_percent = (pacar[numeric_cols] - linux[numeric_cols]) / linux[numeric_cols] * 100
for col in diff_percent.columns:
    diff_percent[col] = diff_percent[col].apply(lambda x: f"{x:.2f}%")

print(diff_percent)
