#!/bin/bash
# Install AgenticNotes Scheduler as a systemd service

echo "Installing AgenticNotes Scheduler Service..."

# Copy service file to systemd
sudo cp agenticnotes-scheduler.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable agenticnotes-scheduler.service

# Start service now
sudo systemctl start agenticnotes-scheduler.service

# Check status
sudo systemctl status agenticnotes-scheduler.service

echo ""
echo "✅ Scheduler installed!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status agenticnotes-scheduler   # Check status"
echo "  sudo systemctl stop agenticnotes-scheduler     # Stop scheduler"
echo "  sudo systemctl start agenticnotes-scheduler    # Start scheduler"
echo "  sudo systemctl restart agenticnotes-scheduler  # Restart scheduler"
echo "  journalctl -u agenticnotes-scheduler -f        # View logs"
