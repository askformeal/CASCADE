# Notify

Notifies are messages sent from the backend to frontends.

Notifies will be buffered in the backend until a request from a notify-supported frontend is received, and then all the buffered notifies will be included in the response to that request.

Currently, there are **TWO** notify-supported frontends.

## CLI

If notifies are received in the response of a CLI command, they will be shown in the terminal output.

## GUI

Unlike the CLI, the GUI polls the backend continuously and will receive notifies in near real-time, and will show them in a pop-up window.
