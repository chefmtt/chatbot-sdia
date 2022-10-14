#!/usr/bin/env bash
pushd hooks/
chmod u+x pre-push post-merge
popd
rsync -avh hooks/ .git/hooks/
