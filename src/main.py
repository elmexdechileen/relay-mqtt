import logging
import time
import threading
import os
import json
import EightChanRelay as rel

#mine
import mqtt
import yamlparser

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)
QUERY_TIME = 2

processNow = False

def init_relays(config):
	boards = []

	if config is None:
		raise Exception("Config is None.")
	relays = config.get("relays", "None")
	if relays is None:
		raise Exception("Config -> relays is None.")

	for relay in relays:
		if (relay is None):
			continue
		try:
			rl = rel.EightChanRelay(
				hostname=relay,
				port=relays.get(relay).get("port", "None"),
				NumberOfRelays=relays.get(relay).get("numberrelays", "None"),
				id=relays.get(relay).get("name", "None"),
			)

			boards.append(rl)
		except Exception as e:
			_LOGGER.error('Connection to ', str(relay) , ' error:', str(e))
	return boards

def wait():
	global processNow
	for x in range(1,10):
		if (processNow):
			processNow=False
			break
		time.sleep(QUERY_TIME/10)

def process_relay_states(client):
	global boards
	while True:
		wait()
		try:
			for board in boards:
				board.updateStatus()
				for rl in board.relays:
					data = {'status': rl.status}
					client.publish(board.name, rl.name, str(data))
		except Exception as e:
			_LOGGER.error('Error while sending from gateway to mqtt: ', str(e))

def process_mqtt_messages(client):
	global processNow, boards
	while True:
		try: 
			data = client._queue.get()
			_LOGGER.debug("data from mqtt: " + format(data))

			board = data.get("board", None)
			relay = data.get("relay", None)
			value = data.get("value", None)

			for brd in boards:
				if brd.name != board:
					continue
				brd.processUpdate(value, relay)
				processNow = True

			client._queue.task_done()
			process_relay_states(client)
		except Exception as e:
			_LOGGER.error('Error while sending from mqtt to gateway: ', str(e))

if __name__ == "__main__":
	_LOGGER.info("Loading config file...")
	#config=yamlparser.load_yaml('config/config.yaml')
	config = yamlparser.load_yaml('config.yaml')
	_LOGGER.info("Init mqtt client.")
	client = mqtt.Mqtt(config)
	client.connect()
	#only this devices can be controlled from MQTT
	client.subscribe("+", "+", "set")
	
	boards = init_relays(config)

	t1 = threading.Thread(target=process_relay_states, args=[client])
	t1.daemon = True
	t1.start()

	t2 = threading.Thread(target=process_mqtt_messages, args=[client])
	t2.daemon = True
	t2.start()

	while True:
		time.sleep(60)