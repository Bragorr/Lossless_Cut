#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
common.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

## Standard library imports
import os
import re

__author__ = 'R.D. Vaughan <rdvLaunchpad@gmail.com>'
__date__ = '$03/09/2012'
__version__ = '0.2.2'
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Changed:
#       lossless_cut.py - Handle the lack of a "streamid" when there is
#       only a single "Text" subtitle track
#       lossless_cut.py - Changed the extraction of the subtitle track
#       "subid" to properly handle varying number of digits
#       lossless_cut.py - Made the gathering of subtitle extraction data
#       more resilient. Skip subtitle tracks that
#       cannot be handled instead of aborting.
#       utilities.py - Dependency checks now displays any error output
#       ll_report.py - Fixed identification of the MythTV version
#       common.py - Changed the mythccextractor arguments from
#       quite to verbose
# 0.1.3 mythtvinterface - Refresh the recorded record markup data
#       after a cutlist was generated otherwise
#       the markup data is inaccurate
#       mythtvinterface - Fix a bug when the seektable does not have
#       a zero keyframe and the first cut point keyframe is being
#       changed to one higher than it should be
#       ll_report.py - Added Manufacturer and Model columns to wiki table
#       common.py - Added Manufacturer and Model columns to wiki table
#       common.py - Fixed the URL variable for the supported
#       and unsupport wiki device table
# 0.1.4 Fixed a bug where the removal of the old recording
#       option "delete_old" was being ignore when the replace "-r"
#       option was used.
#       Added edits for missing fps, first and last frames which
#       indicate that the recording does not have valid database
#       records. If these edits do not pass a message is sent added
#       the log and displayed on the console then the script
#       aborts with a error return code.
# 0.1.5 lossless_cut.py - For consistency added surrounding quotes
#       to the first video path and filename in a merge list. If
#       uses can ever add their own recorded videos with proper
#       seek tables then this would have caused an abort.
#       Trapped an abort where the lossless_cut.cfg file could not be
#       created due to R/W permissions issue with "~/.mythtv"
#       Added a "-D" delay option to change when the video track starts
#       playing by a positive or negative number of milliseconds
#       Added a "-X" option to force use of mythccextractor as the primary
#       utility to extract and convert subtitles tracks
#       into srt format.
#       Added the "-C" Concert Cuts processing command line option which
#       takes each cut and creates individual video-audio and/or audio only
#       files. The segment names are optionally specified in a "segment.cfg"
#       file.
#       Added a Concert Cut default format string.
#       Added "-T" audio track selection used in conjunction with the
#       "-S" Strip option to specify which among multiple audio tracks
#       to include in the final lossless cut file.
#       Added a new command line option to ccextractor for HDHomerun 'EIA'
#       format subtitles. New option is '-noteletext'
#       ccextractor32bit and ccextractor64bit executables have been updated
#       with support for HDHomerun 'EIA' format subtitles
#       Added support for a Remove Recording configuration section both
#       adding to an existing config file, varible validation and removing
#       recording that match the configuration settings
# 0.1.6 For new installs the creation of the "~/.mythtv/lossless_cut.cfg"
#       file caused an abort.
#       If the "-f" file path started with a tilde character the path
#       was not being expanded with the user's home directory.
#       The source package did not include the new files added in the
#       v0.1.5 release
# 0.1.7 Removed several SQL calls and use the MythTV python bindings instead
#       which reduced the need to deal with UTC start and end times changes
#       in MythTV v0.26 and higher
#       Added a new configuration file section called
#       "mkvmerge_user_settings". This section allows a user to
#       customize the command line for either/or the mkvmerge cut or
#       merge processing. This is an "use at your own risk" set of
#       variables.
#       Made a common routine to create a lossless_cut.cfg file and
#       removed redundant code in lossless_cut.py, keyframe_adjust.py
#       and ll_report.py
#       With a "-r" replace lossless_cut.py renames the original
#       recording with an added ".old" rather than ".Old" to be
#       consistent with mythtranscode's similar function
#       Added check for the minimum MythTV install which is v0.24+fixes
#       Added check for pre MythTV release versions that cannot be supported
#       Added a check for the UTCTZ datetime class when MythTV v0.26 and
#       higher
#       With a concert cut that does not have a subtitle, remove the
#       subtitle from the file name format string.
# 0.1.8 Add automatic generation of a cut list when it is empty and there is
#       a skip list. Saves the redundant effort of manually
#       loading the skip list through the MythTV edit UI.
# 0.1.9 Changed automatic generation of a cut list to be optional. It can now
#       be invoked by adding the command line switch "-g"
#       to keyframe_adjust.py. The default is no automatic cut
#       list generation.
# 0.2.0 Bug Fix:
#       Acquire the fps, height, width from mediainfo rather than the
#       recorded markup table. This is because those records are not
#       created by MythTV when a scheduled recording occurs when a user
#       is watching LiveTV.
#       Added a new configuration section "error_detection" which allows
#       a user to specific bash commands that are run against the log
#       before processing is completed. This feature is primarily used
#       to detect video file corruption and prevent deletion/replacement
#       of a recording.
#       Added the command line -j option for inclusion of the JobID
#       "%JOBID%" variable passed by MythTV. This is a required parameter
#       if the new configuration "error_detection" variables are used.
#       Remove all commented out code in anticipation that this release
#       will be the end of the beta and a move to maintenance mode.
# 0.2.1 Bug Fix:
#       Changed all abort condition exit codes so
#       that MythTV properly updates the jobqueue status to Errored.
#       The lossless_cut and keyframe_adjust shell scripts had hard coded
#       return values. This was changed to return the return values
#       actually generated by the two Lossless Cut user jobs.
#       Change:
#       lossless_cut.py will only generate a missing cut list from
#       a skip list when the new "-g" command line option is present.
#       Previosuly lossless_cut.py automatically generate a cutlist
#       from a skip list when no cut list existed.
# 0.2.2 Bug Fix:
#       Handle abort when mediainfo cannot find a video's duration.
#       The issue is likely caused by a corrupt recording.
#
__copyright__ = 'Copyright (c) 2012 R.D. Vaughan'
__license__ = 'GPLV2'
__url__ = 'http://www.mythtv.org/wiki/lossless_cut'


def is_package():
    """ Check if the code is being run
    as part of a distributed package or from source.
    """
    return __file__.find('src') < 0

# System variables
VERSION = __version__
APP = 'lossless_cut'
APPNAME = 'LossLess_Cut'
APPDIR = os.path.dirname(\
        os.path.realpath(__file__)).replace(u'importcode', u'')
#
CONFIG_DIR = u'%s/.mythtv' \
    % os.path.expanduser(u"~")
CONFIG_FILE = u'%s/lossless_cut.cfg' % CONFIG_DIR
INIT_CONFIG_FILE = u'%simportcode/init_config.cfg' % APPDIR
INIT_DVB_SUBTITLE_CONFIG_FILE = u'%simportcode/init_dvb_subtitle.cfg' % APPDIR
INIT_REMOVE_RECORDING_CONFIG_FILE = \
            u'%simportcode/init_remove_recording.cfg' % APPDIR
INIT_MKVMERGE_USER_SETTINGS_CONFIG_FILE = \
            u'%simportcode/init_mkvmerge_user_settings.cfg' % APPDIR
INIT_ERROR_DETECTION_CONFIG_FILE = \
            u'%simportcode/init_error_detection.cfg' % APPDIR
INIT_PROJECTX_INI_FILE = u'%simportcode/init_ProjectX.ini' % APPDIR
PROJECTX_INI_PATH = u'%(workpath)s/%(recorded_name)s.ini'
#
APPENDTO_FORMAT = u'%d:%d:%d:%d'
DATETIME_SQL_FORMAT = '%Y-%m-%d %H:%M:%S'
#
## Version support is v0.24+fixes and the current git master is the
## only pre-release that can be supported
SUPPORTED_VERSIONS = 24
UNSUPPORTED_PRE_VERSION = 26
#
## plus or minus video track deplay in millseconds
VIDEO_TRACK_DELAY = u' --sync 0:%d'
#
## String which identifies track info from mkvmerge --identity command
TRACK_ID = u'Track ID'
## Various commands and argument sets
ADD_SRT_CMD = u'-o "%(workpath)s/%(recorded_name)s_tmp.mkv" "%(recordedfile)s"'
EXTRACT_DVB_SUBTITLES = u'''-Djava.awt.headless=true -jar "%(projectx_jar_path)s" -ini "%(projectx_ini_path)s" -out "%(workpath)s" -name "%(recorded_name)s" "%(recordedfile)s"'''
CLEAR_CUTLIST = u'--clearcutlist --chanid %(chanid)s --starttime "%(SQL_starttime)s"'
CLEAR_SKIPLIST = u'--clearskiplist --chanid %(chanid)s --starttime "%(SQL_starttime)s"'
GEN_CUTLIST = u'--gencutlist --chanid %(chanid)s --starttime "%(SQL_starttime)s"'
CUTS_CMD = u'-o "%(workpath)s/%(recorded_name)s-%%04d.mkv" %(strip_args)s --split parts:%(split_list)s "%(sourcefile)s"'
CONCERT_CUTS_CMD = u'-o "%(segment_path)s/%(segment_filename)s.mkv" %(strip_args)s --split parts:%(split_list)s "%(sourcefile)s"'
#
START_CUT_CMD = u'%(strip_args)s --split parts:%(split_list)s "%(sourcefile)s"'
CONVERT_CMD = u'%s -o "%%s" --title "%%s" --attachment-description "%%s" "%%s" &>>"%%s"'
GEN_GET_CUTLIST_CMD = u'--chanid %(chanid)s --starttime "%(SQL_starttime)s"'
#
## Command line utilities
MKVMERGE = u'mkvmerge'
MKVMERGE_MIN_VERSION = '5.7'
MKVTOOLNIX_DOWNLOADS_URL = u'https://www.bunkus.org/videotools/mkvtoolnix/downloads.html'
MKVTOOLNIX_SOURCE_URL = u'https://www.bunkus.org/videotools/mkvtoolnix/source.html'
MEDIAINFO = u'mediainfo'
MEDIAINFO_MIN_VERSION = 'v0.7.5'
MEDIAINFO_XML = u'--Output=OLDXML "%s"'
MEDIAINFO_URL = u'http://mediainfo.sourceforge.net/en/Download'
MEDIAINFO_PPA_URL = u'https://launchpad.net/~shiki/+archive/mediainfo'
#
## Subtitle track extracting utilities:
MYTHCCEXTRACTOR_ARGS = u'--verbose -i "%(recordedfile)s"'
BIT_ARCH_64 = u'%ssubtitle/%s64bit'
BIT_ARCH_32 = u'%ssubtitle/%s32bit'
CCEXTRACTOR = u'ccextractor'
ISO639_2_LANG_CODE_FILE = u'%simportcode/ISO639-2_language_code.txt' % APPDIR
#
## SQL statements used for processing a lossless cut recording
SQL_GET_GENRE = u"SELECT genre FROM `programgenres` WHERE chanid=%(chanid)s AND starttime='%(SQL_progstart)s' LIMIT 1;"
#
## SQL statements to collect information on the device that recorded the video
SQL_GET_CARDID = u"SELECT `cardtype`, `defaultinput`, `videodevice`, `audiodevice`, `hostname` FROM `capturecard` WHERE `cardid` = %d"
SQL_GET_CARDINFO = u"SELECT `cardid`, `displayname` FROM `cardinput` WHERE `sourceid` = %d"
SQL_GET_SOURCEID = u"SELECT `sourceid`  FROM `channel` WHERE `chanid` = %d"
#
## SQL statements for collecting and inserting a Recording's data base records.
## Used to assist in problem analysis and testing
SQL_GET_OR_INSERT = {
    'progstart': ['oldrecorded', 'programgenres', 'program', 'recordedprogram', ],
    'starttime': ['recordedseek', 'recorded', 'recordedmarkup', ],
    'get_sql': u"SELECT * FROM %(table)s WHERE chanid=%(chanid)s AND starttime='%(SQL_start)s';",
    'delete_sql': u"DELETE FROM %(table)s WHERE chanid=%(chanid)s AND starttime='%(SQL_start)s';",
    'insert_sql': {
        'recorded': {
            24: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'hostname', 'bookmark', 'editing', 'cutlist', 'autoexpire', 'commflagged', 'recgroup', 'recordid', 'seriesid', 'programid', 'lastmodified', 'filesize', 'stars', 'previouslyshown', 'originalairdate', 'preserve', 'findid', 'deletepending', 'transcoder', 'timestretch', 'recpriority', 'basename', 'progstart', 'progend', 'playgroup', 'profile', 'duplicate', 'transcoded', 'watched', 'storagegroup', 'bookmarkupdate'],
                u"INSERT INTO `mythconverg`.`recorded` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `hostname`, `bookmark`, `editing`, `cutlist`, `autoexpire`, `commflagged`, `recgroup`, `recordid`, `seriesid`, `programid`, `lastmodified`, `filesize`, `stars`, `previouslyshown`, `originalairdate`, `preserve`, `findid`, `deletepending`, `transcoder`, `timestretch`, `recpriority`, `basename`, `progstart`, `progend`, `playgroup`, `profile`, `duplicate`, `transcoded`, `watched`, `storagegroup`, `bookmarkupdate`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(hostname)s', '%(bookmark)s', '%(editing)s', '%(cutlist)s', '%(autoexpire)s', '%(commflagged)s', '%(recgroup)s', '%(recordid)s', '%(seriesid)s', '%(programid)s', '%(lastmodified)s', '%(filesize)s', '%(stars)s', '%(previouslyshown)s', '%(originalairdate)s', '%(preserve)s', '%(findid)s', '%(deletepending)s', '%(transcoder)s', '%(timestretch)s', '%(recpriority)s', '%(basename)s', '%(progstart)s', '%(progend)s', '%(playgroup)s', '%(profile)s', '%(duplicate)s', '%(transcoded)s', '%(watched)s', '%(storagegroup)s', '%(bookmarkupdate)s');"
            ],
            25: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'season', 'episode', 'category', 'hostname', 'bookmark', 'editing', 'cutlist', 'autoexpire', 'commflagged', 'recgroup', 'recordid', 'seriesid', 'programid', 'inetref', 'lastmodified', 'filesize', 'stars', 'previouslyshown', 'originalairdate', 'preserve', 'findid', 'deletepending', 'transcoder', 'timestretch', 'recpriority', 'basename', 'progstart', 'progend', 'playgroup', 'profile', 'duplicate', 'transcoded', 'watched', 'storagegroup', 'bookmarkupdate'],
                u"INSERT INTO `mythconverg`.`recorded` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `season`, `episode`, `category`, `hostname`, `bookmark`, `editing`, `cutlist`, `autoexpire`, `commflagged`, `recgroup`, `recordid`, `seriesid`, `programid`, `inetref`, `lastmodified`, `filesize`, `stars`, `previouslyshown`, `originalairdate`, `preserve`, `findid`, `deletepending`, `transcoder`, `timestretch`, `recpriority`, `basename`, `progstart`, `progend`, `playgroup`, `profile`, `duplicate`, `transcoded`, `watched`, `storagegroup`, `bookmarkupdate`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(season)s', '%(episode)s', '%(category)s', '%(hostname)s', '%(bookmark)s', '%(editing)s', '%(cutlist)s', '%(autoexpire)s', '%(commflagged)s', '%(recgroup)s', '%(recordid)s', '%(seriesid)s', '%(programid)s', '%(inetref)s', '%(lastmodified)s', '%(filesize)s', '%(stars)s', '%(previouslyshown)s', '%(originalairdate)s', '%(preserve)s', '%(findid)s', '%(deletepending)s', '%(transcoder)s', '%(timestretch)s', '%(recpriority)s', '%(basename)s', '%(progstart)s', '%(progend)s', '%(playgroup)s',' %(profile)s', '%(duplicate)s', '%(transcoded)s', '%(watched)s', '%(storagegroup)s', '%(bookmarkupdate)s');"
            ],
        },
        'recordedprogram': {
            24: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'category_type', 'airdate', 'stars', 'previouslyshown', 'title_pronounce', 'stereo', 'subtitled', 'hdtv', 'closecaptioned', 'partnumber', 'parttotal', 'seriesid', 'originalairdate', 'showtype', 'colorcode', 'syndicatedepisodenumber', 'programid', 'manualid', 'generic', 'listingsource', 'first', 'last', 'audioprop', 'subtitletypes', 'videoprop'],
                u"INSERT INTO `mythconverg`.`recordedprogram` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `category_type`, `airdate`, `stars`, `previouslyshown`, `title_pronounce`, `stereo`, `subtitled`, `hdtv`, `closecaptioned`, `partnumber`, `parttotal`, `seriesid`, `originalairdate`, `showtype`, `colorcode`, `syndicatedepisodenumber`, `programid`, `manualid`, `generic`, `listingsource`, `first`, `last`, `audioprop`, `subtitletypes`, `videoprop`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(category_type)s', '%(airdate)s', '%(stars)s', '%(previouslyshown)s', '%(title_pronounce)s', '%(stereo)s', '%(subtitled)s', '%(hdtv)s', '%(closecaptioned)s', '%(partnumber)s', '%(parttotal)s', '%(seriesid)s', '%(originalairdate)s', '%(showtype)s', '%(colorcode)s', '%(syndicatedepisodenumber)s', '%(programid)s', '%(manualid)s', '%(generic)s', '%(listingsource)s', '%(first)s', '%(last)s', '%(audioprop)s', '%(subtitletypes)s', '%(videoprop)s');"
            ],
            25: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'category_type', 'airdate', 'stars', 'previouslyshown', 'title_pronounce', 'stereo', 'subtitled', 'hdtv', 'closecaptioned', 'partnumber', 'parttotal', 'seriesid', 'originalairdate', 'showtype', 'colorcode', 'syndicatedepisodenumber', 'programid', 'manualid', 'generic', 'listingsource', 'first', 'last', 'audioprop', 'subtitletypes', 'videoprop'],
                u"INSERT INTO `mythconverg`.`recordedprogram` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `category_type`, `airdate`, `stars`, `previouslyshown`, `title_pronounce`, `stereo`, `subtitled`, `hdtv`, `closecaptioned`, `partnumber`, `parttotal`, `seriesid`, `originalairdate`, `showtype`, `colorcode`, `syndicatedepisodenumber`, `programid`, `manualid`, `generic`, `listingsource`, `first`, `last`, `audioprop`, `subtitletypes`, `videoprop`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(category_type)s', '%(airdate)s', '%(stars)s', '%(previouslyshown)s', '%(title_pronounce)s', '%(stereo)s', '%(subtitled)s', '%(hdtv)s', '%(closecaptioned)s', '%(partnumber)s', '%(parttotal)s', '%(seriesid)s', '%(originalairdate)s', '%(showtype)s', '%(colorcode)s', '%(syndicatedepisodenumber)s', '%(programid)s', '%(manualid)s', '%(generic)s', '%(listingsource)s', '%(first)s', '%(last)s', '%(audioprop)s', '%(subtitletypes)s', '%(videoprop)s');"
            ],
        },
        'recordedseek': {
            'All': [
                    ['chanid', 'starttime', 'mark', 'offset', 'type'],
                    u"INSERT INTO `mythconverg`.`recordedseek` (`chanid`, `starttime`, `mark`, `offset`, `type`) VALUES (%(chanid)s, '%(starttime)s', %(mark)s, %(offset)s, %(type)s);"
            ],
        },
        'recordedmarkup': {
            'All': [
                    ['chanid', 'starttime', 'mark', 'type', 'data'],
                    u"INSERT INTO `mythconverg`.`recordedmarkup` (`chanid`, `starttime`, `mark`, `type`, `data`) VALUES (%(chanid)s, '%(starttime)s', %(mark)s, %(type)s, %(data)s);"
            ],
        },
        'program': {
            24: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'category_type', 'airdate', 'stars', 'previouslyshown', 'title_pronounce', 'stereo', 'subtitled', 'hdtv', 'closecaptioned', 'partnumber', 'parttotal', 'seriesid', 'originalairdate', 'showtype', 'colorcode', 'syndicatedepisodenumber', 'programid', 'manualid', 'generic', 'listingsource', 'first', 'last', 'audioprop', 'subtitletypes', 'videoprop'],
                u"INSERT INTO `mythconverg`.`program` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `category_type`, `airdate`, `stars`, `previouslyshown`, `title_pronounce`, `stereo`, `subtitled`, `hdtv`, `closecaptioned`, `partnumber`, `parttotal`, `seriesid`, `originalairdate`, `showtype`, `colorcode`, `syndicatedepisodenumber`, `programid`, `manualid`, `generic`, `listingsource`, `first`, `last`, `audioprop`, `subtitletypes`, `videoprop`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(category_type)s', '%(airdate)s', '%(stars)s', '%(previouslyshown)s', '%(title_pronounce)s', '%(stereo)s', '%(subtitled)s', '%(hdtv)s', '%(closecaptioned)s', '%(partnumber)s', '%(parttotal)s', '%(seriesid)s', '%(originalairdate)s', '%(showtype)s', '%(colorcode)s', '%(syndicatedepisodenumber)s', '%(programid)s', '%(manualid)s', '%(generic)s', '%(listingsource)s', '%(first)s', '%(last)s', '%(audioprop)s', '%(subtitletypes)s', '%(videoprop)s');"
            ],
            25: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'category_type', 'airdate', 'stars', 'previouslyshown', 'title_pronounce', 'stereo', 'subtitled', 'hdtv', 'closecaptioned', 'partnumber', 'parttotal', 'seriesid', 'originalairdate', 'showtype', 'colorcode', 'syndicatedepisodenumber', 'programid', 'manualid', 'generic', 'listingsource', 'first', 'last', 'audioprop', 'subtitletypes', 'videoprop'],
                u"INSERT INTO `mythconverg`.`program` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `category_type`, `airdate`, `stars`, `previouslyshown`, `title_pronounce`, `stereo`, `subtitled`, `hdtv`, `closecaptioned`, `partnumber`, `parttotal`, `seriesid`, `originalairdate`, `showtype`, `colorcode`, `syndicatedepisodenumber`, `programid`, `manualid`, `generic`, `listingsource`, `first`, `last`, `audioprop`, `subtitletypes`, `videoprop`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(category_type)s', '%(airdate)s', '%(stars)s', '%(previouslyshown)s', '%(title_pronounce)s', '%(stereo)s', '%(subtitled)s', '%(hdtv)s', '%(closecaptioned)s', '%(partnumber)s', '%(parttotal)s', '%(seriesid)s', '%(originalairdate)s', '%(showtype)s', '%(colorcode)s', '%(syndicatedepisodenumber)s', '%(programid)s', '%(manualid)s', '%(generic)s', '%(listingsource)s', '%(first)s', '%(last)s', '%(audioprop)s', '%(subtitletypes)s', '%(videoprop)s');"
            ],
        },
        'programgenres': {
            'All': [
                    ['chanid', 'starttime', 'relevance', 'genre'],
                    u"INSERT INTO `mythconverg`.`programgenres` (`chanid`, `starttime`, `relevance`, `genre`) VALUES ('%(chanid)s', '%(starttime)s', '%(relevance)s', '%(genre)s');"
            ],
        },
        'oldrecorded': {
            24: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'category', 'seriesid', 'programid', 'findid', 'recordid', 'station', 'rectype', 'duplicate', 'recstatus', 'reactivate', 'generic'],
                u"INSERT INTO `mythconverg`.`oldrecorded` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `category`, `seriesid`, `programid`, `findid`, `recordid`, `station`, `rectype`, `duplicate`, `recstatus`, `reactivate`, `generic`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(category)s', '%(seriesid)s', '%(programid)s', '%(findid)s', '%(recordid)s', '%(station)s', '%(rectype)s', '%(duplicate)s', '%(recstatus)s', '%(reactivate)s', '%(generic)s');"
            ],
            25: [
                ['chanid', 'starttime', 'endtime', 'title', 'subtitle', 'description', 'season', 'episode', 'category', 'seriesid', 'programid', 'inetref', 'findid', 'recordid', 'station', 'rectype', 'duplicate', 'recstatus', 'reactivate', 'generic', 'future'],
                u"INSERT INTO `mythconverg`.`oldrecorded` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `season`, `episode`, `category`, `seriesid`, `programid`, `inetref`, `findid`, `recordid`, `station`, `rectype`, `duplicate`, `recstatus`, `reactivate`, `generic`, `future`) VALUES ('%(chanid)s', '%(starttime)s', '%(endtime)s', '%(title)s', '%(subtitle)s', '%(description)s', '%(season)s', '%(episode)s', '%(category)s', '%(seriesid)s', '%(programid)s', '%(inetref)s', '%(findid)s', '%(recordid)s', '%(station)s', '%(rectype)s', '%(duplicate)s', '%(recstatus)s', '%(reactivate)s', '%(generic)s', '%(future)s')"
            ],
        },
    },
}
#
### Date formating
## Mon 17OCT at 02:00:00
LL_START_END_FORMAT = '%a %d %b at %H:%M:%S'
#
## Default configuration settings
DEFAULT_CONFIG_SETTINGS = {
    'add_metadata': u'true',
    # CCExtractor options for UK DVB Teletext subtitles e.g.: -teletext -datapid 5603  --defaultcolor "#ffd700" -utf8 -tpage 888
    'ccextractor_args': u'-teletext -datapid %(subid)s -tpage %(subpage)s --defaultcolor "#ffd700" -utf8 "%(recordedfile)s" -o "%(sub_filename)s"',
    'delete_old': u'false',
    # movepath is not used as this config variable is commented out
    # in the initalized configuration file
    'export_path': u'/path to an export directory',
    'keep_log': u'false',
    'logpath': u'/tmp',
    'movie_format': u'%(title)s (%(releasedate)s)',
    'tvseries_format': u'%(series)s - S%(season_num)02dE%(episode_num)02d - %(episode)s',
    'strip': u'false',
    'workpath': u'/tmp/lossless_cut',
    #
    # Defaults for mythvidexport section
    'television': u'Review/%TITLE% - S%SEASONPAD%E%EPISODEPAD% - %SUBTITLE%',
    'movie': u'Review/%TITLE% (%YEAR%)',
    'generic': u'Review/%TITLE%: %SUBTITLE%',
    #
    # Defaults for the dvb_subtitles section
    'dvb_subtitle_defaults': {
        'include_dvb_subtitles': u'false',
        'moveposition': u'0,0',
        'ttxlanguagepair': u'0',
        'font_point_size': u'26',
        'background_alpha': u'10',
        'yoffset': u'32',
        'xoffset': u'80',
        'xwidth': u'560',
        'h_unused': u'720',
        'vertical': u'576',
        'yoffset2': u'-1',
        'maxlines': u'4',
        'unknown_1': u'3',
        'unknown_2': u'1',
        'vobsub_delay': u'0',
    }
}
#
CONCERT_CUT_DEFAULT_FORMAT = u'%SEGNUMPAD% - %TITLE%: %SUBTITLE%'
#
FORMAT_SUP_VALUES = u'''%(font_point_size)s,%(background_alpha)s,%(yoffset)s,%(xoffset)s,%(xwidth)s,%(h_unused)s,%(vertical)s,%(yoffset2)s,%(maxlines)s,%(unknown_1)s,%(unknown_2)s'''
# lxml XPath filters used to parse out video details
# from XML produced by mediainfo utility
TRACKS_XPATH = u'//track[@type = $track_type]'
ELEMENTS_XPATH = u'./*[local-name() = $element]/text()'
#
## Track elements used in detail, debugging and log display
VIDEO_ELEMENTS = [
    u"Format",
    u"Format_version",
    u"Bit_rate_mode",
    u"Bit_rate",
    u"Maximum_bit_rate",
    u"Display_aspect_ratio",
    u"Frame_rate",
    u"Standard",
    u"Color_space",
    u"Chroma_subsampling",
    u"Bit_depth",
    u"Scan_type",
    u"Compression_mode",
    u'Width',
    u'Height',
    u'Original_frame_rate',
]
#
AUDIO_ELEMENTS = [
    u"Format",
    u"Format_version",
    u"Format_profile",
    u"Codec_ID",
    u"Bit_rate_mode",
    u"Bit_rate",
    u"Channel_s_",
    u"Sampling_rate",
    u"Compression_mode",
    u"Delay_relative_to_video",
    u"Language",
]
#
SUBTITLE_ELEMENTS = [
    u"Format",
    u"Format_version",
    u"Codec_ID",
    u"Delay_relative_to_video",
    u"Language",
]
#
TRACK_ELEM_DICT = {
    'video': VIDEO_ELEMENTS,
    'audio': AUDIO_ELEMENTS,
    'subtitle': SUBTITLE_ELEMENTS,
}
TRACK_DISPLAY_ORDER = ['video', 'audio', 'subtitle']
#
VIDEO_SAMPLE_FILE_CMD = \
u'if="%(recordedfile)s" of="%(bug_sample)s" skip=%(sample_startblock)s bs=1 count=25321472'
#
## Track elements used in a wiki table entry for successful or unsupported
## MythTV recording devices
VIDEO_ELEMENTS = [
    u"Format",
    u"Format_version",
]
#
AUDIO_ELEMENTS = [
    u"Format",
    u"Format_version",
    u"Format_profile",
    u"Codec_ID",
]
#
SUBTITLE_ELEMENTS = [
    u"Format",
    u"Codec_ID",
]
#
WIKI_TRACK_ELEM_DICT = {
    'video': VIDEO_ELEMENTS,
    'audio': AUDIO_ELEMENTS,
    'subtitle': SUBTITLE_ELEMENTS,
}
#
WIKI_UNSUPPORTED_DEVICE_TABLE_URL = \
u'http://www.mythtv.org/wiki/Lossless_Cut#Unsupported_Recording_Devices'
WIKI_SUPPORTED_DEVICE_TABLE_URL = \
u'http://www.mythtv.org/wiki/Lossless_Cut#Supported_Recording_Devices'
WIKI_FIRST_COLUMN = u'|-\n'
WIKI_MANUFACTURER_COLUMN = u'|Manufacturer Name\n'
WIKI_MODEL_COLUMN = u'|Device Model\n'
WIKI_ROW = u'|%(recorders_cardtype)s\n'
WIKI_TABLE_COLUMN = u'|%s\n'
#
## Duration and track delay time, regex strings:
DURATION_REGEX = {
    # 1h 10mn 25s 650ms
    'hrs': re.compile(u''' ([0-9]+)h[^\\/]*$''', re.UNICODE),
    'mins': re.compile(u''' ([0-9]+)mn[^\\/]*$''', re.UNICODE),
    'secs': re.compile(u''' ([0-9]+)s[^\\/]*$''', re.UNICODE),
    'millsecs': re.compile(u''' ([0-9]+)ms[^\\/]*$''', re.UNICODE),
    'mins1': re.compile(u'''^(.+?)[ \._\-]\[?([0-9]+)mn[^\\/]*$''', re.UNICODE),
    'secs1': re.compile(u'''^(.+?)[ \._\-]\[?([0-9]+)s[^\\/]*$''', re.UNICODE),
    'millsecs1': re.compile(u'''^(.+?)[ \._\-]\[?([0-9]+)ms[^\\/]*$''', re.UNICODE),
    'hrs2': re.compile(u'''([0-9]+)h[^\\/]*$''', re.UNICODE),
    'mins2': re.compile(u'''([0-9]+)mn[^\\/]*$''', re.UNICODE),
    'secs2': re.compile(u'''([0-9]+)s[^\\/]*$''', re.UNICODE),
    'millsecs2': re.compile(u'''([0-9]+)ms[^\\/]*$''', re.UNICODE),
    'hrs3': re.compile(u'''(-[0-9]+)h[^\\/]*$''', re.UNICODE),
    'mins3': re.compile(u'''(-[0-9]+)mn[^\\/]*$''', re.UNICODE),
    'secs3': re.compile(u'''(-[0-9]+)s[^\\/]*$''', re.UNICODE),
    'millsecs3': re.compile(u'''(-[0-9]+)ms[^\\/]*$''', re.UNICODE),
}
#
class JOBSTATUS( object ):
    """ Job Status hex values.  """
# Queued
    UNKNOWN      = 0x0000
    QUEUED       = 0x0001
    PENDING      = 0x0002
    STARTING     = 0x0003
# Running
    RUNNING      = 0x0004
# Stopped/Paused
    STOPPING     = 0x0005
    PAUSED       = 0x0006
# Running
    RETRY        = 0x0007
# Error
    ERRORING     = 0x0008
    ABORTING     = 0x0009
# Complete
    DONE         = 0x0100
    FINISHED     = 0x0110
# Error
    ABORTED      = 0x0120
    ERRORED      = 0x0130
# Complete
    CANCELLED    = 0x0140
#
## Check if the code is being running from source
if is_package():
    ROOTDIR = '/usr/share/'
    LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')
else:
    VERSION = VERSION + '-src'
    ROOTDIR = os.path.dirname(__file__)
    LANGDIR = os.path.normpath(os.path.join(ROOTDIR, '../template1'))
