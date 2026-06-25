from cache import redis_client

redis_client.set("test_key", "Education AI")

value = redis_client.get("test_key")

print(value)