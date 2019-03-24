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
        log(url)
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
    log(url)
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
        log(url)
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
        log(response)
        return response
    except Exception as e:
        log(e)
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
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_folder_stream, path=path, label=label.encode("utf8"), name=file_label.encode("utf8"),  thumbnail=f['thumbnail']))))
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

@plugin.route('/m3u/<url>')
def m3u(url):
    if url:
        filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/temp.m3u'
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
        log(url)
        name = None
        split = info.rsplit(',',1)
        #log((info,split))
        if len(split) == 2:
            name = split[1]
        context_items = []
        channel = info + '\n' + url + '\n'
        log(channel)
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add Stream', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_m3u_stream, channel=channel))))            
        items.append({
            'label':name,
            'path' : url,
            'is_playable': True,
            'info_type': 'Video',
            'info':{"title": name},
            'context_menu': context_items,
        })
    return items
    
@plugin.route('/streams')
def streams():
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    data = get_data(filename)
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
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    original = get_data(filename)
    channels = re.findall('#EXTINF.*?\r?\n.*?\r?\n', data, flags=(re.I|re.DOTALL|re.MULTILINE))
    for channel in channels:
        original += channel
    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()
  

@plugin.route('/add_all_folder/<path>/<label>')
def add_all_folder(path,label):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    original = get_data(filename) or ""

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


@plugin.route('/add_folder_stream/<path>/<label>/<name>/<thumbnail>')
def add_folder_stream(path,label,name,thumbnail):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    original = get_data(filename) or ""

    match = re.search('plugin://(.*?)/',path)
    if match:
        plugin = match.group(1)
        plugin_name = xbmcaddon.Addon(plugin).getAddonInfo('name')
        label = "%s - %s" % (plugin_name,label)   

    channel = '#EXTINF:-1 tvg-name="%s" tvg-id="%s" tvg-logo="%s" group-title="%s",%s\n%s\n' % (name,name,thumbnail,label,name,path)
    original += channel.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close()  


@plugin.route('/add_m3u_stream/<channel>')
def add_m3u_stream(channel):
    filename = 'special://profile/addon_data/plugin.video.iptvsimple.addons/streams.m3u8'
    original = get_data(filename) or ""

    original += channel #.encode("utf8")

    f = xbmcvfs.File(filename,'w')
    f.write(original)
    f.close() 

@plugin.route('/subscribe_all_streams/<url>')
def subscribe_all_streams(url):
    pass
    x = 1


@plugin.route('/m3u_playlists')
def m3u_playlists():
    m3us = plugin.get_storage('m3us')
    items = []
    for url,name in m3us.items():
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_all_streams,url=url))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Subscribe All Streams', 'XBMC.RunPlugin(%s)' % (plugin.url_for(subscribe_all_streams,url=url))))
        items.append({
            'label': name,
            'path': plugin.url_for('m3u',url=url),
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
    items.append(
    {
        'label': "Streams",
        'path': plugin.url_for('streams'),
        'thumbnail':get_icon_path('tv'),
        'context_menu': context_items,
    })       
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
