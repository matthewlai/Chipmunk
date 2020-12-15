#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <email>"
fi

echo "DELETE FROM registration WHERE email='$1';" | sqlite3 userdata.db
