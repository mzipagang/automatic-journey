from logging import Filter

from app.common.context.context import user_context
from app.common.context.context_vars import UserContextVarNames


class UsernameFilter(Filter):
    def filter(self, record):
        username = 'Unset'
        user_info = user_context.get()
        if isinstance(user_info, dict) and UserContextVarNames.USERNAME.value in user_info.keys():
            username = user_info[UserContextVarNames.USERNAME.value]
        record.usr = {'name': username}
        return True
