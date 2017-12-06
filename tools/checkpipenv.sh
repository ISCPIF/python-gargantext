#!/usr/bin/env bash

[ -n "$PIPENV_ACTIVE" -o "$_" = "$(type -p pipenv)" ] || \
    ( echo "Please run this with pipenv run or in pipenv shell." && exit 1 )
