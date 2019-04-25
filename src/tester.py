import EightChanRelayAlt as rel

rl = rel.EightChanRelay(
    hostname="192.168.0.20",
    port=1234,
    NumberOfRelays=8,
    id="a",
)

print("Added relay")

rl.updateStatus()

print("Success")

for relay in rl.relays:
    print(f"Relay {relay.name} status: {relay.status}")
