from core.helpers import timestamp, pad_title, plural, get_pref, get_filter
from core.localization import localization
from plex.plex_media_server import PlexMediaServer
from sync.manager import SyncManager

from datetime import datetime
from ago import human

L, LF = localization('interface.sync_menu')


# NOTE: pad_title(...) is used as a "hack" to force the UI to use 'media-details-list'

@route('/applications/trakttv/sync')
def SyncMenu(refresh=None):
    oc = ObjectContainer(title2=L('sync_menu:title'), no_history=True, no_cache=True)
    all_keys = []

    create_active_item(oc)

    oc.add(DirectoryObject(
        key=Callback(Synchronize),
        title=pad_title('Synchronize'),
        summary=get_task_status('synchronize'),
        thumb=R("icon-sync.png")
    ))

    f_allow, f_deny = get_filter('filter_sections')
    sections = PlexMediaServer.get_sections(['show', 'movie'], titles=f_allow)

    for _, key, title in sections:
        oc.add(DirectoryObject(
            key=Callback(Push, section=key),
            title=pad_title('Push "' + title + '" to trakt'),
            summary=get_task_status('push', key),
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push),
            title=pad_title('Push all to trakt'),
            summary=get_task_status('push'),
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(Pull),
        title=pad_title('Pull from trakt'),
        summary=get_task_status('pull'),
        thumb=R("icon-sync_down.png")
    ))

    return oc


def create_active_item(oc):
    task, handler = SyncManager.get_current()
    if not task:
        return

    # Format values
    remaining = format_remaining(task.statistics.seconds_remaining)
    progress = format_percentage(task.statistics.progress)

    # Title
    title = '%s - Status' % handler.title

    if progress:
        title += ' (%s)' % progress

    # Summary
    summary = task.statistics.message or 'Working'

    if remaining:
        summary += ', ~%s second%s remaining' % (remaining, plural(remaining))

    # Create items
    oc.add(DirectoryObject(
        key=Callback(SyncMenu, refresh=timestamp()),
        title=pad_title(title),
        summary=summary + ' (click to refresh)'
    ))

    oc.add(DirectoryObject(
        key=Callback(Cancel),
        title=pad_title('%s - Cancel' % handler.title)
    ))


def format_percentage(value):
    if not value:
        return None

    return '%d%%' % (value * 100)

def format_remaining(value):
    if not value:
        return None

    return int(round(value, 0))


def get_task_status(key, section=None):
    result = []

    status = SyncManager.get_status(key, section)

    if status.previous_timestamp:
        since = datetime.utcnow() - status.previous_timestamp

        if since.seconds < 1:
            result.append('Last run just a moment ago')
        else:
            result.append('Last run %s' % human(since, precision=1))

    if status.previous_elapsed:
        if status.previous_elapsed.seconds < 1:
            result.append('taking less than a second')
        else:
            result.append('taking %s' % human(
                status.previous_elapsed,
                precision=1,
                past_tense='%s'
            ))

    if status.previous_success is True:
        result.append('was successful')
    elif status.previous_timestamp:
        # Only add 'failed' fragment if there was actually a previous run
        result.append('failed')

    if len(result):
        return ', '.join(result) + '.'

    return 'Not run yet.'


@route('/applications/trakttv/sync/synchronize')
def Synchronize():
    success, message = SyncManager.trigger_synchronize()

    if not success:
        return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Synchronize')
    )



@route('/applications/trakttv/sync/push')
def Push(section=None):
    success, message = SyncManager.trigger_push(section)

    if not success:
        return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Push')
    )


@route('/applications/trakttv/sync/pull')
def Pull():
    success, message = SyncManager.trigger_pull()

    if not success:
        return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Pull')
    )


@route('/applications/trakttv/sync/cancel')
def Cancel():
    if not SyncManager.cancel():
        return MessageContainer(
            L('cancel_failure:title'),
            L('cancel_failure:message'),
        )

    return MessageContainer(
        L('cancel_success:title'),
        L('cancel_success:message')
    )
