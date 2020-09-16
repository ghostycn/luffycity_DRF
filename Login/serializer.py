#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from rest_framework import serializers
from Course.models import Account
import hashlib

class RegisterSerializers(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = "__all__"

    def create(self, validated_data):
        pwd = validated_data["pwd"]
        pwd_salt = "luffy_password" + pwd
        md5_str = hashlib.md5(pwd_salt.encode()).hexdigest()
        print("md5_str",md5_str)
        user_obj = Account.objects.create(username=validated_data["username"],pwd=md5_str)
        print(user_obj)
        return user_obj