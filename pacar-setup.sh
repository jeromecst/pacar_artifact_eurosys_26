#!/bin/sh -e

# Install PaCaR, RocksDB and Filebench on a Debian system

version=6.12.20
proc=$(nproc)

apt install wget tar xz-utils kexec-tools bc make gcc g++ patch flex bison libelf-dev libssl-dev numactl git libtool automake fio linux-perf libgflags-dev python3-numpy python3-seaborn python3-pandas python3-matplotlib coreutils

install_pacar() {
	if ! [ -d "linux-$version.tar.xz" ]; then
		wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-$version.tar.xz
	fi
	rm linux-6.12.20/ -fr
	tar xf linux-$version.tar.xz
	cd linux-6.12.20
	patch -p1 < ../PaCaR/PaCaR.patch
	cp ../PaCaR/kernel_config .config
	make -j"$proc"
	make modules_install install -j"$proc"
	cd -
}

install_filebench() {
	if ! [ -d filebench/ ] ; then
		git clone https://github.com/filebench/filebench
	fi
	cd filebench || return
	git checkout 22620e602cbbebad90c
	libtoolize
	aclocal
	autoheader
	automake --add-missing
	autoconf

	./configure
	make -j"$proc"
	cd -
}

install_rocksdb() {
	if ! [ -d rocksdb/ ]; then
		git clone https://github.com/facebook/rocksdb
	fi
	cd rocksdb || return
	git checkout v9.10.0
	DISABLE_WARNING_AS_ERROR=1 make -j"$proc" db_bench static_lib
	cd -
}

install_pacar
install_filebench
install_rocksdb
