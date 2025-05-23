# WebSocket Task System Usage Guide

## Overview

Since I didn't want to set up additional applications, but encountered frequent unresponsiveness or deadlock issues when running long tasks with DiskCache+Background Callback,
I implemented a Task system using Threading + WebSocket to provide more stable long-running task execution and real-time progress updates.

## Architecture Features

- **Threading + WebSocket**: Tasks run in separate threads with progress pushed through WebSocket
- **Real-time Updates**: No need for polling, progress is pushed directly to clients
- **Stable & Reliable**: Avoids the multiprocess deadlock issues from Background Callbacks

## Core Components

### 1. TskMgr
- Manages lifecycle of all tasks
- Provides WebSocket server
- Handles task status and progress broadcasting

### 2. BaseTask
- Abstract task base class
- Supports progress callbacks
- Cancellable execution

### 3. TskSvc
- Bridges existing Dash app with task system

### 4. WebSocket UI
- Integrates Dash WebSocket component
- Auto-updates progress bar and status


## Testing

Run test cases:
```bash
# Unit tests
python tests/test_tsk.py

# UI integration tests
python tests/test_tsk_integration.py
```
