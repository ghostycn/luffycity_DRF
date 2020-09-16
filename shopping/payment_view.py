#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.my_auth import LoginAuth
from utils.base_response import BaseResponse
from .settlement_view import SETTLEMENT_KEY,GLOBAL_COUPON_KEY
from utils.redis_pool import POOl
from Course.models import Course
from .models import Coupon
from django.utils.timezone import now
import redis

CONN = redis.Redis(connection_pool=POOl)

class PaymentView(APIView):
    authentication_classes = [LoginAuth]
    def post(self,request):
        res = BaseResponse()
        # 1、获取数据
        balance = request.data.get("balance",0)
        price = request.data.get("price","")
        user_id = request.user.ok
        # 2 校验数据的合法性
        # 2.1 校验贝里数是否合法
        if int(balance) > request.user.balance:
            res.code = 1070
            res.error = "抵扣的贝里错误"
            return Response(res.dict)
        # 2.2 从用户的结算中心拿数据 跟数据库比对是否合法
        settlement_key = SETTLEMENT_KEY % (user_id,"*")
        all_keys = CONN.scan_iter(settlement_key)
        # 课程id是否合法
        course_rebate_total_price = 0
        for key in all_keys:
            settlement_info = CONN.hgetall(key)
            course_id = settlement_info["id"]
            course_obj = Course.objects.filter(id=course_id).first()
            if not course_obj or course_obj.status == 1:
                res.code = 1071
                res.error = "课程id不合法"
                return Response(res.dict)
            # 优惠劵是否过期
            course_coupon_id = settlement_info.get("default_coupon_id",0)
            if course_coupon_id:
                coupon_dict = Coupon.objects.filter(
                    id = course_coupon_id,
                    couponrecord__status=0,
                    couponrecord__account_id=user_id,
                    object_id=course_id,
                    valid_begin_date__lte=now(),
                    valid_end_date__gte=now()
                ).values("content_type","money_equivalent_value","off_percent","minimum_consume")
            if not coupon_dict:
                res.code = 1072
                res.error = "优惠劵不合法"
                return Response(res.dict)
            # 2.3 校验price
            # 得到所有的课程的折后价格和
            course_price = settlement_info["price"]
            course_rebate_price = self.account_price(coupon_dict,course_price)
            if course_rebate_price == -1:
                res.code = 1074
                res.error = "课程优惠劵不符合要求"
                return Response(res.dict)
            course_rebate_total_price +=course_rebate_price
        # 跟全局优惠劵做折扣
        # 校验全局优惠劵是否合法
        global_coupon_key = GLOBAL_COUPON_KEY %user_id
        global_coupon_id = int(CONN.hget(global_coupon_key,"default_global_coupon_id"))
        if global_coupon_id:
            global_coupon_dict = Coupon.objects.filter(
                id=global_coupon_id,
                couponrecord__status=0,
                couponrecord__account_id=user_id,
                valid_begin_date__lte=now(),
                valid_end_date__gte=now(),
            ).values("coupon_type", "money_equivalent_value", "off_percent", "minimum_consume")
        if not global_coupon_dict:
            res.code = 1073
            res.error = "全局优惠券id不合法"
            return Response(res.dict)
        global_rebate_price = self.account_price(global_coupon_dict, course_rebate_total_price)
        if global_rebate_price == -1:
            res.code = 1076
            res.error = "全局优惠券不符合要求"
            return Response(res.dict)
        # 抵扣贝里
        balance_money = balance / 100
        balance_rebate_price = global_rebate_price - balance
        if balance_rebate_price < 0:
            balance_rebate_price = 0
        # 终极校验price
        if balance_rebate_price != price:
            res.code = 1078
            res.error = "价格不合法"
            return Response(res.dict)
        # 3 调用支付宝接口支付

    def account_price(self, coupon_dict, price):
        coupon_type = coupon_dict["coupon_type"]
        if coupon_type == 0:
            # 通用优惠券
            money_equivalent_value = coupon_dict["money_equivalent_value"]
            if price - money_equivalent_value >= 0:
                rebate_price = price - money_equivalent_value
            else:
                rebate_price = 0
        elif coupon_type == 1:
            # 满减
            money_equivalent_value = coupon_dict["money_equivalent_value"]
            minimum_consume = coupon_dict["minimum_consume"]
            if price >= minimum_consume:
                rebate_price = price - money_equivalent_value
            else:
                return -1
        elif coupon_type == 2:
            # 折扣
            minimum_consume = coupon_dict["minimum_consume"]
            off_percent = coupon_dict["off_percent"]
            if price >= minimum_consume:
                rebate_price = price * (off_percent / 100)
            else:
                return -1
        return rebate_price