from core.loader.decorator import command
from core.elements import MessageSession

from modules.github import repo, user, search

@command('github', alias=['gh'], help_doc=['~github repo <name> {获取 GitHub 仓库信息}',
                   '~github (user|usr|organization|org) <name> {获取 GitHub 用户或组织信息}',
                   '~github search <query> {搜索 GitHub 上的仓库。}'])
async def github(msg: MessageSession):
    if msg.parsed_msg['repo']:
        return await repo(msg)
    elif msg.parsed_msg['(user|usr|organization|org)']:
        return await user(msg)
    elif msg.parsed_msg['search']:
        return await search(msg)
    else:
        return await msg.sendMessage('发生错误：指令使用错误，请选择 repo、user 或 search 工作模式。使用 ~help github 查看详细帮助。')