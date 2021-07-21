import traceback
import uuid
from os.path import abspath
import os

import aiohttp
import filetype as ft
from graia.application import MessageChain, GroupMessage, FriendMessage
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.application.message.elements.internal import Plain, Image
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter

from core.logger import Logger
from core.elements import Plain as BPlain, Image as BImage
from core.bots.graia.broadcast import app, bcc
from database_old import BotDB as database


class Template:
    all_func = ("sendMessage", "waitConfirm", "asDisplay")
    async def sendMessage(self, message: dict, msgchain, quote=True):
        """
        用于发送一条消息，兼容Group和Friend消息。
        :param message: 函数传入的dict
        :param msgchain: 消息链，若传入str则自动创建一条带有Plain元素的消息链
        :param quote: 是否引用传入dict中的消息（仅对Group消息有效）
        :return: 被发送的消息链
        """
        if isinstance(msgchain, str):
            if msgchain == '':
                msgchain = '发生错误：机器人尝试发送空文本消息，请联系机器人开发者解决问题。'
            msgchain = MessageChain.create([Plain(msgchain)])
        if isinstance(msgchain, list):
            msgchain_list = []
            for x in msgchain:
                if isinstance(x, BPlain):
                    msgchain_list.append(Plain(x.text))
                if isinstance(x, BImage):
                    msgchain_list.append(Image.fromLocalFile(x.image))
            if not msgchain_list:
                msgchain_list.append(Plain('发生错误：机器人尝试发送空文本消息，请联系机器人开发者解决问题。'))
            msgchain = MessageChain.create(msgchain_list)
        if Group in message:
            send = await app.sendGroupMessage(message[Group], msgchain)
            return send
        if Friend in message:
            send = await app.sendFriendMessage(message[Friend], msgchain)
            return send
        if 'From' in message:
            if message['From'] == 'Group':
                send = await app.sendGroupMessage(message['ID'], msgchain)
                return send
            if message['From'] == 'Friend':
                send = await app.sendFriendMessage(message['ID'], msgchain)
                return send


    async def waitConfirm(self, message: dict):
        """
        一次性模板，用于等待触发对象确认，兼容Group和Friend消息
        :param message: 函数传入的dict
        :return: 若对象发送confirm_command中的其一文本时返回True，反之则返回False
        """
        inc = InterruptControl(bcc)
        confirm_command = ["是", "对", '确定', '是吧', '大概是',
                           '也许', '可能', '对的', '是呢', '对呢', '嗯', '嗯呢',
                           '吼啊', '资瓷', '是呗', '也许吧', '对呗', '应该',
                           'yes', 'y', 'yeah', 'yep', 'ok', 'okay', '⭐', '√']
        if Group in message:
            @Waiter.create_using_function([GroupMessage])
            def waiter(waiter_group: Group,
                       waiter_member: Member, waiter_message: MessageChain):
                if all([
                    waiter_group.id == message[Group].id,
                    waiter_member.id == message[Member].id,
                ]):
                    if waiter_message.asDisplay() in confirm_command:
                        return True
                    else:
                        return False
        if Friend in message:
            @Waiter.create_using_function([FriendMessage])
            def waiter(waiter_friend: Friend, waiter_message: MessageChain):
                if all([
                    waiter_friend.id == message[Friend].id,
                ]):
                    if waiter_message.asDisplay() in confirm_command:
                        return True
                    else:
                        return False

        return await inc.wait(waiter)

    def asDisplay(self, message: dict):
        if 'TEST' in message:
            display = message['command']
        else:
            display = message[MessageChain].asDisplay()
        return display

    async def revokeMessage(self, msgchain):
        """
        用于撤回消息。
        :param msgchain: 需要撤回的已发送/接收的消息链
        :return: 无返回
        """
        try:
            if isinstance(msgchain, list):
                for msg in msgchain:
                    await app.revokeMessage(msg)
            else:
                await app.revokeMessage(msgchain)
        except:
            traceback.print_exc()


    def checkPermission(self, message):
        """
        检查对象是否拥有某项权限
        :param message: 从函数传入的dict
        :return: 若对象为群主、管理员或机器人超管则为True
        """
        if Group in message:
            if str(message[Member].permission) in ['MemberPerm.Administrator',
                                                  'MemberPerm.Owner'] or database.check_superuser(
                    message) or database.check_group_adminuser(message):
                return True
        if Friend in message:
            if database.check_superuser(message[Friend].id):
                return True
        return False

"""    async def Nudge(kwargs):
        try:
            if Group in kwargs:
                await app.nudge(kwargs[Member])
            if Friend in kwargs:
                await app.nudge(kwargs[Friend])
        except:
            traceback.print_exc()"""