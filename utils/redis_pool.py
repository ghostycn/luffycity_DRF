#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import redis

POOl = redis.ConnectionPool(host="127.0.0.1",port=6379,decode_responses=True,max_connections=10)