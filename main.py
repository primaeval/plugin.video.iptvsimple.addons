from xbmcswift2 import Plugin
import re
import requests
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import xbmcplugin
import base64
import random
import urllib,urlparse
import time,datetime,calendar
import threading
import subprocess
import json
import os,os.path
import stat
import platform
import pickle
#import lzma
from HTMLParser import HTMLParser
from rpc import RPC
from bs4 import BeautifulSoup
import collections
import operator

plugin = Plugin()
big_list_view = False

def decode(x):
    try: return x.decode("utf8")
    except: return x

def addon_id():
    return xbmcaddon.Addon().getAddonInfo('id')

def log(v):
    xbmc.log(repr(v),xbmc.LOGERROR)

#log(sys.argv)

def profile():
    return xbmcaddon.Addon().getAddonInfo('profile')

def get_icon_path(icon_name):
    if plugin.get_setting('user.icons') == "true":
        user_icon = "special://profile/addon_data/%s/icons/%s.png" % (addon_id(),icon_name)
        if xbmcvfs.exists(user_icon):
            return user_icon
    return "special://home/addons/%s/resources/img/%s.png" % (addon_id(),icon_name)

def remove_formatting(label):
    label = re.sub(r"\[/?[BI]\]",'',label)
    label = re.sub(r"\[/?COLOR.*?\]",'',label)
    return label

def escape( str ):
    str = str.replace("&", "&amp;")
    str = str.replace("<", "&lt;")
    str = str.replace(">", "&gt;")
    str = str.replace("\"", "&quot;")
    return str

def unescape( str ):
    str = str.replace("&lt;","<")
    str = str.replace("&gt;",">")
    str = str.replace("&quot;","\"")
    str = str.replace("&amp;","&")
    return str


@plugin.route('/iptvsimple_streams1')
def iptvsimple_streams1():
    channels_m3u = 'special://profile/addon_data/plugin.video.iptvsimple.addons/channels.m3u8'
    if plugin.get_setting('use.iptv.m3u.url',bool):
        url = xbmcaddon.Addon('pvr.iptvsimple').getSetting('m3uUrl')
        if url:
            filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/iptvsimple.m3u'
            if "m3u8" in url:
                filename += '8'
            xbmcvfs.copy(url,filename)
            f = xbmcvfs.File(filename)
            data = f.read()
            f.close()
            f = xbmcvfs.File(channels_m3u,'w')
            f.write(data)
            f.close()
    f = xbmcvfs.File(channels_m3u)
    data = f.read()
    f.close()
    #log(data)
    channels = re.findall('(#EXTINF.*?)\r?\n(.*?)\r?\n',data,flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        items.append({
            'label':name,
            'path' : url,
            'is_playable': True,
            'info_type': 'Video',
            'info':{"title": name}
        })
    return items


@plugin.route('/iptvsimple_streams')
def iptvsimple_streams():
    url = xbmcaddon.Addon('pvr.iptvsimple').getSetting('m3uUrl')
    #log(url)
    if url:
        filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/iptvsimple.m3u'
        xbmcvfs.copy(url,filename)
        f = xbmcvfs.File(filename)
        data = f.read()
        f.close()
    else:
        return

    channels = re.findall('(#EXTINF.*?)\r?\n(.*?)\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        items.append({
            'label':name,
            'path' : url,
            'is_playable': True,
            'info_type': 'Video',
            'info':{"title": name}
        })
    return items


#@plugin.cached(TTL=plugin.get_setting('ttl',int))
def get_directory(media,path):
    try:
        response = RPC.files.get_directory(media=media, directory=path, properties=["thumbnail"])
        #log(response)
        return response
    except Exception as e:
        #log(e)
        return {"files":[]}


@plugin.route('/folder/<path>/<label>')
def folder(path,label):
    #recordings = plugin.get_storage('recordings')
    #favourites = plugin.get_storage('favourites')
    #trakt_movies = plugin.get_storage('trakt_movies')
    #trakt_shows = plugin.get_storage('trakt_shows')
    label = label.decode("utf8")
    #log(path)
    #folders = plugin.get_storage('folders')
    media = "video"
    response = get_directory(media,path)
    files = response["files"]
    dir_items = []
    file_items = []
    for f in files:
        file_label = remove_formatting(f['label'])
        url = f['file']
        thumbnail = f['thumbnail']
        if not thumbnail:
            thumbnail = get_icon_path('unknown')

        if f['filetype'] == 'directory':
            if media == "video":
                window = "10025"
            elif media in ["music","audio"]:
                window = "10502"
            else:
                window = "10001"
            context_items = []
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_all_folder, path=url, label=file_label.encode("utf8")))))
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Subscribe All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(subscribe_all_folder, path=url, label=file_label.encode("utf8")))))
            #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Record', 'XBMC.RunPlugin(%s)' % (plugin.url_for(record_folder, path=url, label=file_label.encode("utf8")))))
            #if url in favourites:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove Favourite', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_favourite_folder, path=url))))
            #else:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Favourite', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_favourite_folder, path=url, label=file_label.encode("utf8")))))
            #if url in trakt_movies:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove Trakt Movies Folder', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_trakt_movie_folder, path=url))))
            #else:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Trakt Movies Folder', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_trakt_movie_folder, path=url, label=file_label.encode("utf8")))))
            #if url in trakt_shows:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove Trakt Shows Folder', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_trakt_shows_folder, path=url))))
            #else:
                #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Trakt Shows Folder', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_trakt_shows_folder, path=url, label=file_label.encode("utf8")))))

            dir_label = "[B]%s[/B]" % file_label

            dir_items.append({
                'label': dir_label,
                'path': plugin.url_for('folder', path=url, label=file_label.encode("utf8")),
                'thumbnail': f['thumbnail'],
                'context_menu': context_items,
            })
        else:
            record_label = "[%s] %s" % (label,file_label)


            context_items = []
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_folder_stream, path=url, label=label.encode("utf8"), name=file_label.encode("utf8"),  thumbnail=f['thumbnail']))))
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Search', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_folder_search, path=path, label=label.encode("utf8"), name=file_label.encode("utf8"),  thumbnail=f['thumbnail']))))
            #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Record', 'XBMC.RunPlugin(%s)' % (plugin.url_for(record, url=url, label=record_label.encode("utf8")))))
            #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Favourite', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_favourite_folder, path=url, label=record_label.encode("utf8")))))

            #if record_label in recordings.values():
                #record_label = "[COLOR yellow]%s[/COLOR]" % record_label
                #display_label = "[COLOR yellow]%s[/COLOR]" % file_label
            #else:
            display_label = "%s" % file_label

            file_items.append({
                'label': display_label,
                'path': url,
                'thumbnail': f['thumbnail'],
                'context_menu': context_items,
                'is_playable': True,
                'info_type': 'Video',
                'info':{"mediatype": "episode", "title": file_label}
            })

    return dir_items + file_items


@plugin.route('/folder_search/<path>/<name>')
def folder_search(path,name):
    media = "video"
    response = get_directory(media,path)
    files = response["files"]
    dir_items = []
    file_items = []
    items = []
    for f in files:
        file_label = remove_formatting(f['label'])
        url = f['file']
        thumbnail = f['thumbnail']
        if not thumbnail:
            thumbnail = get_icon_path('unknown')

        if f['filetype'] == 'file':
            if re.search(name,file_label,flags=re.I):
                items.append((file_label,url))
    if items:
        names = [x[0] for x in items]
        select = xbmcgui.Dialog().select(name,names)
        if select != -1:
            url = items[select][1]
            plugin.set_resolved_url(url)




@plugin.route('/m3u/<url>/<name>')
def m3u(url,name):
    if url:
        filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/temp.m3u'
        xbmcvfs.copy(url,filename)
        f = xbmcvfs.File(filename)
        data = f.read()
        f.close()
    else:
        return

    channels = re.findall('((#EXTINF.*?)\r?\n(.*?)\r?\n)', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for channel,info,path in channels:
        #log(url)
        channel_name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            channel_name = split[1]
        id = ""
        match = re.search('tvg-id="(.*?)"',info,flags=re.I)
        if match:
            id = match.group(1)
        group = ""
        match = re.search('group-title="(.*?)"',info,flags=re.I)
        if match:
            group = match.group(1)
        context_items = []
        #log(channel)
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_m3u_stream, channel=channel))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Group', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_m3u_group, url=url, group=group))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Subscribe Group', 'XBMC.RunPlugin(%s)' % (plugin.url_for(subscribe_m3u_group, url=url, group=group, name=name))))
        items.append({
            'label':"%s - [COLOR dimgray]%s[/COLOR] - %s" % (channel_name,id,group),
            'path' : path,
            'is_playable': True,
            'info_type': 'Video',
            'info':{"title": channel_name},
            'context_menu': context_items,
        })
    return items

@plugin.route('/streams')
def streams():
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    data = get_data(filename) or ""
    channels = re.findall('((#EXTINF.*?)\r?\n(.*?)\r?\n)', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for channel,info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        id = ""
        match = re.search('tvg-id="(.*?)"',info,flags=re.I)
        if match:
            id = match.group(1)
        group = ""
        match = re.search('group-title="(.*?)"',info,flags=re.I)
        if match:
            group = match.group(1)
        context_items = []
        #log(channel)
        #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit Name', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_name, channel=channel))))
        #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit id', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_id, channel=channel))))
        #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit tvg-name', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_tvg_name, channel=channel))))
        #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit Group', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_group, channel=channel))))
        items.append({
            'label':"%s - [COLOR dimgray]%s[/COLOR] - %s" % (name,id,group),
            'path' : url,
            'is_playable': True,
            'info_type': 'Video',
            'info':{"title": name},
            'context_menu': context_items,
        })
    return items


@plugin.route('/template')
def template():
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    data = get_data(filename) or ""
    channels = re.findall('((#EXTINF.*?)\r?\n(.*?)\r?\n)', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for channel,info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        id = ""
        match = re.search('tvg-id="(.*?)"',info,flags=re.I)
        if match:
            id = match.group(1)
        group = ""
        match = re.search('group-title="(.*?)"',info,flags=re.I)
        if match:
            group = match.group(1)
        context_items = []
        #log(channel)
        path = url
        playable = True
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Move Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(move_stream, channel=channel))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_stream, channel=channel))))
        if name != "SUBSCRIBE":
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit Name', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_name, channel=channel))))
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit id', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_id, channel=channel))))
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit tvg-name', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_tvg_name, channel=channel))))
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Edit Group', 'XBMC.RunPlugin(%s)' % (plugin.url_for(edit_stream_group, channel=channel))))
        else:
            playable = False
            if not url.startswith('plugin'):
                path = plugin.url_for('m3u',url=url,name=id)

        #log(path)
        items.append({
            'label':"%s - [COLOR dimgray]%s[/COLOR] - %s" % (name,id,group),
            'path' : path,
            'is_playable': playable,
            'info_type': 'Video',
            'info':{"title": name},
            'context_menu': context_items,
        })
    return items

def get_data(url):
    if url:
        filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/temp.m3u'
        xbmcvfs.copy(url,filename)
        f = xbmcvfs.File(filename)
        data = f.read()
        f.close()
        if data:
            return data + '\n'
    else:
        return

@plugin.route('/add_all_streams/<url>')
def add_all_streams(url):
    data = get_data(url)
    if not data:
        return
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"
    channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    for channel in channels:
        original += channel
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/add_m3u_group/<url>/<group>')
def add_m3u_group(url,group):
    data = get_data(url)
    if not data:
        return
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"
    channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    for channel in channels:
        channel_group = ""
        match = re.search('group-title="(.*?)"',channel,flags=re.I)
        if match:
            channel_group = match.group(1)
        if channel_group == group:
            original += channel
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/add_all_folder/<path>/<label>')
def add_all_folder(path,label):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    match = re.search('plugin://(.*?)/',path)
    if match:
        plugin = match.group(1)
        plugin_name = xbmcaddon.Addon(plugin).getAddonInfo('name')
        label = "%s - %s" % (plugin_name,label)

    media = "video"
    response = get_directory(media,path)
    files = response["files"]
    dir_items = []
    file_items = []
    for f in files:
        file_label = remove_formatting(f['label'])
        url = f['file']
        thumbnail = f['thumbnail']
        if not thumbnail:
            thumbnail = get_icon_path('unknown')
        if f['filetype'] == 'file':
            channel = '#EXTINF:-1 tvg-name="%s" tvg-id="%s" tvg-logo="%s" group-title="%s",%s\n%s\n' % (file_label,file_label,thumbnail,label,file_label,url)
            original += channel.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/subscribe_all_folder/<path>/<label>')
def subscribe_all_folder(path,label):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    match = re.search('plugin://(.*?)/',path)
    if match:
        plugin = match.group(1)
        plugin_name = xbmcaddon.Addon(plugin).getAddonInfo('name')
        label = "%s - %s" % (plugin_name,label)

    channel = '#EXTINF:-1 group-title="%s",SUBSCRIBE\n%s\n' % (label,path)
    original += channel

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/add_folder_stream/<path>/<label>/<name>/<thumbnail>')
def add_folder_stream(path,label,name,thumbnail):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    match = re.search('plugin://(.*?)/',path)
    if match:
        addon = match.group(1)
        addon_name = xbmcaddon.Addon(addon).getAddonInfo('name')
        label = "%s - %s" % (addon_name,label)

    channel = '#EXTINF:-1 tvg-name="%s" tvg-id="%s" tvg-logo="%s" group-title="%s",%s\n%s\n' % (name,name,thumbnail,label,name,path)
    original += channel.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/add_folder_search/<path>/<label>/<name>/<thumbnail>')
def add_folder_search(path,label,name,thumbnail):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    match = re.search('plugin://(.*?)/',path)
    if match:
        addon = match.group(1)
        addon_name = xbmcaddon.Addon(addon).getAddonInfo('name')
        label = "%s - %s" % (addon_name,label)

    new_name = xbmcgui.Dialog().input('%s (regex)' % (name),name)
    if not new_name:
        return
    name = new_name

    path = plugin.url_for('folder_search',name=name,path=path)

    channel = '#EXTINF:-1 tvg-name="%s" tvg-id="%s" tvg-logo="%s" group-title="%s",%s\n%s\n' % (name,name,thumbnail,label,name,path)
    original += channel.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/add_m3u_stream/<channel>')
def add_m3u_stream(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    original += channel #.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/remove_stream/<channel>')
def remove_stream(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    original = original.replace(channel,'')

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/move_stream/<channel>')
def move_stream(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    original = original.replace(channel,'')

    channels = re.findall('((#EXTINF.*?)\r?\n(.*?)\r?\n)', original, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for new_channel,info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
            items.append((name,new_channel))
    select = xbmcgui.Dialog().select('%s (move after)',[x[0] for x in items])
    if select == -1:
        return
    original = original.replace(items[select][1],items[select][1]+channel)

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/edit_stream_name/<channel>')
def edit_stream_name(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    new_channel = None
    match = re.search('(#EXTINF.*?)\r?\n(.*?)\r?\n', channel, flags=(re.I|re.DOTALL|re.MULTILINE))
    if match:
        info = match.group(1)
        url = match.group(2)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
            extinf = split[0]
            new_name = xbmcgui.Dialog().input('Edit',name)
            if new_name:
                new_info = "%s,%s" %(extinf,new_name)
                new_channel = channel.replace(info,new_info)

    #return
    if not new_channel:
        return

    original = original.replace(channel,new_channel)

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/edit_stream_id/<channel>')
def edit_stream_id(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    new_channel = None
    match = re.search('(#EXTINF.*?)\r?\n(.*?)\r?\n', channel, flags=(re.I|re.DOTALL|re.MULTILINE))
    if match:
        info = match.group(1)
        url = match.group(2)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
            extinf = split[0]
            match = re.search('tvg-id="(.*?)"',extinf,flags=re.I)
            if match:
                tvg_id = match.group(0)
                id = match.group(1)
                new_id = xbmcgui.Dialog().input('Edit id',id)
                if new_id:
                    new_channel = channel.replace(tvg_id,tvg_id.replace(id,new_id))

    #return
    if not new_channel:
        return

    original = original.replace(channel,new_channel)

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/edit_stream_group/<channel>')
def edit_stream_group(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    new_channel = None
    match = re.search('(#EXTINF.*?)\r?\n(.*?)\r?\n', channel, flags=(re.I|re.DOTALL|re.MULTILINE))
    if match:
        info = match.group(1)
        url = match.group(2)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
            extinf = split[0]
            match = re.search('group-title="(.*?)"',extinf,flags=re.I)
            if match:
                tvg_id = match.group(0)
                id = match.group(1)
                new_id = xbmcgui.Dialog().input('Edit group',id)
                if new_id:
                    new_channel = channel.replace(tvg_id,tvg_id.replace(id,new_id))

    #return
    if not new_channel:
        return

    original = original.replace(channel,new_channel)

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/edit_stream_tvg_name/<channel>')
def edit_stream_tvg_name(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"

    new_channel = None
    match = re.search('(#EXTINF.*?)\r?\n(.*?)\r?\n', channel, flags=(re.I|re.DOTALL|re.MULTILINE))
    if match:
        info = match.group(1)
        url = match.group(2)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
            extinf = split[0]
            match = re.search('tvg-name="(.*?)"',extinf,flags=re.I)
            if match:
                tvg_id = match.group(0)
                id = match.group(1)
                new_id = xbmcgui.Dialog().input('Edit tvg-name',id)
                if new_id:
                    new_channel = channel.replace(tvg_id,tvg_id.replace(id,new_id))

    #return
    if not new_channel:
        return

    original = original.replace(channel,new_channel)

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/update_streams/')
def update_streams():
    url = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    data = get_data(url)
    if not data:
        return
    original = "#EXTM3U\n"
    channels = re.findall('((#EXTINF.*?)\r?\n(.*?)\r?\n)', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    items = []
    #log(channels)
    for channel,info,url in channels:
        #log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        id = ""
        match = re.search('tvg-id="(.*?)"',info,flags=re.I)
        if match:
            id = match.group(1)
        group = ""
        match = re.search('group-title="(.*?)"',info,flags=re.I)
        if match:
            group = match.group(1)
        if name == "SUBSCRIBE":
            if url.startswith('plugin'):
                match = re.search('group-title="(.*?)"',info,flags=re.I)
                if match:
                    label = match.group(1)

                media = "video"
                response = get_directory(media,url)
                files = response["files"]
                dir_items = []
                file_items = []
                for f in files:
                    file_label = remove_formatting(f['label'])
                    url = f['file']
                    thumbnail = f['thumbnail']
                    if not thumbnail:
                        thumbnail = get_icon_path('unknown')
                    if f['filetype'] == 'file':
                        channel = '#EXTINF:-1 tvg-name="%s" tvg-id="%s" tvg-logo="%s" group-title="%s",%s\n%s\n' % (file_label,file_label,thumbnail,label,file_label,url)
                        original += channel.encode("utf8")
            else:
                data = get_data(url)
                new_channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
                if group:
                    for new_channel in new_channels:
                        match = re.search('group-title="(.*?)"',new_channel,flags=re.I)
                        if match:
                            new_group = match.group(1)
                            if new_group == group:
                                #log(group)
                                original += new_channel
                else:
                    for new_channel in new_channels:
                        #log(new_channel)
                        original += new_channel
        else:
            original += channel
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/clear_streams/')
def clear_streams():
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    f = xbmcvfs.File(filename,'w')
    f.close()


@plugin.route('/subscribe_all_streams/<url>/<name>')
def subscribe_all_streams(url,name):
    data = get_data(url)
    if not data:
        return
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"
    channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    channel = '#EXTINF:-1 tvg-id="%s",SUBSCRIBE\n%s\n' % (name,url)
    original += channel
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()

@plugin.route('/subscribe_m3u_group/<url>/<group>/<name>')
def subscribe_m3u_group(url,group,name):
    data = get_data(url)
    if not data:
        return
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'
    original = get_data(filename) or "#EXTM3U\n"
    channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    channel = '#EXTINF:-1 tvg-id="%s" group-title="%s",SUBSCRIBE\n%s\n' % (name,group,url)
    original += channel
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()


@plugin.route('/m3u_playlists')
def m3u_playlists():
    m3us = plugin.get_storage('m3us')
    items = []
    for url,name in m3us.items():
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_all_streams,url=url))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Subscribe All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(subscribe_all_streams,url=url,name=name.encode("utf8")))))
        items.append({
            'label': name,
            'path': plugin.url_for('m3u',url=url, name=name),
            'context_menu': context_items,
        })

    return items

@plugin.route('/add_iptvsimple_m3u')
def add_iptvsimple_m3u():
    m3us = plugin.get_storage('m3us')
    which = xbmcgui.Dialog().select('IPTV Simple Client M3U',["URL","File"])
    if which == -1:
        return
    if which == 0:
        url = xbmcaddon.Addon('pvr.iptvsimple').getSetting('m3uUrl')
        if url:
            name = xbmcgui.Dialog().input("Name","IPTV Simple Client URL")
            if name:
                m3us[url] = name
    elif which == 0:
        url = xbmcaddon.Addon('pvr.iptvsimple').getSetting('m3uPath')
        if url:
            name = xbmcgui.Dialog().input("Name","IPTV Simple Client File")
            if name:
                m3us[url] = name

@plugin.route('/add_m3u_url')
def add_m3u_url():
    m3us = plugin.get_storage('m3us')
    url = xbmcgui.Dialog().input('M3U URL')
    if url:
        name = xbmcgui.Dialog().input("Name")
        if name:
            m3us[url] = name

@plugin.route('/add_m3u_file')
def add_m3u_file():
    m3us = plugin.get_storage('m3us')
    path = xbmcgui.Dialog().browseSingle(1, 'M3U', '', '', False, False)
    if path:
        name = xbmcgui.Dialog().input("Name")
        if name:
            m3us[path] = name

@plugin.route('/set_iptvsimple_m3u_file')
def set_iptvsimple_m3u_file():
    xbmcaddon.Addon('pvr.iptvsimple').setSetting('m3uPathType',"0")
    xbmcaddon.Addon('pvr.iptvsimple').setSetting('m3uPath',xbmc.translatePath('special://profile/addon_data/plugin.video.iptvsimple.addons/template.m3u8'))


@plugin.route('/')
def index():
    items = []

    context_items = []
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add IPTV Simple Client M3U', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_iptvsimple_m3u))))
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add M3U URL', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_m3u_url))))
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add M3U File', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_m3u_file))))
    items.append(
    {
        'label': "M3U Playlists",
        'path': plugin.url_for('m3u_playlists'),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })
    context_items = []
    items.append(
    {
        'label': "Library",
        'path': plugin.url_for('folder',path="library://video",label="Library"),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })
    context_items = []
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Clear', 'XBMC.RunPlugin(%s)' % (plugin.url_for(clear_streams))))
    items.append(
    {
        'label': "Stream Template",
        'path': plugin.url_for('template'),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })
    context_items = []
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Update', 'XBMC.RunPlugin(%s)' % (plugin.url_for(update_streams))))
    context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Set as IPTV File M3U', 'XBMC.RunPlugin(%s)' % (plugin.url_for(set_iptvsimple_m3u_file))))
    items.append(
    {
        'label': "Streams",
        'path': plugin.url_for('streams'),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })
    context_items = []
    items.append(
    {
        'label': "EPG Program Sources",
        #'path': plugin.url_for('epg_sources'),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })

    return items



if __name__ == '__main__':
    plugin.run()
