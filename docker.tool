#!/bin/bash
[ -f .bash_cmd.tmp ] && rm .bash_cmd.tmp
./utils/dockertool.py $@
[ -f .bash_cmd.tmp ] && ./.bash_cmd.tmp



