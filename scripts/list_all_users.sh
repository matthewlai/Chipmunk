#!/bin/bash

echo -e ".width 40 30 10 1\nSELECT name, email, unit, validated FROM registration;" | sqlite3 -column userdata.db
