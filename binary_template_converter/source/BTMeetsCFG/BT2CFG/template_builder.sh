#!/bin/bash
# args to variables
f=/source/$1

# prepare env
cd /FormatFuzzer || exit
mkdir -p build

# apply patches
# patch -l < /source/BTMeetsCFG/BT2CFG/benchmark.patch
patch -l < /source/BTMeetsCFG/BT2CFG/hotfix.patch
echo "Patch successfully applied!"

# prepare file
echo "Processing $f file..";
name=$(basename $f)
cpp_name=$name.cpp
./ffcompile $f $cpp_name
# TODO fuzzer.o generation could be optimized, is only required once.
g++ -c -I . -std=c++17 -g -O3 -Wall fuzzer.cpp
g++ -c -I . -std=c++17 -g -O3 -Wall $cpp_name
g++ -O3 $name.o fuzzer.o -o build/$name-fuzzer -lz
rm "$name.o"
rm "$cpp_name"