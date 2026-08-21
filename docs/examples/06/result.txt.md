# Result

Source file: `result.txt`

```text
PS ~\abb-rws-client-python-rw6> pixi run -e examples python examples/06/subscription.py
[main] Connected to 192.168.125.1:80
[main] Watching ['value1', 'value2']
[main] Start RAPID execution (PP to Main + Start) if not already running.
[main] Press Ctrl+C to stop.

17:59:27 [INFO    ] abb_rws_client_python_rw6.abb_rws_client_python_rw6.highlevel.subscription — Creating subscription on 2 resource(s)
17:59:27 [INFO    ] abb_rws_client_python_rw6.abb_rws_client_python_rw6.highlevel.subscription — Subscription created: group_id=14, ws_url=ws://192.168.125.1:80/poll/14
[event] value1 = 6
[event] value2 = 1
17:59:27 [INFO    ] abb_rws_client_python_rw6.abb_rws_client_python_rw6.highlevel.subscription — WebSocket connected: ws://192.168.125.1:80/poll/14
[event] value1 = 7
[event] value2 = 2
[event] value1 = 8
[event] value2 = 3
[event] value1 = 9
[event] value2 = 4
[event] value1 = 0
[event] value2 = 0
[event] value1 = 1
[event] value2 = 1

[main] Ctrl+C — stopping…
17:59:52 [INFO    ] abb_rws_client_python_rw6.abb_rws_client_python_rw6.highlevel.subscription — Subscription group_id=14 cleanup delegated to WebSocket close
[main] Done.
PS ~\abb-rws-client-python-rw6>
```
