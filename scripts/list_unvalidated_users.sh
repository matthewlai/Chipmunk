#!/bin/bash

echo -e ".width 40 30 10 1\nSELECT name, email, unit, validated FROM registration WHERE validated = 0;" | sqlite3 -column userdata.db
