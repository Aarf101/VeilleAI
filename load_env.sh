#!/bin/bash
# Load environment variables from .env file
# Usage: source load_env.sh

if [ -f .env ]; then
    echo "📂 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | grep -v '^\s*$' | xargs)
    
    # Check if GROQ_API_KEY is set
    if [ ! -z "$GROQ_API_KEY" ] && [ "$GROQ_API_KEY" != "gsk_your_key_here" ]; then
        echo "✅ GROQ_API_KEY loaded: ${GROQ_API_KEY:0:10}..."
    else
        echo "⚠️  GROQ_API_KEY not set or using placeholder"
        echo "   Edit .env file and add your API key from: https://console.groq.com/keys"
    fi
    
    # Check if TOGETHER_API_KEY is set
    if [ ! -z "$TOGETHER_API_KEY" ] && [ "$TOGETHER_API_KEY" != "your_together_key_here" ]; then
        echo "✅ TOGETHER_API_KEY loaded"
    fi
    
    echo ""
    echo "Environment loaded! You can now run:"
    echo "  python3 demo_groq_synthesis.py"
    echo "  python3 demo/run_collectors.py"
    echo ""
else
    echo "❌ .env file not found!"
    echo "   Copy .env.example to .env and add your API keys"
fi
