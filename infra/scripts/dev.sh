#!/bin/bash

# This script provides instructions for local development.
# Since the environment doesn't support multiple terminal tabs easily,
# run these in separate sessions or backgrounds.

echo "To start the Web application:"
echo "cd apps/web && pnpm dev"
echo ""
echo "To start the Orchestrator service:"
echo "cd apps/orchestrator && ./run.sh"
echo ""
echo "To start the Executor service:"
echo "cd apps/executor && ./run.sh"
echo ""
echo "Make sure to set up your .env file in the root first!"
