import asyncio
import aiomqtt

MQTT_BROKER_ADDRESS = "localhost"  # Change this to your MQTT broker address
TOPIC = "golfball/golfball1/command"  # Change this to your chosen topic for new player notifications

async def main():
    async with aiomqtt.Client(MQTT_BROKER_ADDRESS) as client:
        # Subscribe to the topic where new player notifications are published
        await client.subscribe(TOPIC)
        
        # Continuously check for new messages
        async for message in client.messages:
            # Decode the message payload
            message_content = message.payload.decode('utf-8')
            
            # Check if the message is "new_player"
            if message_content == "new_player":
                print("New player is ready!")
                # Here, you can implement any action you want to take when a new player is ready

asyncio.run(main())
