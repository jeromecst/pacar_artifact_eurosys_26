import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re


def parse_file_to_csv(file_path):
    patch_pattern = re.compile(r'^(no patch|patch)$')
    bandwidth_pattern = re.compile(r'^(\w+).+ (\d+\.?\d*) MB\/s.*$')

    current_patch = 'base'
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            patch_match = patch_pattern.match(line)
            if patch_match:
                current_patch = 'duplication' if line == 'patch' else 'base'
                continue

            bandwidth_match = bandwidth_pattern.match(line)
            if bandwidth_match:
                operation_type, bandwidth_value = bandwidth_match.groups()
                operation_type = bandwidth_match.group(1)
                bandwidth_value = bandwidth_match.group(2)
                if (operation_type == 'fillseq'):
                    continue
                data.append([current_patch, float(bandwidth_value), operation_type])

    df = pd.DataFrame(data, columns=['patch', 'bandwidth (MB/s)', 'operation'])

    return df


a = parse_file_to_csv("dbbench")
sns.catplot(data=a, kind='bar', x='operation', y='bandwidth (MB/s)', hue='patch')
plt.show()
