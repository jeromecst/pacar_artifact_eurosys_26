#!/bin/sh -e

# Install PaCaR, RocksDB and Filebench on a Debian system

version=6.12.20

apt install wget tar xz-utils kexec-tools bc make gcc g++ patch flex bison libelf-dev libssl-dev numactl git libtool automake fio linux-perf libgflags-dev

install_pacar() {
	wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-$version.tar.xz
	tar xf linux-$version.tar.xz
	cd linux-6.12.20
	patch -p1 < ../PaCaR/PaCaR.patch
	cp ../PaCaR/kernel_config .config
	make -j24
	make modules_install install -j24
	cd -
}

install_filebench() {
	git clone https://github.com/filebench/filebench
	cd filebench
	git checkout 22620e602cbbebad90c
	libtoolize
	aclocal
	autoheader
	automake --add-missing
	autoconf

	./configure
	make -j24
	cd -
}

install_rocksdb() {
	git clone https://github.com/facebook/rocksdb
	cd rocksdb || exit
	git checkout v9.10.0
	make -j24 db_bench static_lib
	cd -
}

install_pacar
install_filebench
install_rocksdb
