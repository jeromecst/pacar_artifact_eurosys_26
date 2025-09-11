Artifact Eurosys'26
-------------------

This is the artifact for the paper "PaCaR: Improved Buffered I/O Locality on NUMA Systems with Page Cache Replication".

**Requirement**: Debian 12 or Debian 13 with an XFS root filesystem. A tutorial to install Debian with XFS can be found [here](pdf/tutorial_debian_xfs.pdf)

**Hardware requirement**: These experiments are scaled for a 2-nodes NUMA system. It has been tested on 2x24 threads and 256 GB ram, but most of the experiment are scaling automatically depending on your configuration. 
1 TB disk space is required. 

This artifact contains the following components:

```
📦 Artifact
├── 🧩 PaCaR
│   ├── 🧵 PaCaR.patch
│   └── ⚙️ kernel_config
├── 📊 plot
│   └── 📜 Scripts for figures & tables (paper)
├── 🧪 workloads
│   ├── 💾 fio_workloads/
│   └── 📂 filebench_workloads/
├── 📁 exp_results (generated folder)
│   └── 📑 Outputs from experiments
├── 📥 pacar-setup.sh   (install PaCaR)
└── 🚀 run_exp.sh       (run benchmarks)
```

Setup
-----

You can setup the machine with the script `pacar-setup.sh`. 
It will download dependencies, fetch Linux sources, apply the PaCaR patch, compile, and install RocksDB and filebench.

```sh
git clone https://github.com/jeromecst/pacar_artifact_eurosys_26
cd pacar_artifact_eurosys_26
sudo ./pacar-setup.sh
```

Reboot on Linux with PaCaR
--------------------------

PaCaR should now be installed on the system, now is a good time to reboot with `kexec`.

```sh
version=6.12.20
# Reboot on the new kernel
sudo kexec -l /boot/vmlinuz-$version --initrd /boot/initrd.img-$version --reuse-cmdline
sudo kexec -e
```

Before running experiments, verify that PaCaR is correctly installed on the system:

```sh
$ ls /sys/kernel/mm/duplication/
dump  enabled  memory_pressure_mitigation  stats  switch_main_eviction  threshold
```

Run experiments
---------------

In order to run the experiment and generate the figures of the paper, follow this.
The appropriate python packages should be already installed using the script `pacar-setup.sh`

```sh
# for each experiment, run and plot the results with these commands
# each experiment is described in the section Artifact of the paper

# E1 (40GB, 50 compute-minutes): this produces figure 4
# Warning: this benchmark doesn't scale well if your system has more than 100 threads
sudo ./run_exp.sh fio_percentage
python3 ./plot/script_fio_percentages.py exp_results/fio_percentage_XXXX-XX-XX_XX:XX:XX

# E2 (80GB, 2 compute-hours): this produces figure 5
sudo ./run_exp.sh fio_malloc
python3 ./plot/script_fio_malloc.py exp_results/fio_malloc_XXXX-XX-XX_XX:XX:XX

# E3 (120 GB, 2.4 compute-hours): this produces figure 6
sudo ./run_exp.sh filebench
python3 ./plot/script_filebench.py exp_results/filebench-XX-XX_XX:XX:XX

# E4 (500 GB, 70 compute-minutes): this produces table 2
sudo ./run_exp.sh dbbench
python3 ./plot/script_dbbench.py exp_results/dbbench-XX-XX_XX:XX:XX
```

Auxiliary Information
---------------------

1. The number of occurrence of NUMA in commits, referenced in the introduction of the paper, can be obtained with this command:

```sh
for year in {2005..2025}; do echo -n "$year: " ; git log --since="$year-01-01" --until="$year-12-31" --grep="NUMA" --oneline | wc -l ; done
```

2. The Table 1 cannot be easily generated, we reserved a bunch of NUMA machines
   on [Grid5000](https://www.grid5000.fr/w/Hardware) and ran [Intel MLC](https://www.intel.de/content/www/de/de/download/736633/intel-memory-latency-checker-intel-mlc.html) to fetch latency and bandwidth.

