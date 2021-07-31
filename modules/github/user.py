import traceback

from core.elements import MessageSession

from modules.github.utils import query, time_diff, dirty_check, darkCheck

async def user(msg: MessageSession):
    try:
        result = await query('https://api.github.com/users/' + msg.parsed_msg['name'], 'json')
        optional = []
        if 'hireable' in result and result['hireable'] is True:
            optional.append('Hireable')
        if 'is_staff' in result and result['is_staff'] is True:
            optional.append('GitHub Staff')
        if 'company' in result:
            optional.append('Work · ' + result['company'])
        if 'twitter_username' in result:
            optional.append('Twitter · ' + result['twitter_username'])
        if 'blog' in result:
            optional.append('Site · ' + result['blog'])
        if 'location' in result:
            optional.append('Location · ' + result['location'])

        bio = result['bio']
        if bio is None:
            bio = ''
        else:
            bio = '\n' + result['bio']

        optional_text = '\n' + ' | '.join(optional)
        msg = f'''{result['login']} aka {result['name']} ({result['id']}){bio}
    
Type · {result['type']} | Follower · {result['followers']} | Following · {result['following']} | Repo · {result['public_repos']} | Gist · {result['public_gists']}{optional_text}
Account Created {time_diff(result['created_at'])} ago | Latest activity {time_diff(result['updated_at'])} ago
    
result['html_url']'''

        is_dirty = await dirty_check(msg, result['login']) or darkCheck(msg)
        if is_dirty:
            msg = 'https://wdf.ink/6OUp'

        await msg.sendMessage(msg)
    except Exception as error:
        await msg.sendMessage('发生错误：' + str(error))
        traceback.print_exc()