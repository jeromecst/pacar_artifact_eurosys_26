#!/bin/bash -e

if [ -z "$1" ]; then
	echo specify workload
	echo fio_percentage
	echo fio_malloc
	echo filebench
	echo dbbench
	exit
fi

exp=$1
cur=$(pwd)
iter=1

ulimit -n 40000
echo never > /sys/kernel/mm/transparent_hugepage/enabled

echo 1 > /sys/kernel/mm/duplication/stats
echo 1 > /sys/kernel/mm/duplication/memory_pressure_mitigation
echo 1 > /sys/kernel/mm/duplication/switch_main_eviction

# shellcheck disable=SC2317
load_dbbench() {
	cd "$cur/rocksdb/"
	./db_bench --benchmarks=fillrandom --use_existing_db=0\
		--threads=48 --batch_size=30 --level0_file_num_compaction_trigger=4\
		--level0_slowdown_writes_trigger=20 --level0_stop_writes_trigger=30\
		--max_background_jobs=0 --max_write_buffer_number=8\
		--undefok=use_blob_cache,use_shared_block_and_blob_cache,blob_cache_size,blob_cache_numshardbits,prepopulate_blob_cache,multiread_batched,cache_low_pri_pool_ratio,prepopulate_block_cache\
		--db=/mnt/rocksdb --wal_dir=/mnt/wall --num=1000000 --key_size=20\
		--value_size=8000 --block_size=8192 --cache_size=0\
		--cache_numshardbits=6 --compression_max_dict_bytes=0\
		--compression_ratio=0.5 --compression_type=none\
		--bytes_per_sync=1048576 --benchmark_write_rate_limit=0\
		--write_buffer_size=134217728 --target_file_size_base=134217728\
		--max_bytes_for_level_base=1073741824 --verify_checksum=1\
		--delete_obsolete_files_period_micros=62914560\
		--max_bytes_for_level_multiplier=8 --statistics=0\
		--stats_per_interval=1 --stats_interval_seconds=60\
		--report_interval_seconds=1 --histogram=1 --memtablerep=skip_list\
		--bloom_bits=10 --open_files=-1 --subcompactions=0 --multiread_batched\
		--compaction_style=0 --num_levels=10 --min_level_to_compress=-1\
		--level_compaction_dynamic_level_bytes=true\
		--pin_l0_filter_and_index_blocks_in_cache=0 --duration=900\
		--seed=1742464364\
		--report_file=/tmp/benchmark_multireadrandom.t256.log.r.csv 2>&1 | tee -a /tmp/benchmark_multireadrandom.t256.log
	sync
}

# shellcheck disable=SC2317
exp_dbbench() {
	cd "$cur"/rocksdb/
	./db_bench --benchmarks=multireadrandom,stats --use_existing_db=1\
		--threads=$2 --batch_size=30 --max_background_jobs=0\
		--max_write_buffer_number=1 --db=/mnt/rocksdb --wal_dir=/mnt/wall\
		--num=1000000 --key_size=20 --value_size=8000 --block_size=8192\
		--cache_size=0 --compression_type=none --bytes_per_sync=0\
		--benchmark_write_rate_limit=0 --write_buffer_size=134217728\
		--target_file_size_base=134217728 --max_bytes_for_level_base=1073741824\
		--delete_obsolete_files_period_micros=62914560\
		--bloom_bits=20  --subcompactions=0 --multiread_batched\
		--compaction_style=0 --num_levels=10 --min_level_to_compress=-1\
		--disable_auto_compactions=1 --level_compaction_dynamic_level_bytes=true\
		--pin_l0_filter_and_index_blocks_in_cache=0 --duration=$1\
		--seed=1742464364 2>&1 
}

export COMPRESSION_TYPE=none
export WAL_DIR=/mnt/wall
export DB_DIR=/mnt/rocksdb
export NUM_KEYS=10000000
export CACHE_SIZE=0
export SUBCOMPACTIONS=0
export NUM_THREADS=48
export USE_BLOB_CACHE=0
export DURATION=30

filename="$cur/exp.tmp"
echo > "$filename"

sync
echo 1 > /proc/sys/vm/drop_caches

start=$(date)
if [ "$exp" == "fio_malloc" ] ; then
	iter=1

	printf "#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

#define NBGIB 100ul
#define NPROC 1

int main() {
	char *zone = malloc(sizeof(char *) * NPROC);
	int t, n;
	unsigned long size = NBGIB * 1024 * 1024 * 1024;
	unsigned long size_save = size;
	zone =
		mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
	if (!zone) {
		perror(\"mmap\");
		exit(1);
	}
	size = (unsigned long)((double)size / (double)NPROC);
	for (t = 0; t < NPROC; t++) {
		if (fork() == 0) {
			zone = zone + size * t;
			for (unsigned long i = 0; i < size; i += 4096) {
				zone[i] = '0';
			}
			exit(0);
		}
	}
	for (t = 0; t < NPROC; t++)
		wait(NULL);

	sleep(140);
	munmap(zone, size_save);
}

" > "$cur"/mmap.c
	gcc mmap.c

	finished=0
	for patch in 0 1; do
		for switch_main in 0 1; do
			for pressure_mitigation in 0 1; do
				for i in $(seq $iter); do
					dump=0
					if [ $patch -eq 0 ] && [ $finished -eq 1 ]; then continue; fi
					sync
					echo 1 > /proc/sys/vm/drop_caches
					echo 0 > /sys/kernel/mm/duplication/stats 
					echo $pressure_mitigation > /sys/kernel/mm/duplication/memory_pressure_mitigation
					echo $switch_main > /sys/kernel/mm/duplication/switch_main_eviction
					echo $patch > /sys/kernel/mm/duplication/enabled
					export SIZE=80g
					export RUNTIME=450
					export NUMREADER=76
					fio -f --eta=always --eta-newline=100ms --eta=interval=1 "$cur"/workloads/fio/workload_simple.fio | tee -a "$filename" &
					pid=$!
					(
						while kill -0 $pid 2>/dev/null; do
							echo "patch: $dump $i $patch $NUMREADER $SIZE" >> "$filename"
							echo "features: $pressure_mitigation $switch_main" >> "$filename"
							cat /proc/meminfo >> "$filename"
							cat /sys/kernel/mm/duplication/stats >> "$filename"
							dump=$((dump + 1))
							sleep 1
							printf "\n%s\n" dump >> "$filename"
						done
						) &
						sleep 40
						./a.out &
						wait
						if [ $patch -eq 0 ]; then finished=1; fi
					done
				done
			done
		done
	echo 1 > /sys/kernel/mm/duplication/memory_pressure_mitigation
	echo 1 > /sys/kernel/mm/duplication/switch_main_eviction
fi
if [ "$exp" == filebench ]; then
	for patch in 0 1 ; do
		for workload in webserver videoserver fileserver ycsb-a ycsb-b ycsb-c; do
		#for workload in ycsb-a ycsb-b ycsb-c ; do
			sync
			echo 0 > /sys/kernel/mm/duplication/stats 
			echo 1 > /proc/sys/vm/drop_caches
			echo $patch > /sys/kernel/mm/duplication/enabled
			echo "patch: $patch workload: $workload" | tee -a "$filename"

			# modify the workload
			cp "$cur"/workloads/filebench/$workload.f /tmp/workload.f
			sed -i 's/dir=.*/dir=\/mnt\/filebench/' /tmp/workload.f
			sed -i '/run .*/d' /tmp/workload.f
			echo run 600 >> /tmp/workload.f
			setarch -R -- "$cur"/filebench/filebench -f /tmp/workload.f | tee -a "$filename"
			cat /sys/kernel/mm/duplication/stats >> "$filename"
			echo "done" | tee -a "$filename"
		done
	done
fi
if [ "$exp" == dbbench_local_vs_distant ]; then
	#load_$exp 
	for i in $(seq 1); do
		for local in 0 1; do
			sync
			echo 1 > /proc/sys/vm/drop_caches
			echo 0 > /sys/kernel/mm/duplication/stats

			echo 0 > /sys/kernel/mm/duplication/enabled

			if [ $local -eq 0 ]; then
				find /mnt/rocksdb/ -type f -print0 | xargs -I {} -0 -P24 numactl -N 1 cat "{}" >/dev/null
			else
				find /mnt/rocksdb/ -type f -print0 | xargs -I {} -0 -P24 numactl -N 0 cat "{}" >/dev/null
			fi

			echo "patch: $patch iter: $i" | tee -a "$filename"
			numactl -N 1 bash -c "$(declare -f exp_dbbench_manual); exp_dbbench_manual 60 24" | grep -v finished  | tee -a "$filename"
			< /sys/kernel/mm/duplication/stats tee -a "$filename"
		done
	done
	echo 1 > /proc/sys/kernel/numa_balancing
fi
if [ "$exp" == dbbench ]; then
	mkdir -p /mnt/rocksdb
	"load_$exp"
	for i in $(seq 1); do
		for patch in 0 1; do
			sync
			echo 1 > /proc/sys/vm/drop_caches
			echo 0 > /sys/kernel/mm/duplication/stats

			echo $patch > /sys/kernel/mm/duplication/enabled


			find /mnt/rocksdb/ -type f -print0 | xargs -I {} -0 -P24 numactl -N 0 cat "{}" >/dev/null
			find /mnt/rocksdb/ -type f -print0 | xargs -I {} -0 -P24 numactl -N 1 cat "{}" >/dev/null

			echo "patch: $patch iter: $i" | tee -a "$filename"
			exp_"$exp" 300 48 | grep -v finished  | tee -a "$filename"
			< /sys/kernel/mm/duplication/stats tee -a "$filename"
		done
	done
	echo 1 > /proc/sys/kernel/numa_balancing
fi
if [ "$exp" == fio_percentage ]; then
	export RUNTIME=20

	for iter in $(seq 8); do
		for patch in 1 0; do
			echo $patch > /sys/kernel/mm/duplication/enabled
			for i in $(seq 0 5 90) $(seq 92 2 100); do
				nbread=$i
				nbwrite=$((100 - i))
				export NUMREADER=$nbread
				export NUMWRITER=$nbwrite
				export SIZE=40g
				echo "patch: $iter $patch $nbread $nbwrite" | tee -a "$filename"
				echo 0 > /sys/kernel/mm/duplication/stats
				if [ "$i" -eq 0 ]; then
					perf stat -o "$filename" --append -e node-loads,node-load-misses -- fio -f "$cur"/workloads/fio/workload_rwonly.f | tee -a "$filename"
				elif [ "$i" -eq 100 ]; then
					perf stat -o "$filename" --append -e node-loads,node-load-misses -- fio -f "$cur"/workloads/fio/workload_rdonly.f | tee -a "$filename"
				else
					perf stat -o "$filename" --append -e node-loads,node-load-misses -- fio -f "$cur"/workloads/fio/workload_optimized.fio | tee -a "$filename"
				fi
				< /sys/kernel/mm/duplication/stats tee -a "$filename"
			done
		done
	done
fi
end=$(date)
dir="$cur/exp_results/"
mkdir -p "$dir "
filename_save="${dir}${exp}_$(date '+%F_%T')"
mv "$filename" "$filename_save"
