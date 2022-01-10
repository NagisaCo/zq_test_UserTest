import re

from rest_framework import serializers
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    注册序列化器
    """

    # 序列化器的所有字段 ['id', 'username', 'nickname', 'password', 'password2', 'mobile']
    # 校验字段 ['username', 'nickname', 'password', 'password2', 'mobile']
    # 已存在字段 ['id', 'username', 'nickname', 'password', 'mobile']

    # 需要序列化（后端响应）的字段 ['id', 'username', 'mobile', 'access', 'refresh']
    # 需要反序列化（前端传入）的字段 ['username', 'nickname', 'password', 'password2', 'mobile']  write_only=True

    password = PasswordField(label='密码', write_only=True)
    password2 = PasswordField(label='确认密码', write_only=True)
    refresh = serializers.CharField(label='刷新令牌', read_only=True)  # JWT
    access = serializers.CharField(label='访问令牌', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'password', 'password2', 'mobile', 'refresh', 'access']  # 序列化器内容
        extra_kwargs = {  # 简易校验字段
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义校验信息
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'nickname': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义校验信息
                    'min_length': '仅允许5-20个字符的昵称',
                    'max_length': '仅允许5-20个字符的昵称',
                }
            },
        }

    def validate_mobile(self, value):
        """
        手机号校验
        """
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机号格式错误', code='mobile_invalid')

        return value

    def validate_password(self, value):
        """
        密码校验
        """
        if not re.match(r'^[A-Za-z\d.,/;:"\'\[\]\\<>|()\-=+`~@$!%*#?&]{8,24}$', value):
            raise serializers.ValidationError('密码不安全', code='password_invalid')

        return value

    def validate(self, attrs):
        """
        校验密码
        """
        # 判断两次密码是否一致
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('密码不一致', code='password_not_match')

        return attrs

    @staticmethod
    def get_tokens_for_user(user):
        """
        生成用户 token
        :param user: 用户对象
        :return: token 字典
        """
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def create(self, validated_data):
        """
        创建用户, 追加返回 jwt token
        """
        # 删除数据库中不需要的字段
        del validated_data['password2']

        password = validated_data.pop('password')  # 避免密码明文存储

        # 创建用户
        user = User(**validated_data)
        user.set_password(password)  # 密码加密
        user.save()

        # 生成jwt token
        token = self.get_tokens_for_user(user)
        user.refresh = token['refresh']
        user.access = token['access']

        return user
