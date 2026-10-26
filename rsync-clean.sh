#!/bin/bash
# Clean rsync - excludes infected/suspicious files
rsync -avz --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.next' \
  --exclude='*.pyc' \
  --exclude='frontend/api.js' \
  --exclude='backend/app/routers/public/fonts/' \
  --exclude='*.orc' \
  --exclude='*.woff' \
  --exclude='*.woff2' \
  --exclude='*.ttf' \
  --exclude='*.eot' \
  --exclude='*.svg' \
  --exclude='.vscode/tasks.json' \
  --exclude='.vscode/settings.json' \
  /home/dipo/Projects/lxd/ root@31.97.56.15:/opt/lxd/
