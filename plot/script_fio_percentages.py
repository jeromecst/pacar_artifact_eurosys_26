#!/usr/bin/env python3
import pandas as pd
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import re

linux = "Linux"
pacar = "PaCaR"


def parse_file_to_csv(file_path):
    patch_pattern = re.compile(r"^patch\: (\d+) (\d) (\d+) (\d+)$")
    bandwidth_pattern = re.compile(r"^\s*(READ|WRITE):\s+bw=(\d+.?\d+)(G|M)iB")
    duplication_strucs_pattern = re.compile(r'^(\d+)\W+([\w+ ]+)$')
    duplication_stats_pattern = re.compile(r'^([\w+ ]+)\W+(\d+)$')
    perf_pattern = re.compile(r'((?:\d+,?)+)\W+(node-loads|node-load-misses)')

    current_patch = "base"
    read_percentage = 0
    nb_read = 0
    nb_write = 0
    readbw = 0
    writebw = 0
    data = []
    exp = {}

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            patch_match = patch_pattern.match(line)
            if patch_match:
                iter, current_patch, nb_read, nb_write = patch_match.groups()
                current_patch = pacar if current_patch == "1" else linux
                read_percentage = int(100 * int(nb_read) / (int(nb_write) + int(nb_read)))
                exp["read percentage"] = read_percentage
                exp["patch"] = current_patch
                exp["iter"] = iter
                continue

            bandwidth_match = bandwidth_pattern.match(line)

            if bandwidth_match:
                operation_type, bandwidth_value, multiplier = bandwidth_match.groups()
                bandwidth_value = float(bandwidth_value)
                if multiplier == "M":
                    bandwidth_value /= 1024
                if operation_type == "READ":
                    readbw = bandwidth_value
                else:
                    writebw = bandwidth_value

                continue

            dstruct_match = duplication_strucs_pattern.match(line)
            if dstruct_match:
                value, metric = dstruct_match.groups()
                exp[metric] = int(value)
                continue

            perf_match = perf_pattern.match(line)
            if perf_match:
                value, metric = perf_match.groups()
                exp[metric] = int(value.replace(",", ""))
                continue

            dstats_match = duplication_stats_pattern.match(line)
            if dstats_match:
                metric, value = dstats_match.groups()
                exp[metric] = int(value)
                if metric == "distant write":
                    exp["bandwidth (GiB/s)"] = readbw
                    exp["operation"] = "read"
                    data.append(exp.copy())
                    exp["bandwidth (GiB/s)"] = writebw
                    exp["operation"] = "write"
                    data.append(exp.copy())
                    readbw = 0
                    writebw = 0
                    exp = {}
                else:
                    continue

    df = pd.DataFrame(data)

    return df


if len(sys.argv) < 2:
    print("Usage: python script.py <first_parameter>")
    sys.exit(1)
filename = sys.argv[1]


df = parse_file_to_csv(filename)

pd.set_option('display.max_columns', None)
print(df)

df["total read"] = df["local read"] + df["distant read"]
df["total write"] = df["local write"] + df["distant write"]
df["ratio local read"] = df["local read"] / df["total read"]
df["ratio local write"] = df["local write"] / df["total write"]
df['ratio local'] = df.apply(lambda row: row['ratio local read'] if row['operation'] == 'read' else row['ratio local write'], axis=1)
df['ratio local memory accesses'] = df["node-loads"] / (df["node-loads"] + df["node-load-misses"])

plt.rcParams.update({'font.size': 24})
ax = sns.barplot(data=df[df["operation"] == "read"], x='read percentage', y='bandwidth (GiB/s)', hue='patch', hue_order=[linux, pacar])
ax.set(ylabel='read bandwidth (GiB/s)')
plt.legend(title='')
plt.show()
ax = sns.barplot(data=df[df["operation"] == "write"], x='read percentage', y='bandwidth (GiB/s)', hue='patch', hue_order=[linux, pacar])
ax.set(ylabel='write bandwidth (GiB/s)')
plt.legend(title='')
plt.show()
sns.barplot(data=df, x='read percentage', y='ratio local memory accesses', hue='patch', hue_order=[linux, pacar])
plt.legend(title='')
plt.show()
# sns.catplot(data=df, kind='bar', x='operation', y='ratio local', hue='patch')
# plt.tight_layout()

# vim: set textwidth=0:
