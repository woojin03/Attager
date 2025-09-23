#!/bin/bash

# ... existing code ...

# Directory containing agent card JSON files
AGENT_CARDS_DIR="/home/agents/agent_cards"

# Iterate over each JSON file in the directory and register the agent
for file in "$AGENT_CARDS_DIR"/*.json; do
  if [ -f "$file" ]; then
    echo "Registering agent from $file..."
    curl -X POST "http://localhost:8000/agents/register" \
         -H "Content-Type: application/json" \
         -d "@$file"
    echo -e "\n" # Add a newline for better readability between registrations
  fi
done

echo "All agents from $AGENT_CARDS_DIR registered."