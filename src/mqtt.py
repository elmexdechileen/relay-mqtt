import paho.mqtt.client as mqtt
import os
import logging
from queue import Queue
from threading import Thread

_LOGGER = logging.getLogger(__name__)

class Mqtt:
	username = ""
	password = ""
	server = "localhost"
	port = 1883
	prefix = "home"
	
	_client = None
	_sids = None
	_queue = None
	_threads = None

	def __init__(self, config):
		if (config == None):
			raise Exception("Config is null")

		#load sids dictionary
		self._sids = config.get("sids", None)
		if (self._sids == None):
			self._sids = dict({})

		#load mqtt settings
		mqttConfig = config.get("mqtt", None)
		if (mqttConfig == None):
			raise Exception("Config mqtt section is null")

		self.username = mqttConfig.get("username", "")
		self.password = mqttConfig.get("password", "")
		self.server = mqttConfig.get("server", "localhost")
		self.port = mqttConfig.get("port", 1883)
		self.prefix = mqttConfig.get("prefix", "home")
		self._queue = Queue()
		self._threads = []

	def connect(self):
		_LOGGER.info("Connecting to MQTT server " + self.server + ":" + str(self.port) + " with username (" + self.username + ":" + self.password + ")")
		self._client = mqtt.Client()
		if (self.username != "" and self.password != ""):
			self._client.username_pw_set(self.username, self.password)
		self._client.on_message = self._mqtt_process_message
		self._client.on_connect = self._mqtt_on_connect
		self._client.connect(self.server, self.port, 60)
        
        #run message processing loop
		t1 = Thread(target=self._mqtt_loop)
		t1.start()
		self._threads.append(t1)

	def subscribe(self, board="+", relay="+", command="set"):
		topic = self.prefix + "/" + board + "/" + relay + "/" + command
		_LOGGER.info("Subscibing to " + topic + ".")
		self._client.subscribe(topic)

	def publish(self, board, relay, data, retain=True):
		PATH_FMT = self.prefix + "/{board}/{relay}"

		topic = PATH_FMT.format(board=board, relay=relay)
		_LOGGER.info("Publishing message to topic " + topic + ".")
		self._client.publish(topic, payload=data, qos=0, retain=retain)

	def _mqtt_on_connect(self, client, userdata, rc, unk):
		_LOGGER.info("Connected to mqtt server.")

	def _mqtt_process_message(self, client, userdata, msg):
		_LOGGER.info("Processing message in " + str(msg.topic) + ": " + str(msg.payload) + ".")
		parts = msg.topic.split("/")
		if (len(parts) != 4):
			return
		board = parts[1]
		relay = parts[2] #sid or name part

		try:
			relay = int(relay[-1:])
		except:
			relay = 1

		value = (msg.payload).decode('utf-8')
		if self._is_int(value):
			value = int(value)

		data = {'board': board, 'relay': relay, 'value':value}
		# put in process queuee
		self._queue.put(data)

	def _mqtt_loop(self):
		_LOGGER.info("Starting mqtt loop.")
		self._client.loop_forever()

	def _is_int(self, x):
		try:
			tmp = int(x)
			return True
		except Exception as e:
			return False
