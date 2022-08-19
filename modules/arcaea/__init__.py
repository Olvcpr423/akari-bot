import os
import traceback

from config import Config
from core.builtins.message import MessageSession
from core.component import on_command
from core.elements import Plain, Image
from core.utils import get_url
from core.utils.i18n import get_target_locale
from .dbutils import ArcBindInfoManager
from .getb30 import getb30
from .getb30_official import getb30_official
from .info import get_info
from .info_official import get_info_official
from .initialize import arcb30init
from .utils import get_userinfo

arc = on_command('arcaea', developers=['OasisAkari'], desc='查询Arcaea相关内容。',
                 alias={'b30': 'arcaea b30', 'a': 'arcaea', 'arc': 'arcaea'})
webrender = Config('web_render')
assets_path = os.path.abspath('./assets/arcaea')


@arc.handle('b30 unofficial [<friendcode>] {查询一个Arcaea用户的b30列表（不使用官方API）}',
            'b30 [<friendcode>] {查询一个Arcaea用户的b30列表}'
            )
async def _(msg: MessageSession):
    if not os.path.exists(assets_path):
        await msg.finish('未找到资源文件！请放置一枚arcaea的apk到机器人的assets目录并重命名为arc.apk后，使用~arcaea initialize初始化资源。')
    query_code = None
    unofficial = msg.parsed_msg.get('unofficial', False)
    friendcode: str = msg.parsed_msg.get('<friendcode>', False)
    if friendcode:
        if friendcode.isdigit():
            if len(friendcode) == 9:
                query_code = friendcode
            else:
                await msg.finish('好友码必须是9位数字！')
        else:
            await msg.finish('请输入正确的好友码！')
    else:
        get_friendcode_from_db = ArcBindInfoManager(msg).get_bind_friendcode()
        if get_friendcode_from_db is not None:
            query_code = get_friendcode_from_db
    if query_code is not None:
        if not unofficial:
            try:
                resp = await getb30_official(query_code)
                msgchain = [Plain(resp['text'])]
                if 'file' in resp and msg.Feature.image:
                    msgchain.append(Image(path=resp['file']))
                await msg.sendMessage(msgchain)
            except Exception:
                traceback.print_exc()
                await msg.sendMessage(msg.t('arcaea.official_fallback'))
                unofficial = True
        if unofficial:
            try:
                resp = await getb30(query_code)
                msgchain = [Plain(resp['text'])]
                if 'file' in resp and msg.Feature.image:
                    msgchain.append(Image(path=resp['file']))
                await msg.finish(msgchain)
            except Exception:
                traceback.print_exc()
                await msg.finish('获取失败。')
    else:
        await msg.finish('未绑定用户，请使用~arcaea bind <friendcode>绑定一个用户。')


@arc.handle('info unofficial [<friendcode>] {查询一个Arcaea用户的最近游玩记录（不使用官方API）}',
            'info [<friendcode>] {查询一个Arcaea用户的最近游玩记录}')
async def _(msg: MessageSession):
    if not os.path.exists(assets_path):
        await msg.sendMessage('未找到资源文件！请放置一枚arcaea的apk到机器人的assets目录并重命名为arc.apk后，使用~arcaea initialize初始化资源。')
        return
    query_code = None
    unofficial = msg.parsed_msg.get('unofficial', False)
    friendcode = msg.parsed_msg.get('<friendcode>', False)
    if friendcode:
        if friendcode.isdigit():
            if len(friendcode) == 9:
                query_code = friendcode
            else:
                await msg.finish(msg.t('arcaea.info.friendcode_digit'))
        else:
            await msg.finish(msg.t('arcaea.info.friendcode_invalid'))
    else:
        get_friendcode_from_db = ArcBindInfoManager(msg).get_bind_friendcode()
        if get_friendcode_from_db is not None:
            query_code = get_friendcode_from_db
    if query_code is not None:
        if not unofficial:
            try:
                resp = await get_info_official(query_code)
                if resp['success']:
                    await msg.finish(resp['msg'])
                else:
                    await msg.sendMessage(msg.t('arcaea.official_fallback'))
                    unofficial = True
            except Exception:
                traceback.print_exc()
                await msg.sendMessage(msg.t('arcaea.official_fallback'))
                unofficial = True
        if unofficial:
            try:
                resp = await get_info(query_code)
                await msg.finish(resp)
            except Exception:
                traceback.print_exc()
                await msg.finish('获取失败。')
    else:
        await msg.finish('未绑定用户，请使用~arcaea bind <friendcode>绑定一个用户。')


@arc.handle('bind <friendcode/username> {绑定一个Arcaea用户}')
async def _(msg: MessageSession):
    code: str = msg.parsed_msg['<friendcode/username>']
    getcode = await get_userinfo(code)
    if getcode:
        bind = ArcBindInfoManager(msg).set_bind_info(username=getcode[0], friendcode=getcode[1])
        if bind:
            await msg.finish(msg.t('arcaea.bind.success', a=getcode[0], b=getcode[1]))
    else:
        if code.isdigit():
            bind = ArcBindInfoManager(msg).set_bind_info(username='', friendcode=code)
            if bind:
                await msg.finish(msg.t('arcaea.bind.fail_to_fetch'))
        else:
            await msg.finish(msg.t('arcaea.bind.failure'))


@arc.handle('unbind {取消绑定用户}')
async def _(msg: MessageSession):
    unbind = ArcBindInfoManager(msg).remove_bind_info()
    if unbind:
        await msg.finish(msg.t('arcaea.unbind'))


@arc.handle('initialize', required_superuser=True)
async def _(msg: MessageSession):
    assets_apk = os.path.abspath('./assets/arc.apk')
    if not os.path.exists(assets_apk):
        await msg.finish(msg.t('arcaea.init.missing_arcapk'))
        return
    result = await arcb30init()
    if result:
        await msg.finish(msg.t('arcaea.init.success'))


@arc.handle('download {获取最新版本的游戏apk}')
async def _(msg: MessageSession):
    if not webrender:
        await msg.finish([msg.t('global.missing_web_render')])
    resp = await get_url(webrender + 'source?url=https://webapi.lowiro.com/webapi/serve/static/bin/arcaea/apk/', 200,
                         fmt='json')
    if resp:
        await msg.finish([Plain(f'目前的最新版本为{resp["value"]["version"]}。\n下载地址：{resp["value"]["url"]}')])


@arc.handle('random {随机一首曲子}')
async def _(msg: MessageSession):
    if not webrender:
        await msg.finish([msg.t('global.missing_web_render')])
    resp = await get_url(webrender + 'source?url=https://webapi.lowiro.com/webapi/song/showcase/', 200, fmt='json')
    if resp:
        value = resp["value"][0]
        image = f'{assets_path}/jacket/{value["song_id"]}.jpg'
        result = [Plain(value["title"]["en"])]
        if os.path.exists(image):
            result.append(Image(path=image))
        await msg.finish(result)


@arc.handle('rank free {查看当前免费包游玩排行}', 'rank paid {查看当前付费包游玩排行}')
async def _(msg: MessageSession):
    if not webrender:
        await msg.finish([msg.t('global.missing_web_render')])
    if msg.parsed_msg.get('free', False):
        resp = await get_url(webrender + 'source?url=https://webapi.lowiro.com/webapi/song/rank/free/', 200, fmt='json')
    else:
        resp = await get_url(webrender + 'source?url=https://webapi.lowiro.com/webapi/song/rank/paid/', 200, fmt='json')
    if resp:
        r = []
        rank = 0
        for x in resp['value']:
            rank += 1
            r.append(f'{rank}. {x["title"]["en"]} ({x["status"]})')
        await msg.finish('\n'.join(r))
