import redis.asyncio as redis


class ConnectionManager:

    def __init__(self):
        self.redis = redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )

    async def add_connection(self, user_id, channel_name):
        key = f"user:{user_id}:connections"

        await self.redis.sadd(key, channel_name)
        await self.redis.expire(key, 86400)

        return await self.redis.scard(key)

    async def remove_connection(self, user_id, channel_name):
        key = f"user:{user_id}:connections"

        await self.redis.srem(key, channel_name)

        count = await self.redis.scard(key)

        if count == 0:
            await self.redis.delete(key)

        return count

    async def close(self):
        await self.redis.aclose()


connection_manager = ConnectionManager()