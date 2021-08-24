import re
import traceback

from graia.application import MessageChain, GroupMessage, FriendMessage
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.application.message.elements.internal import Plain, Image, Source, Voice
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter

from core.bots.graia.broadcast import app, bcc
from core.elements import Plain as BPlain, Image as BImage, Voice as BVoice, MessageSession as MS, MsgInfo, Session, \
    FetchTarget as FT
from core.elements.others import confirm_command
from core.utils import slk_converter


class MessageSession(MS):
    class Feature:
        image = True
        voice = True

    async def sendMessage(self, msgchain, quote=True):
        if isinstance(msgchain, str):
            if msgchain == '':
                msgchain = '发生错误：机器人尝试发送空文本消息，请联系机器人开发者解决问题。\n错误汇报地址：https://github.com/Teahouse-Studios/bot/issues/new?assignees=OasisAkari&labels=bug&template=5678.md&title='
            msgchain = MessageChain.create([Plain(msgchain)])
        if isinstance(msgchain, list):
            msgchain_list = []
            for x in msgchain:
                if isinstance(x, BPlain):
                    msgchain_list.append(Plain(x.text))
                if isinstance(x, BImage):
                    msgchain_list.append(Image.fromLocalFile(await x.get()))
                if isinstance(x, BVoice):
                    msgchain_list.append(Voice().fromLocalFile(filepath=await slk_converter(x.path)))
            if not msgchain_list:
                msgchain_list.append(Plain('发生错误：机器人尝试发送空文本消息，请联系机器人开发者解决问题。\n错误汇报地址：https://github.com/Teahouse-Studios/bot/issues/new?assignees=OasisAkari&labels=bug&template=5678.md&title='))
            msgchain = MessageChain.create(msgchain_list)
        if isinstance(self.session.target, Group):
            send = await app.sendGroupMessage(self.session.target, msgchain, quote=self.session.message[Source][0].id
            if quote and self.session.message else None)
            return MessageSession(
                target=MsgInfo(targetId=0, senderId=0, targetFrom='QQ|Bot', senderFrom="QQ|Bot", senderName=''),
                session=Session(message=send, target=0, sender=0))
        if isinstance(self.session.target, Friend):
            send = await app.sendFriendMessage(self.session.target, msgchain)
            return MessageSession(
                target=MsgInfo(targetId=0, senderId=0, targetFrom='QQ|Bot', senderFrom="QQ|Bot", senderName=''),
                session=Session(message=send, target=0, sender=0))

    async def waitConfirm(self):
        inc = InterruptControl(bcc)
        if isinstance(self.session.target, Group):
            @Waiter.create_using_function([GroupMessage])
            def waiter(waiter_group: Group,
                       waiter_member: Member, waiter_message: MessageChain):
                if all([
                    waiter_group.id == self.session.target.id,
                    waiter_member.id == self.session.sender.id,
                ]):
                    if waiter_message.asDisplay() in confirm_command:
                        return True
                    else:
                        return False
        elif isinstance(self.session.target, Friend):
            @Waiter.create_using_function([FriendMessage])
            def waiter(waiter_friend: Friend, waiter_message: MessageChain):
                if all([
                    waiter_friend.id == self.session.sender.id,
                ]):
                    if waiter_message.asDisplay() in confirm_command:
                        return True
                    else:
                        return False

        return await inc.wait(waiter)

    def asDisplay(self):
        display = self.session.message.asDisplay()
        return display

    async def delete(self):
        """
        用于撤回消息。
        :param send_msg: 需要撤回的已发送/接收的消息链
        :return: 无返回
        """
        try:
            await app.revokeMessage(self.session.message)
        except Exception:
            traceback.print_exc()

    async def checkPermission(self):
        """
        检查对象是否拥有某项权限
        :param display_msg: 从函数传入的dict
        :return: 若对象为群主、管理员或机器人超管则为True
        """
        if isinstance(self.session.target, Group):
            if str(self.session.sender.permission) in ['MemberPerm.Administrator', 'MemberPerm.Owner'] \
                    or self.target.senderInfo.query.isSuperUser \
                    or self.target.senderInfo.check_TargetAdmin(self.target.targetId):
                return True
        if isinstance(self.session.target, Friend):
            return True
        return False

    def checkSuperUser(self):
        return True if self.target.senderInfo.query.isSuperUser else False

    class Typing:
        def __init__(self, msg: MS):
            self.msg = msg

        async def __aenter__(self):
            if isinstance(self.msg.session.target, Group):
                await app.nudge(self.msg.session.sender)

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass


class FetchTarget(FT):
    @staticmethod
    async def fetch_target(targetId):
        matchTarget = re.match(r'^(QQ\|(?:Group\||))(.*)', targetId)
        if matchTarget:
            if matchTarget.group(1) == 'QQ|Group':
                target = await app.getGroup(int(matchTarget.group(2)))
            else:
                target = await app.getFriend(int(matchTarget.group(2)))
            if target is not None:
                return MessageSession(MsgInfo(targetId=targetId, senderId=targetId, senderName='',
                                              targetFrom=matchTarget.group(1), senderFrom=matchTarget.group(1)),
                                      Session(message=False, target=target, sender=target))
            else:
                return False
        else:
            return False
