#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.redis_pool import POOl
from utils.base_response import BaseResponse
from utils.my_auth import LoginAuth
import redis,json
from .views import SHOPPINGCART_KEY
from .models import CouponRecord
from django.utils.timezone import now

CONN = redis.Redis(connection_pool=POOl)
SETTLEMENT_KEY = "SETTLEMENT_%s_%s"
GLOBAL_COUPON_KEY = "GLOBAL_COUPON_%s"

"""
前端传过来数据 course_list
redis = {
    settlement_userid_cccourseid: {
        id: "课程id",
        title:"",
        course_img:"",
        valid_period_display,
        price,
        course_coupon_dict: {
            course_id1:{优惠卷信息}
            course_id2:{优惠卷信息}
            course_id3:{优惠卷信息}
        }
        # 默认不选 这个字段只有更新的时候才添加
        default_coupon_id: 1
    }
    
    global_coupon_userid:{
        coupon_id: {优惠卷信息}
        coupon_id2: {优惠卷信息}
        coupon_id3: {优惠卷信息}，
        # 这个字段只有更新的时候才添加
        default_global_coupon_id: 1
    }
}
"""

class SettlementView(APIView):
    authentication_classes = [LoginAuth]
    def post(self,request):
        res = BaseResponse()
        # 1、获取前端的数据以及user_id
        course_list = request.data.get("course_list","")
        user_id = request.user.pk
        # 2、校验数据的合法性
        for course_id in course_list:
            # 2.1 判断course_id 是否在购物车中
            shopping_cart_key = SHOPPINGCART_KEY % (user_id, course_id)
            if not CONN.exists(shopping_cart_key):
                res.code = 1050
                res.error = "课程ID不合法"
                return Response(res.dict)
            # 3、构建数据结构
            # 3.1 获取用户的所有合法优惠卷
            user_all_coupons = CouponRecord.objects.filter(
                account_id=user_id,
                status=0,
                coupon__valid_begin_date__lte=now(),
                coupon__valid_end_date__gte=now()
            ).all()
            # 3.2 构建优惠卷dict
            course_coupon_dict = {}
            global_coupon_dict = {}
            print("count:",len(user_all_coupons))
            for coupon_record in user_all_coupons:
                coupon = coupon_record.coupon
                print("test:",coupon)
                if coupon.object_id == course_id:
                    course_coupon_dict[coupon.id] = {
                        "id": coupon.id,
                        "name":coupon.name,
                        "coupon_type":coupon.get_coupon_type_display(),
                        "object_id":coupon.object_id,
                        "off_percent": coupon.off_percent,
                        "money_equivalent_value":coupon.money_equivalent_value,
                        "minimum_consume":coupon.minimum_consume
                    }
                elif coupon.object_id == None:
                    global_coupon_dict[coupon.id] = {
                        "id": coupon.id,
                        "name": coupon.name,
                        "coupon_type": coupon.get_coupon_type_display(),
                        "off_percent": coupon.off_percent,
                        "money_equivalent_value": coupon.money_equivalent_value,
                        "minimum_consume": coupon.minimum_consume
                    }
            # 3.3 构建写入redis的数据结构
            course_info = CONN.hgetall(shopping_cart_key)
            default_policy_id = course_info["default_price_policy_id"]
            price_policy_dict = json.loads(course_info["price_policy_dict"])

            valid_period = price_policy_dict[str(default_policy_id)]["valid_period_display"]
            price = price_policy_dict[str(default_policy_id)]["price"]

            settlement_info = {
                "id": course_info["id"],
                "title":course_info["title"],
                "course_img":course_info["course_img"],
                "valid_period":valid_period,
                "price":price,
                "course_coupon_dict": json.dumps(course_coupon_dict,ensure_ascii=False)
            }

            # 4、写入redis
            settlement_key = SETTLEMENT_KEY % (user_id,course_id)
            global_coupon_key = GLOBAL_COUPON_KEY % user_id
            print(settlement_key,":",settlement_info)
            CONN.hmset(settlement_key, settlement_info)
            if global_coupon_dict:
                CONN.hmset(global_coupon_key,global_coupon_dict)
            # 5、删除购物车中的数据
            CONN.delete(shopping_cart_key)
        res.data = "加入结算中心成功"
        return Response(res.dict)

    def get(self,request):
        res = BaseResponse()
        # 1、获取user_id
        user_id = request.user.pk
        # 2、拼接所有key
        # 3、去redis取数据
        settlement_key = SETTLEMENT_KEY % (user_id,"*")
        global_coupon_key = GLOBAL_COUPON_KEY % user_id
        all_keys = CONN.scan_iter(settlement_key)
        ret = []
        for key in all_keys:
            ret.append(CONN.hgetall(key))
        global_coupon_info = CONN.hgetall(global_coupon_key)
        res.data = {
            "settlement_info": ret,
            "global_coupon_dict": global_coupon_info
        }
        return Response(res.dict)

    def put(self,request):
        # course_id course_coupon_id global_coupin_id
        res = BaseResponse()
        # 1、获取前端传过来的数据
        course_id = request.data.get("course_id","")
        course_coupon_id = request.data.get("course_coupon_id","")
        global_coupon_id = request.data.get("global_coupon_id","")
        user_id = request.user.pk
        # 2、校验数据合法性
        # 2.1、校验course_id
        key = SETTLEMENT_KEY %(user_id, course_id)
        if course_id:
            if not CONN.exists(key):
                res.code = 1060
                res.error = "课程不合法"
                return Response(res.dict)
        # 2.2、校验course_coupon_id
        if course_coupon_id:
            course_coupon_dict = json.loads(CONN.hget(key,"course_coupon_dict"))
            if str(course_coupon_id) not in course_coupon_dict:
                res.data = 1061
                res.error = "课程优惠卷ID不合法"
                return Response(res.dict)
        # 2.3、校验global_coupon_id
        if global_coupon_id:
            global_coupon_key = GLOBAL_COUPON_KEY %user_id
            if not CONN.exists(global_coupon_key):
                res.code = 1052
                res.error = "全局优惠卷ID不合法"
                return Response(res.dict)
            CONN.hset(global_coupon_key,"default_global_coupon_id",global_coupon_id)
        # 3、修改redis中数据
        CONN.hset(key,"default_global_coupon_id",course_coupon_id)
        res.code = 1062
        return Response(res.dict)