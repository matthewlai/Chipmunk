#!/bin/bash

echo "UPDATE registration SET validated = 1;" | sqlite3 userdata.db
