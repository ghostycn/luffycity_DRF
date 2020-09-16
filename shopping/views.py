from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.base_response import BaseResponse
from utils.my_auth import LoginAuth
from utils.redis_pool import POOl
from Course.models import Course
import json,redis

# Create your views here.
# 前端传过来 course_id price_policy_id
# 把购物车数据放入redis
"""
{
    SHOPPINGCART_USERID_COURSE_ID: {
        "id":"",
        "title":"",
        "course_img":"",
        "price_policy_dict":{
            price_policy_id1: "{valid_period, price}",
            price_policy_id2: "{valid_period, price}",
            price_policy_id3: "{valid_period, price}"
        },
        "default_price_policy_id":1
    }
}
"""

SHOPPINGCART_KEY = "SHOPPINGCART_%s_%s"
CONN = redis.Redis(connection_pool=POOl)

class ShoppingCartView(APIView):
    authentication_classes = [LoginAuth]
    def post(self,request):
        res = BaseResponse()
        # 1、获取前端传过来的数据以及user_id
        course_id = request.data.get("course_id","")
        price_policy_id = request.data.get("price_policy_id","")
        user_id = request.user.pk
        # 2、校验数据的合法性
        # 2.1 校验课程id合法性
        course_obj = Course.objects.filter(id=course_id).first()
        print(course_obj.price_policy.all())
        if not course_id:
            res.code = 1040
            res.error = "课程id不合法"
            return Response(res.dict)
        # 2.2校验价格策略id是否合法
        price_policy_queryset = course_obj.price_policy.all()
        price_policy_dict = {}
        for price_policy in price_policy_queryset:
            print(price_policy)
            print(price_policy.id)
            price_policy_dict[price_policy.id] = {
                "price": price_policy.price,
                "valid_period": price_policy.valid_period,
                "valid_period_display": price_policy.get_valid_period_display()
            }
        if price_policy_id not in price_policy_dict:
            res.code = 1041
            res.error = "价格策略不合法"
            return Response(res.dict)
        # 3、构建redisKEY
        key = SHOPPINGCART_KEY %(user_id,course_id)
        # 4、构建数据结构
        course_info = {
            "id": course_obj.id,
            "title":course_obj.title,
            "course_img":str(course_obj.course_img),
            "price_policy_dict":json.dumps(price_policy_dict,ensure_ascii=False),
            "default_price_policy_id":price_policy_id
        }
        print(course_info)
        # 5、写入redis
        CONN.hmset(key,course_info)
        res.data = "加入购物车成功"
        return Response(res.dict)

    def get(self,request):
        res = BaseResponse()
        # 1、拼接redis key
        user_id = request.user.pk
        shopping_cart_key = SHOPPINGCART_KEY % (user_id, "*")
        # 2、去redis中读取数据
        # 2.1 匹配所有的keys
        # 3、构建数据结构展示
        all_keys = CONN.scan_iter(shopping_cart_key)
        ret = []
        for key in all_keys:
            ret.append(CONN.hgetall(key))
        res.data = ret
        return Response(res.dict)

    def put(self,request):
        # 前端 course_id price_policy_id
        res = BaseResponse()
        # 1、获取前端传过来的数据以及user_id
        course_id = request.data.get("course_id","")
        price_policy_id = request.data.get("price_policy_id","")
        user_id = request.user.pk

        # 2、校验数据的合法性
        # 2.1 course_id是否合法
        key = SHOPPINGCART_KEY %(user_id,course_id)
        print(key)
        if not CONN.exists(key):
            res.code = 1043
            res.error = "课程id不合法"
            return Response(res.dict)
        # 2.2 price_policy_id 是否合法
        price_policy_dict = json.loads(CONN.hget(key,"price_policy_dict"))
        if str(price_policy_id) not in price_policy_dict:
            res.code = 1044
            res.error = "价格策略不合法"
            return Response(res.dict)
        # 3、更新redis default_price_policy_id
        CONN.hset(key,"default_price_policy_id",price_policy_id)
        res.data = "更新成功"
        return Response(res.dict)

    def delete(self,request):
        # course_list = [course_id]
        res = BaseResponse()
        # 1、获取前端传来的数据以及user_id
        course_list = request.data.get("course_list","")
        user_id = request.user.pk
        # 2、校验course_id是否合法
        for course_id in course_list:
            key = SHOPPINGCART_KEY %(user_id,course_id)
            if not CONN.exists(key):
                res.code = 1045
                res.error = "课程ID不合法"
                return Response(res.dict)
            # 3、删除redis数据
            CONN.delete(key)
        res.data = "删除成功"
        return Response(res.data)