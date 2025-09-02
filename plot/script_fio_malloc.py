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


def parse_file_to_csv(file_path):
    patch_pattern = re.compile(r'patch: (\d+) (\d+) (\d+) (\d+) (\d+[a-z]+)\W*')
    bandwidth_pattern = re.compile(r'Jobs:.*r=(\d+.?\d*)(M|G)iB\/s\]\[r=(\d+\.?\d*)k IOP')
    feature_pattern = re.compile(r'^features:\W*(\d+)\W*(\d+)\W*$')
    meminfo_pattern = re.compile(r'^(\w+):\W+(\d+) kB$')
    duplication_strucs_pattern = re.compile(r'^(\d+)\W+([\w+ ]+)$')
    duplication_stats_pattern = re.compile(r'^([\w+ ]+)\W+(\d+)$')
    dump_pattern = re.compile(r'dump')

    data = []
    exp = {}
    threads = 64  # default
    bandwidth = 0
    iops = 0
    multiplier = ''

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            patch_match = patch_pattern.match(line)
            if patch_match:
                dump, iteration, patch, readers, size = patch_match.groups()
                if int(iteration) == 0:
                    iops = 0
                    bandwidth = 0
                continue

            features_match = feature_pattern.match(line)
            if features_match:
                pressure_mitigation, switch_main = features_match.groups()
                switch_main = switch_main == "1"
                pressure_mitigation = pressure_mitigation == "1"
                if switch_main and not pressure_mitigation:
                    feature = "Switch Main"
                elif not switch_main and pressure_mitigation:
                    feature = "Pressure Mitigation"
                elif not switch_main and not pressure_mitigation:
                    feature = "None"
                else:
                    feature = "Switch + Mitigations"

                continue

            meminfo_match = meminfo_pattern.match(line)
            if meminfo_match:
                name, value = meminfo_match.groups()
                exp[f"{name}"] = float(value) / 1024**2
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

            bandwidth_match = bandwidth_pattern.match(line)
            if bandwidth_match:
                bandwidth, multiplier, iops = bandwidth_match.groups()

            dump_match = dump_pattern.match(line)
            if dump_match:
                exp["Bandwidth (GiB/s)"] = float(bandwidth) * multipliers[multiplier] / 1024**3
                exp["IOPS (k)"] = float(iops)
                exp["Version"] = "PaCaR" if patch == "1" else "Linux"
                exp["Time (s)"] = float(dump)
                exp["size"] = size
                exp["iter"] = iteration
                exp["threads"] = threads
                exp["Feature"] = feature

                data.append(exp)
                exp = {}
                continue

    df = pd.DataFrame(data)

    return df


if len(sys.argv) < 2:
    print("Please provide a filename.")
    sys.exit(1)

filename = sys.argv[1]
df = parse_file_to_csv(filename)
print(df["Bandwidth (GiB/s)"])
print(df.columns)
df = df[df['Time (s)'] > 5]

df['Malloc (GB)'] = df['AnonPages'] + df['Shmem']
df['Cached'] -= df['Shmem']
df['Cached'] -= df['Twins']
df['total read'] = df['local read'] + df['distant read']
df['ratio local read'] = df['local read'] / df['total read']

df.loc[df['Time (s)'] < 30, 'Malloc (GB)'] = 0

df["Memory Footprint (GB)"] = df["struct duplication"] * 48 / 1024**3

plt.rcParams.update({'font.size': 24})
ax = sns.lineplot(data=df, x='Time (s)', y='Bandwidth (GiB/s)', size='Version', hue='Feature')
ax.set_ylim(0, None)
plt.legend(title='')
plt.show()

plt.rcParams.update({'font.size': 24})
ax = sns.lineplot(data=df, x='Time (s)', y='Malloc (GB)', size='Version', hue='Feature')
ax.set_ylim(0, None)
plt.legend(title='')
plt.show()

for metric in ["switch main", "migrations main", "migrations twin", "remove mapping main", "remove mapping twin"]:
    plt.rcParams.update({'font.size': 24})
    ax = sns.lineplot(data=df, x='Time (s)', y=metric, size='Version', hue='Feature')
    ax.set_ylim(0, None)
    plt.legend(title='')
    plt.show()

# sns.lineplot(data=df, x='Time (s)', y='Twins', size='duplication', hue='feature')
# sns.lineplot(data=df, x='Time (s)', y='Cached', size='duplication', hue='feature')

# ax = sns.lineplot(data=df, x='Time (s)', y='ratio local read', size='duplication', hue='feature')
# ax.set_ylim(0, None)
# plt.legend(title='')
# plt.show()

# sns.lineplot(data=df, x='Time (s)', y='Memory Footprint (GB)', size='duplication', hue='feature')

# plt.tight_layout()
# plt.show()

# vim: set textwidth=0:
