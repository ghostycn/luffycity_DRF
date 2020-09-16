#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import redis

pool = redis.ConnectionPool(host="127.0.0.1",port=6379,decode_responses=True,max_connections=10)
conn = redis.Redis(connection_pool=pool)

ret = conn.get("n1")
print(ret)