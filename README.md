# plugin.video.iptvsimple.addons

* Kodi 18 only.

* Add addon streams to IPTV Simple Client.
* Merge playlists into single m3u file.
* Merge xmltv epg source into single epg xml file.

# Instructions
## m3u

* If you already have IPTV Simple Client set to use a url m3u playlist:

`M3U Playlists \ right click \ Add IPTV Simple Client M3U \ URL \ OK`

* Then either add or subscribe to a channel or group. You can add a search too.

* This will create a stream template which you can edit various attributes and move the items around.

* Update the Streams to generate the final streams.m3u8 playlist.

* You can use the Streams context menu to set IPTV Simple Client to use it.

* After you have created the xml epg you can map missing streams to channels in Streams.

## epg xml

* Add epg xml sources or the current IPTV Simple Client EPG URL.

* Add or subscribe to all or some of the channels.

* You will need to set the location of busybox in Settings if you use xz compressed files.

* Update the channels to generate the xmltv.xml file.

* You can then change the Streams with missing epg data to use the new epg channels.

## Automatic Updates

* Use the Service settings to do an automatic Streams and Channels Update.

* The update will disable and enable IPTV Simple Client to get it to refresh the channels from the m3u.

* The epg in IPTV Simple Client might not get immediately updated.

* Clear the Guide in Kodi \ Settings \ PVR \ Guide \ Clear Data  to get it to load stuck data.
