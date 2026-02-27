#!/bin/bash
# Quick test commands for Agent Collecteur

echo "========================================================================"
echo "AGENT COLLECTEUR - TEST COMMANDS"
echo "========================================================================"

echo ""
echo "1️⃣  Pytest (Assertions)"
echo "   py -m pytest tests/test_collector.py -v"
echo ""

echo "2️⃣  Live RSS/API Collection"
echo "   py test_collector_live.py"
echo ""

echo "3️⃣  Deduplication Test (2 runs)"
echo "   py test_deduplication.py"
echo ""

echo "4️⃣  Duplicate Detection Test"
echo "   py test_duplicate_detection.py"
echo ""

echo "========================================================================"
echo "To run ALL tests:"
echo "========================================================================"
echo ""
echo "cd AgenticNotes-aarf102am"
echo "py -m pytest tests/test_collector.py -v && py test_collector_live.py && py test_deduplication.py && py test_duplicate_detection.py"
echo ""
