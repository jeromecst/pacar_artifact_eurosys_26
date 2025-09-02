Artifact Eurosys'26
-------------------

This is the artifact for the paper "PaCaR: Improved Buffered I/O Locality on NUMA Systems with Page Cache Replication".

**Requirement**: Debian 12 with an XFS root filesystem. A tutorial to install Debian with XFS can be found [here](./pdf/tutorial_debian_xfs.pdf).

**Hardware requirement**: These experiments are scaled for a 2-nodes NUMA system with 2x24 threads and 256 GB ram, and about 200 GB disk space. Feel free to modify the workloads to match your hardware specs.

You can setup the machine with the script `pacar_setup.sh`. This will fetch Linux sources, apply the PaCaR patch, compile, and install RocksDB and filebench.

Setup
-----

```sh
git clone https://github.com/jeromecst/pacar_artifact_eurosys_26
cd pacar_artifact_eurosys_26
./pacar_setup.sh
```

Reboot on Linux with PaCaR
--------------------------

PaCaR should now be installed on the system, now is a good time to reboot with `kexec`.

```sh
version=6.12.20
# Reboot on the new kernel
kexec -l /boot/vmlinuz-$version --initrd /boot/initrd.img-$version --reuse-cmdline
kexec -e
```

Before running experiments, verify that PaCaR is correct installed on the system:

```sh
$ ls /sys/kernel/mm/duplication/
dump  enabled  memory_pressure_mitigation  stats  switch_main_eviction  threshold
```

Run experiments
---------------

In order to run the experiment and generate the figures of the paper, follow this:

```sh
# for each experiment, run and plot the results with these commands
# E1
./run_exp fio_percentage
./plot/script_fio_percentages.py exp_results/fio_percentage_XXXX-XX-XX_XX:XX:XX

# E2
./run_exp fio_malloc
./plot/script_fio_malloc.py exp_results/fio_malloc_XXXX-XX-XX_XX:XX:XX

# E3
./run_exp filebench
./plot/script_filebench.py exp_results/filebench-XX-XX_XX:XX:XX

# E4
./run_exp dbbench
## work in progress
./plot/script_dbbench.py exp_results/dbbench-XX-XX_XX:XX:XX
```
