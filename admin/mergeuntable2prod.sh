#!/bin/bash

git checkout unstable

git checkout testing
git merge unstable

git checkout prod-dev
git merge testing

git checkout prod
git merge prod-dev

git checkout unstable

echo "Push ? (yes)"

read y

if [[ $y == "yes" ]]; then
	echo "je push"
	git push origin prod prod-dev testing unstable
fi
