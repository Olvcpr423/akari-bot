import base64
import traceback
from typing import List, Union

import aiohttp
import filetype as ft
import ujson as json
from PIL import Image as PImage
from aiofile import async_open

from config import Config
from core.builtins import Plain, Image, Voice, Embed
from core.logger import Logger
from core.types.message.chain import MessageChain
from core.utils.cache import random_cache_path
from core.utils.http import download_to_cache

web_render = Config('web_render')
web_render_local = Config('web_render_local')


async def image_split(i: Image) -> List[Image]:
    i = PImage.open(await i.get())
    iw, ih = i.size
    if ih <= 1500:
        return [Image(i)]
    _h = 0
    i_list = []
    for x in range((ih // 1500) + 1):
        if _h + 1500 > ih:
            crop_h = ih
        else:
            crop_h = _h + 1500
        i_list.append(Image(i.crop((0, _h, iw, crop_h))))
        _h = crop_h
    return i_list


save_source = True


async def msgchain2image(msgchain: Union[List, MessageChain], use_local=True):
    if not web_render_local:
        if not web_render:
            Logger.warn('[Webrender] Webrender is not configured.')
            return False
        use_local = False
    if isinstance(msgchain, List):
        msgchain = MessageChain(msgchain)
    lst = []
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <div class="botbox"'>
    ${content}
    </div>
</body>
</html>"""

    for m in msgchain.elements:
        if isinstance(m, Plain):
            lst.append('<div>' + m.text.replace('\n', '<br>') + '</div>')
        if isinstance(m, Image):
            async with async_open(await m.get(), 'rb') as fi:
                data = await fi.read()
                try:
                    ftt = ft.match(data)
                    lst.append(
                        f'<img src="data:{ftt.mime};base64,{(base64.encodebytes(data)).decode("utf-8")}" width="720" />')
                except TypeError:
                    traceback.print_exc()
        if isinstance(m, Voice):
            lst.append('<div>[Voice]</div>')
        if isinstance(m, Embed):
            lst.append('<div>[Embed]</div>')

    pic = False

    d = {'content': html_template.replace('${content}', '\n'.join(lst)), 'element': '.botbox'}

    html_ = json.dumps(d)

    fname = random_cache_path() + '.html'
    with open(fname, 'w', encoding='utf-8') as fi:
        fi.write(d['content'])

    try:
        pic = await download_to_cache((web_render_local if use_local else web_render) + 'element_screenshot',
                                      status_code=200,
                                      headers={'Content-Type': 'application/json'},
                                      method="POST",
                                      post_data=html_,
                                      attempt=1,
                                      timeout=30,
                                      request_private_ip=True
                                      )
    except aiohttp.ClientConnectorError:
        if use_local:
            pic = await download_to_cache(web_render, method='POST', headers={
                'Content-Type': 'application/json',
            }, post_data=html_, request_private_ip=True)
        else:
            return False
    return pic
