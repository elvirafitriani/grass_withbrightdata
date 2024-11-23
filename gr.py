import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect  # Import from websockets_proxy
from fake_useragent import UserAgent

user_agent = UserAgent()
random_user_agent = user_agent.random

async def connect_to_wss(http_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, http_proxy))
    logger.info(f"Connecting with device ID: {device_id}")
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            uri = "wss://proxy.wynd.network:4650/"
            
            # Create a connection to the WebSocket through the HTTP proxy using websockets_proxy
            async with proxy_connect(uri, proxy=http_proxy, ssl=ssl_context) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(30)

                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "4.26.2"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))
                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(http_proxy)

async def main():
    http_proxy = 'http://brd-customer-hl_6edd1de4-zone-isp_proxy1-country-it:dmloes25thb2@brd.superproxy.io:33335'
    user_id = "2oBslkKEyEMamRJiBwteIOSwgzB"  # Replace with your actual user ID
    
    await connect_to_wss(http_proxy, user_id)

if __name__ == '__main__':
    asyncio.run(main())
