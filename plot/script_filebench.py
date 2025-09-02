#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import re

multipliers = {
    '': 0,
    'K': 1024,
    'k': 1024,
    'M': 1024**2,
    'm': 1024**2,
    'G': 1024**3,
    'g': 1024**3,
    'T': 1024**4,
    't': 1024**4,
}

linux = "Linux"
pacar = "PaCaR"


def parse_file_to_csv(file_path):
    patch_pattern = re.compile(r'^patch: (\d) workload: (\w+-?\w*)$')
    iosummary_pattern = re.compile(r'.*IO Summary:\s+(\d+)\s+ops\s+(\d+.?\d*)\s+ops\/s\s+(\d+)\/(\d+)\s+rd\/wr\s+(\d+.?\d*)mb\/s\s+(\d+\.?\d*)ms\/op$')
    duplication_strucs_pattern = re.compile(r'^(\d+)\W+([\w+ ]+)$')
    duplication_stats_pattern = re.compile(r'^([\w+ ]+)\W+(\d+)$')

    data = []
    exp = {}
    bandwidth = 0

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            patch_match = patch_pattern.match(line)
            if patch_match:
                patch, workload = patch_match.groups()
                continue

            iosummary_match = iosummary_pattern.match(line)
            if iosummary_match:
                ops, opssec, rd, wr, bandwidth, latency = iosummary_match.groups()
                continue

            dstruct_match = duplication_strucs_pattern.match(line)
            if dstruct_match:
                value, metric = dstruct_match.groups()
                exp[metric] = int(value)
                continue

            dstats_match = duplication_stats_pattern.match(line)
            if dstats_match:
                metric, value = dstats_match.groups()
                exp[metric] = int(value)
                continue

            if line == "done":
                exp["Version"] = pacar if patch == "1" else linux
                exp["Workload"] = workload
                exp["Operations"] = int(ops)
                exp["Operations/s"] = float(opssec)
                exp["Reads"] = int(rd)
                exp["Writes"] = int(wr)
                exp["Bandwidth (GB/s)"] = float(bandwidth) / 1024
                exp["Latency (ms)"] = float(latency)
                data.append(exp)
                exp = {}

    df = pd.DataFrame(data)

    return df


if len(sys.argv) < 2:
    print("Please provide a filename.")
    sys.exit(1)

filename = sys.argv[1]
df = parse_file_to_csv(filename)
print(df)
df["Ratio Local Read"] = df["local read"] / (df["local read"] + df["distant read"])
df["Ratio Local Write"] = df["local write"] / (df["local write"] + df["distant write"])
df["Ratio r/w"] = df["Reads"] / (df["Reads"] + df["Writes"])
# print(df.columns)

skiplist = ["webproxy", "oltp", "varmail"]
for skip in skiplist:
    df = df[df['Workload'] != skip]

plt.rcParams.update({'font.size': 24})
g = sns.catplot(
    data=df, kind="bar",
    x="Workload", y="Bandwidth (GB/s)", hue="Version",
    hue_order=[linux, pacar]
)
g._legend.remove()
plt.legend(title=None, loc='upper right')
plt.show()

g = sns.catplot(
    data=df, kind="bar",
    x="Workload", y="Latency (ms)", hue="Version",
    hue_order=[linux, pacar]
)
g._legend.remove()
plt.legend(title=None, loc='upper right')

plt.show()


g = sns.catplot(
    data=df, kind="bar",
    x="Workload", y="Operations/s", hue="Version",
    hue_order=[linux, pacar]
)
g._legend.remove()
plt.legend(title=None, loc='upper right')
plt.show()

print(df.groupby('Workload')['Ratio r/w'].mean())

# g = sns.catplot(
#     data=df, kind="bar",
#     x="Workload", y="Ratio r/w"
# )
# plt.show()

# vim: set textwidth=0:
