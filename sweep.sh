#!/usr/bin/env bash
# dev: sweep one env setting over public_01 + public_02 and print the ALL rows. usage: ./sweep.sh EP_EXPLORE_SHARE 0.15
export "$1=$2"
for s in public_01_dev public_02_incidents; do
  ./rerun.sh $s 2>&1 | grep "^| ALL" | sed "s/^/$1=$2 $s /"
done
