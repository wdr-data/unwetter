#!/usr/bin/env bash
pipenv lock --requirements > requirements.txt
pipenv lock --dev --requirements > requirements-dev.txt
