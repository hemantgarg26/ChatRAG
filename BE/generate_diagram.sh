#!/bin/bash

# Generate PNG image from Mermaid diagram
# Prerequisites: npm install -g @mermaid-js/mermaid-cli

echo "Generating SendMessage API Flow Diagram..."

# Check if mmdc (mermaid-cli) is installed
if ! command -v mmdc &> /dev/null; then
    echo "mermaid-cli is not installed. Installing..."
    npm install -g @mermaid-js/mermaid-cli
fi

# Generate PNG from markdown file
mmdc -i sendmessage_flow_diagram.md -o sendmessage_flow_diagram.png -t dark -w 2000 -H 1500

if [ $? -eq 0 ]; then
    echo "✅ Diagram generated successfully: sendmessage_flow_diagram.png"
else
    echo "❌ Failed to generate diagram. Make sure mermaid-cli is installed properly."
    echo "Install with: npm install -g @mermaid-js/mermaid-cli"
fi 