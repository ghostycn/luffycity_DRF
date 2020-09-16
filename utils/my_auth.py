#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from utils.redis_pool import POOl
from Course.models import Account
import redis

CONN = redis.Redis(connection_pool=POOl)

class LoginAuth(BaseAuthentication):
    def authenticate(self, request):
        # 从请求头中获取前端带过来的token
        token = request.META.get("HTTP_AUTHENTICATION","")
        if not token:
            raise AuthenticationFailed("没有携带token")
        # 去redis对比
        user_id = CONN.get(str(token))
        if user_id == None:
            raise AuthenticationFailed("token过期")
        user_id = Account.objects.filter(id=user_id).first()
        return user_id,token