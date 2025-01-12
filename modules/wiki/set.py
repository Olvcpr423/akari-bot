import ujson as json

from config import Config
from core.builtins import Bot, Plain, Image, Url
from core.utils.image_table import image_table_render, ImageTable
from modules.wiki.utils.dbutils import WikiTargetInfo
from modules.wiki.utils.wikilib import WikiLib
from .wiki import wiki


@wiki.handle('set <WikiUrl> {{wiki.help.set}}', required_admin=True)
async def set_start_wiki(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    check = await WikiLib(msg.parsed_msg['<WikiUrl>'], headers=target.get_headers()).check_wiki_available()
    if check.available:
        if not check.value.in_blocklist or check.value.in_allowlist:
            result = WikiTargetInfo(msg).add_start_wiki(check.value.api)
            if result:
                await msg.finish(
                    msg.locale.t("wiki.message.set.success", name=check.value.name) + ('\n' + check.message if check.message != '' else '') +
                    (('\n' + msg.locale.t("wiki.message.untrust") + Config("wiki_whitelist_url"))
                     if not check.value.in_allowlist else ''))
        else:
            await msg.finish(msg.locale.t("wiki.message.error.blocked", name=check.value.name))
    else:
        result = msg.locale.t('wiki.message.error.add') + \
            ('\n' + msg.locale.t('wiki.message.error.info') + check.message if check.message != '' else '')
        await msg.finish(result)


@wiki.handle('iw (add|set) <Interwiki> <WikiUrl> {{wiki.help.iw.set}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    iw = msg.parsed_msg['<Interwiki>']
    url = msg.parsed_msg['<WikiUrl>']
    target = WikiTargetInfo(msg)
    check = await WikiLib(url, headers=target.get_headers()).check_wiki_available()
    if check.available:
        if not check.value.in_blocklist or check.value.in_allowlist:
            result = target.config_interwikis(iw, check.value.api, let_it=True)
            if result:
                await msg.finish(msg.locale.t("wiki.message.iw.set.success", iw=iw, name=check.value.name) +
                                 (('\n' + msg.locale.t("wiki.message.untrust") + Config("wiki_whitelist_url"))
                                  if not check.value.in_allowlist else ''))
        else:
            await msg.finish(msg.locale.t("wiki.message.error.blocked", name=check.value.name))
    else:
        result = msg.locale.t('wiki.message.error.add') + \
            ('\n' + msg.locale.t('wiki.message.error.info') + check.message if check.message != '' else '')
        await msg.finish(result)


@wiki.handle('iw (del|delete|remove|rm) <Interwiki> {{wiki.help.iw.remove}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    iw = msg.parsed_msg['<Interwiki>']
    target = WikiTargetInfo(msg)
    result = target.config_interwikis(iw, let_it=False)
    if result:
        await msg.finish(msg.locale.t("wiki.message.iw.remove.success", iw=iw))


@wiki.handle(['iw (list|show) {{wiki.help.iw.list}}',
              'iw (list|show) legacy {{wiki.help.iw.list.legacy}}'])
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    query = target.get_interwikis()
    start_wiki = target.get_start_wiki()
    base_interwiki_link = None
    if start_wiki is not None:
        base_interwiki_link_ = await WikiLib(start_wiki, target.get_headers()).parse_page_info('Special:Interwiki')
        if base_interwiki_link_.status:
            base_interwiki_link = base_interwiki_link_.link
    if query != {}:
        if 'legacy' not in msg.parsed_msg and msg.Feature.image:
            columns = [[x, query[x]] for x in query]
            img = await image_table_render(ImageTable(columns, ['Interwiki', 'Url']))
        else:
            img = False
        if img:
            mt = msg.locale.t("wiki.message.iw.list", prefix=msg.prefixes[0])
            if base_interwiki_link is not None:
                mt += '\n' + msg.locale.t("wiki.message.iw.list.prompt", url=str(Url(base_interwiki_link)))
            await msg.finish([Image(img), Plain(mt)])
        else:
            result = msg.locale.t("wiki.message.iw.list.legacy") + '\n' + \
                '\n'.join([f'{x}: {query[x]}' for x in query])
            if base_interwiki_link is not None:
                result += '\n' + msg.locale.t("wiki.message.iw.list.prompt", url=str(Url(base_interwiki_link)))
            await msg.finish(result)
    else:
        await msg.finish(msg.locale.t("wiki.message.iw.none", prefix=msg.prefixes[0]))


@wiki.handle('iw get <Interwiki> {{wiki.help.iw.get}}')
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    query = target.get_interwikis()
    if query != {}:
        if msg.parsed_msg['<Interwiki>'] in query:
            await msg.finish(Url(query[msg.parsed_msg['<Interwiki>']]))
        else:
            await msg.finish(msg.locale.t("wiki.message.iw.get.not_found", iw=msg.parsed_msg["<Interwiki>"]))
    else:
        await msg.finish(msg.locale.t("wiki.message.iw.none", prefix=msg.prefixes[0]))


@wiki.handle(['headers (list|show) {{wiki.help.headers.list}}'])
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    headers = target.get_headers()
    prompt = msg.locale.t("wiki.message.headers.list")
    await msg.finish(prompt)


@wiki.handle('headers (add|set) <Headers> {{wiki.help.headers.set}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    add = target.config_headers(
        " ".join(msg.trigger_msg.split(" ")[3:]), let_it=True)
    if add:
        await msg.finish(msg.locale.t("wiki.message.headers.set.success", headers=json.dumps(target.get_headers())))


@wiki.handle('headers (del|delete|remove|rm) <HeaderKey> {{wiki.help.headers.remove}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    delete = target.config_headers(
        [msg.parsed_msg['<HeaderHey>']], let_it=False)
    if delete:
        await msg.finish(msg.locale.t("wiki.message.headers.set.success", headers=json.dumps(target.get_headers())))


@wiki.handle('headers reset {{wiki.help.headers.reset}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    reset = target.config_headers('{}', let_it=None)
    if reset:
        await msg.finish(msg.locale.t("wiki.message.headers.reset.success"))


@wiki.handle('prefix set <prefix> {{wiki.help.prefix.set}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    prefix = msg.parsed_msg['<prefix>']
    set_prefix = target.set_prefix(prefix)
    if set_prefix:
        await msg.finish(msg.locale.t("wiki.message.prefix.set.success", wiki_prefix=prefix))


@wiki.handle('prefix reset {{wiki.help.prefix.reset}}', required_admin=True)
async def _(msg: Bot.MessageSession):
    target = WikiTargetInfo(msg)
    set_prefix = target.del_prefix()
    if set_prefix:
        await msg.finish(msg.locale.t("wiki.message.prefix.reset.success"))


@wiki.handle('fandom {{wiki.help.fandom}}',
             required_admin=True)
async def _(msg: Bot.MessageSession):

    fandom_addon_state = msg.data.options.get('wiki_fandom_addon')
    
    if fandom_addon_state:
        msg.data.edit_option('wiki_fandom_addon', False)
        await msg.finish(msg.locale.t("wiki.message.fandom.disable"))
    else:
        msg.data.edit_option('wiki_fandom_addon', True)
        await msg.finish(msg.locale.t("wiki.message.fandom.enable"))


@wiki.handle('redlink {{wiki.help.redlink}}',
             required_admin=True)
async def _(msg: Bot.MessageSession):
    redlink_state = msg.data.options.get('wiki_redlink')
    
    if redlink_state:
        msg.data.edit_option('wiki_redlink', False)
        await msg.finish(msg.locale.t("wiki.message.redlink.disable"))
    else:
        msg.data.edit_option('wiki_redlink', True)
        await msg.finish(msg.locale.t("wiki.message.redlink.enable"))
