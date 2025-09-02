set $dir=/mnt/filebench
set $filesize=512k
set $entries=20000
set $iosize=8k

set $findex=cvar(type=cvar-gamma,parameters=mean:1000;gamma:1.5)

define fileset name=ycsb,path=$dir,size=$filesize,prealloc,entries=$entries,dirwidth=0

define process name=filereader0,instances=1
{
  thread name=filereaderthread,memsize=10m,instances=45
  {
    flowop openfile name=openfile1,filesetname=ycsb,fd=1,indexed=$findex
    flowop readwholefile name=readfile1,fd=1,iosize=$iosize
    flowop closefile name=closefile1,fd=1
  }
}

define process name=filewriter0,instances=1
{
  thread name=filewriterthread,memsize=10m,instances=3
  {
    flowop openfile name=openfile2,filesetname=ycsb,fd=1,indexed=$findex
    flowop writewholefile name=readfile1,fd=1,iosize=$iosize
    flowop closefile name=closefile2,fd=1
  }
}

echo  "FileMicro-ReadRand Version 2.2 personality successfully loaded"
run 30
