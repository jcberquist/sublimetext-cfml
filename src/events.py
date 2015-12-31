event_listeners = {}

def subscribe(event_name, callback):
	if event_name not in event_listeners:
		event_listeners[event_name] = []
	event_listeners[event_name].append(callback)

def trigger(event_name, *event_args):
	if event_name in event_listeners:
		for callback in event_listeners[event_name]:
			callback(*event_args)