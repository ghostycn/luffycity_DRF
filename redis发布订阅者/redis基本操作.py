#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import redis
conn = redis.Redis(host="127.0.0.1",port=6379,decode_responses=True)

# conn.set("n1","v1")
# conn.hset("n2","k2","v2")
# conn.hmset("n3",{"k3":"v3","k4":"v4"})
print(conn.get("n1"))
print(conn.hget("n2","k2"))
print(conn.hget("n3","k3"))
print(conn.hget("n3","k4"))
print(conn.hgetall("n3"))