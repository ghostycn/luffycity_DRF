from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your views here.
from .serializer import RegisterSerializers
from utils.base_response import BaseResponse
from Course.models import Account
from utils.redis_pool import POOl
from utils.my_auth import LoginAuth
import redis,uuid

class RegisterView(APIView):
    def post(self,request):
        res = BaseResponse()
        ser_obj = RegisterSerializers(data=request.data)
        if ser_obj.is_valid():
            ser_obj.save()
            res.data = ser_obj.data
        else:
            res.code = 1020
            res.error = ser_obj.errors
        return Response(res.dict)

class LoginView(APIView):
    def post(self,request):
        res = BaseResponse()
        username = request.data.get("username","")
        pwd = request.data.get("pwd","")
        user_obj = Account.objects.filter(username=username,pwd=pwd).first()
        if not user_obj:
            res.code = 1030
            res.error = "用户名或密码错误"
            return Response(res.dict)
        # 用户登录成功生成一个token写入redis
        # 写入redis token: user_id
        conn = redis.Redis(connection_pool=POOl)
        try:
            token = uuid.uuid4()
            conn.set(str(token),user_obj.id,ex=6000)
            res.data = token
        except Exception as e:
            res.code = 1031
            res.error = "创建令牌失败"

        return Response(res.dict)

class TestView(APIView):
    authentication_classes = [LoginAuth]
    def get(self,request):
        return Response("认证测试")