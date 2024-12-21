#!/bin/bash

if [ ! -f .env.example ]; then
    echo ".env.example not found! Ensure it exists in the current directory."
    exit 1
fi

if [ -f .env ]; then
    echo ".env already exists! Do you want to overwrite it? (y/n)"
    read answer
    if [ "$answer" != "y" ]; then
        echo "Operation cancelled."
        exit 0
    fi
fi

cp .env.example .env
echo "Edit .env to provide your environment-specific values."
