#!/bin/bash
# bot.sh - Helper script to manage the Kalshi Trading Bot on the server

SESSION_NAME="kalshi"

# Determine the absolute path of the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

BOT_COMMAND="source .venv/bin/activate && python tests/test_strategy.py"

case "$1" in
    start)
        tmux has-session -t $SESSION_NAME 2>/dev/null
        if [ $? == 0 ]; then
            echo "Bot is already running in a background session named '$SESSION_NAME'."
            echo "Use './bot.sh logs' to view it."
        else
            echo "Starting bot in background session..."
            # Create a detached session running the bot
            tmux new-session -d -s $SESSION_NAME "bash -c '$BOT_COMMAND; exec bash'"
            echo "Bot started successfully! Use './bot.sh logs' to watch the live output."
        fi
        ;;
    stop)
        tmux has-session -t $SESSION_NAME 2>/dev/null
        if [ $? == 0 ]; then
            echo "Stopping bot safely (sending interrupt to trigger Kill Switch)..."
            # Send Ctrl+C to trigger the graceful Python exit and cancel orders
            tmux send-keys -t $SESSION_NAME C-c
            echo "Waiting for Kill Switch to safely cancel orders..."
            sleep 4
            tmux kill-session -t $SESSION_NAME 2>/dev/null
            echo "Bot stopped safely and session closed."
        else
            echo "Bot is not currently running."
        fi
        ;;
    logs)
        tmux has-session -t $SESSION_NAME 2>/dev/null
        if [ $? == 0 ]; then
            echo "Attaching to live logs..."
            echo ">>> IMPORTANT: Press Ctrl+B, then let go, then press D to safely exit without stopping the bot! <<<"
            sleep 2
            tmux attach -t $SESSION_NAME
        else
            echo "Bot is not currently running."
        fi
        ;;
    status)
        tmux has-session -t $SESSION_NAME 2>/dev/null
        if [ $? == 0 ]; then
            echo "Status: RUNNING"
        else
            echo "Status: STOPPED"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Kalshi Bot Management Framework"
        echo "Usage: ./bot.sh {start|stop|restart|status|logs}"
        exit 1
esac
