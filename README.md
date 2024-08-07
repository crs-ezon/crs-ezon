## Hi there 👋
# CRS Automate

## Overview

This repository contains systemd service and timer configurations for automating the execution of the CRS module on a Raspberry Pi. The setup includes:

- A systemd service unit to run the CRS Python module.
- Timers to start and stop the CRS service at specified times.
- Service units for enabling and disabling the CRS service via timers.

## Files

### `crs_automate.service`

This is a systemd service unit file that defines how to execute the CRS module:

- **Description**: Execution of CRS module on boot.
- **ExecStart**: Executes the Python script located at `/home/pi/Desktop/CRS/module.py`.
- **WorkingDirectory**: Sets the working directory to `/home/pi/Desktop/CRS`.
- **User/Group**: Runs the service under the `pi` user and group.
- **Restart**: Configured to restart on failure.
- **StandardOutput/StandardError**: Logs output and errors to both journal and console.

### `crs_automate_start.timer`

This is a systemd timer unit file to start the CRS service at 08:30 AM daily:

- **Description**: Start `crs_automate.service` at 08:30 AM daily.
- **OnCalendar**: Configured to trigger at 08:30 AM every day.
- **Persistent**: Ensures the timer triggers even if the system was off during the scheduled time.

### `crs_automate_stop.timer`

This is a systemd timer unit file to stop the CRS service at 04:30 PM daily:

- **Description**: Stop `crs_automate.service` at 04:30 PM daily.
- **OnCalendar**: Configured to trigger at 04:30 PM every day.
- **Persistent**: Ensures the timer triggers even if the system was off during the scheduled time.

### `crs_automate_start.service`

This systemd service unit file is used to enable and start the CRS service:

- **Description**: Start `crs_automate.service`.
- **ExecStart**: Enables and starts `crs_automate.service`.

### `crs_automate_stop.service`

This systemd service unit file is used to stop and disable the CRS service:

- **Description**: Stop `crs_automate.service`.
- **ExecStart**: Stops and disables `crs_automate.service`.

## Installation

1. **Copy the files to the appropriate directories**:
   ```sh
   sudo cp crs_automate.service /lib/systemd/system/
   sudo cp crs_automate_start.timer /lib/systemd/system/
   sudo cp crs_automate_stop.timer /lib/systemd/system/
   sudo cp crs_automate_start.service /lib/systemd/system/
   sudo cp crs_automate_stop.service /lib/systemd/system/

<!--
**crs-ezon/crs-ezon** is a ✨ _special_ ✨ repository because its `README.md` (this file) appears on your GitHub profile.

Here are some ideas to get you started:

- 🔭 I’m currently working on ...
- 🌱 I’m currently learning ...
- 👯 I’m looking to collaborate on ...
- 🤔 I’m looking for help with ...
- 💬 Ask me about ...
- 📫 How to reach me: ...
- 😄 Pronouns: ...
- ⚡ Fun fact: ...
-->
