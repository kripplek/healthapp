import os
import logging
from pwd import getpwnam
from grp import getgrnam

logger = logging.getLogger(__name__)


def drop_privs(user, group=None):
    logger.info('Changing user to %s', user)

    if isinstance(user, basestring):
        user = getpwnam(user).pw_uid

    # Do group first if we need to
    if group:
        if isinstance(group, basestring):
            group = getgrnam(group).gr_gid
        os.setgid(group)

    os.setuid(user)


def daemon_init(configs):
    setuid = configs.get('setuid')
    if setuid:
        drop_privs(setuid, configs.get('setgid'))

    # cd to / to avoid having file handles open where we shouldn't
    os.chdir('/')
