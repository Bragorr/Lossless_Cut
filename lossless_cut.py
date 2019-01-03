#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ----------------------
"""
# Name: lossless_cut.py   A Loss Less video file cut for MythTV recordings
#
# Python Script
# Author:   R.D. Vaughan
# Purpose:  This python script performs loss less video file cut
#           and merge processing on MythTV recordings.
#
# This utility is based on the process found in the shell script
# "h264cut.sh" from:
#
#   Ian Thiele at: icthiele@gmail.com
#   Wiki page for H264 commercial remover and remuxer:
#       http://www.mythtv.org/wiki/H264cut
#
# Copyright (C) 2012 R.D. Vaughan
# rdvLaunchpad@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# License:Creative Commons GNU GPL v2
# (https://www.gnu.org/licenses/gpl-2.0.html)
#-------------------------------------
#
"""
## System imports
import os
import sys
from glob import glob
from optparse import OptionParser
from datetime import datetime
from copy import deepcopy

## Mythtv loss less cut specific imports
import importcode.common as common
from importcode.utilities import create_cachedir, \
        set_language, get_config, exec_commandline, \
        check_dependancies, create_logger, commandline_call, \
        get_iso_language_code, read_iso_language_codes, make_timestamp, \
        display_recorded_info, get_mediainfo, cleanup_working_dir, \
        create_config_file
#
from importcode.mythtvinterface import Mythtvinterface
#
try:
    from lxml import etree as etree
except Exception as errmsg:
    sys.stderr.write(u'''
Importing the "lxml" python libraries failed on
Error: (%s)\n''' % errmsg)
    sys.exit(int(common.JOBSTATUS().ABORTED))
#
# Check that the lxml library is current enough
# From the lxml documents it states:
# (http://codespeak.net/lxml/installation.html)
# "If you want to use XPath, do not use libxml2 2.6.27. We recommend
# libxml2 2.7.2 or later"
#
VERSION = ''
for digit in etree.LIBXML_VERSION:
    VERSION += str(digit)+'.'
VERSION = VERSION[:-1]
if VERSION < '2.7.2':
    sys.stderr.write(u'''
Error: The installed version of the "lxml" python library "libxml" version
       is too old. At least "libxml" version 2.7.2 must be installed.
       Your version is (%s).
''' % VERSION)
    sys.exit(int(common.JOBSTATUS().ABORTED))
#
## Initialize local variables
__title__ = common.APPNAME
__version__ = common.VERSION
__author__ = common.__author__
#
# Language translation specific to this desktop
_ = set_language()
#
__purpose__ = _('''
This python script performs loss less video file cut
and merge processing on MythTV recordings.
''')
#
## Local variables
## Help text
MANDITORY = _(
'''Mandatory command line parameter:
  -f "/path/filename.mpg"       MythTV recorded video path and file name
                                to be converted to a mkv file
  When this script is used as a MythTV user job always specify the
  file as: "%%DIR%%/%%FILE%%"

  One and only one of these three options MUST be selected:
  -e                            Export the final mkv video file to MythVideo,
                                including building any required sub directories.
  -m "/mkv directory path"      Specify directory path to move the final
                                mkv video file
  -r                            Replace the Recorded video file with the loss
                                less cut mkv file. Do not use this option unless
                                you are confident that the results of the cutting
                                process. Unlike the option -e and -m the original
                                recorded video is replaced.

''')
#
USAGE_TEXT = _('''
This script uses a MythTV cut list to create a loss less mkv video file from
MythTV recordings this includes:
Video encoded as with mpeg2 and h.264 (SD, 720p or 1080i HD)
Audio encoded as mp3 and AC3 (2ch and 5.1)
Subtitle encoded srt format or can be exported and converted into an srt file.

Recording devices such as HDPVR, HDHomeRun and MPEG2 from a DVB-T FreeView
transport.
For a complete list of supported recording devices check the wiki at:
    %s

If a cutlist or skiplist has not been created then the whole mpg file is
copied into a mkv file container. In most cases a skip or cut list would
have been created before running this script as a userjob.

MythTV Userjob examples: (modify the path to the script so that it matches
your installation)
Export a loss less mkv file to a specific directory and leave the
original mpg file unchanged:

  /path to/script file/lossless_cut.py -f "%%DIR%%/%%FILE%%" -e

OR

Move a loss less mkv file to a specific local directory and leave the
original mpg file unchanged:

  /path to/script file/lossless_cut.py -f "%%DIR%%/%%FILE%%" -m "/move path"

OR

To create a loss less mkv file and replace the mpg with the mkv in the
MythTV database:

  /path to/script file/lossless_cut.py -f "%%DIR%%/%%FILE%%" -r

%s
Optional command line parameters:
  Most of these parameters can be set in the automatically
  generated "~/.mythtv/lossless_cut.cfg" configuration file.

  -a                            Do NOT add metadata with the MythTV grabbers
  -C                            Create individual files from each cut segment.
                                This is referred to as Concert Cuts.
  -D                            Delay option to change when the video track starts
                                by a positive (start sooner than other tracks)
                                or negative number (start later than other tracks)
                                in milliseconds. One second = 1000
                                This option should only be chosen by experienced users.
  -g                            Generate a cut list if one does not exist but there is
                                a skip list.
  -h or -u                      Display this help/usage text
  -j                            JobQueue ID "%%JOBID%%" of this UserJob.
  -k                            Keep the log file after the userjob
                                has completed successfully
  -l "/log directory path"      Specify a directory path to save the jobs
                                log file
  -s                            Display a summary of the options that would
                                be used during processing
                                but exit before processing begins. Used this
                                option for debugging. No changes to the mpg
                                file occurs.
  -S                            Strip away any subtitle or secondary audio tracks
  -T                            Identifies a specific Audio track to copy in
                                conjunction with the "-S" Strip option.
                                Find the audio track numbers using a
                                "> mkvmerge -i file.mkv" command. If there is only
                                one audio track then this option is meaningless.
  -t                            Perform a test of the environment, display
                                success or failure then exit
  -v                            Display script's version, author's name and
                                purpose.
  -X                            Force use of mythccextractor as the primary
                                utility to extract and convert subtitles tracks
                                into srt format.
  -w "/working directory path"  Specify a working directory path to
                                manipulate the video file

This script requires the following to be installed and accessible:
  1) The "lossless_cut" directory must be installed on a MythTV backend
  2) The utilities: mythutil or mythcommflag
  3) The mkv utility suite "MKVToolNix" is installed. At least versions
    "v5.7.0" or higher. NOTE: Most Linux distros distribute older versions.
     Instructions to upgrading to the latest versions are at:
     Downloads: %s
     Source: %s
  4) The utility mediainfo is installed.
     Use version "MediaInfoLib - v0.7.5" or higher.
     PPA: %s
     Downloads: %s
  5) A properly configured: config.xml or mysql.txt file.

''') % (common.__url__, MANDITORY,
        common.MKVTOOLNIX_DOWNLOADS_URL,
        common.MKVTOOLNIX_SOURCE_URL,
        common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL)
#
MANDITORY = (MANDITORY + "%s") % u''
#
## Command line options and arguments
PARSER = OptionParser(
        usage=u"%prog usage: lossless_cut.py -aCDefghujklmrsStTvXw [parameters]\n")

PARSER.add_option(  "-a", "--addmetadata", action="store_true",
                    default=False, dest="addmetadata",
                    help=_(u"Do NOT add metadata to the mkv video container."))
PARSER.add_option(  "-C", "--concertcuts", metavar="concertcuts",
                    action="store_const", default="N/A", dest="concertcuts",
                    help= u'''Create individual files from each cut segment and an optional
track naming configuration file. This option is referred to as "Concert Cuts".''')
PARSER.add_option(  "-D", "--delayvideo", type="int",
                    metavar="delayvideo", dest="delayvideo",
                    help= _(
u'''Delay option to change when the video track starts by a
positive (start sooner than other tracks) or
negative number (start later than other tracks) in milliseconds.
One second = 1000
This option should only be chosen by experienced users.'''))
PARSER.add_option(  "-e", "--mythvideo_export", action="store_true",
                    default=False, dest="mythvideo_export",
                    help=_(
u"Export the final mkv video into MythVideo, this includes subdirectory creation when necessary."))
PARSER.add_option(  "-f", "--recordedfile", metavar="recordedfile",
                    default="", dest="recordedfile",
                    help=_(
u'The absolute path and file name of the MythTV recording.'))
PARSER.add_option(  "-g", "--gencutlist", action="store_true",
                    default=False, dest="gencutlist",
                    help=_(
u"Generate a cut list if one does not exist but there is a skip list."))
PARSER.add_option(  "-j", "--jobid", metavar="JOBID",
                    default="", dest="jobid",
                    help= u'''This is the MythTV JobQueue ID from the "%JOBID%"
variable. This is a mandatory command line option if the
configuration file "error_detection" variables are used.''')
PARSER.add_option(  "-k", "--keeplog", action="store_true",
                    default=False, dest="keeplog",
                    help=_(
u"Keep the log file after the userjob has completed successfully."))
PARSER.add_option(  "-l", "--logpath", metavar="logpath",
                    default="", dest="logpath",
                    help=_(
u'Specify a directory path to save the jobs log file'))
PARSER.add_option(  "-m", "--movepath", metavar="movepath",
                    default="", dest="movepath",
                    help=_(
u"Specify a local directory path to move/save the final mkv video file."))
PARSER.add_option(  "-r", "--replace_recorded", action="store_true",
                    default=False, dest="replace_recorded",
                    help=_(
u"Replace the recorded video file with the loss less cut version. Use with caution!"))
PARSER.add_option(  "-s", "--summary", action="store_true",
                    default=False, dest="summary",
                    help=_(
u'''Display a summary of the options that would be used during processing
but exit before processing begins. Used this for debugging. No changes
to the mpg file occur.'''))
PARSER.add_option(  "-S", "--noextratracks", action="store_true",
                    default=False, dest="noextratracks",
                    help=_(
u"Do not include any subtitle or secondary audio tracks."))
PARSER.add_option(  "-t", "--test", action="store_true",
                    default=False, dest="test",
                    help=_(
u"Test that the environment meets all the scripts dependencies."))
PARSER.add_option(  "-T", "--tracknumber", type="int",
                    metavar="tracknumber", dest="tracknumber",
                    help= _(
u'''Identifies a specific Audio track to copy in
conjunction with the "-S" Strip option.
Find the audio track numbers using a
"> mkvmerge -i file.mkv" command. If there is only
one audio track then this option is meaningless.'''))
PARSER.add_option(  "-u", "--usage", action="store_true",
                    default=False, dest="usage",
                    help=_(u"Display this help/usage text and exit."))
PARSER.add_option(  "-v", "--version", action="store_true",
                    default=False, dest="version",
                    help=_(u"Display version and author information"))
PARSER.add_option(  "-X", "--forcemythxxextractor", action="store_true",
                    default=False, dest="forcemythxxextractor",
                    help=_(
u'''Force use of mythccextractor as the primary
utility to extract and convert subtitles tracks into SRT format.'''))
PARSER.add_option(  "-w", "--workingpath", metavar="WORKINGPATH",
                    default="", dest="workingpath",
                    help=_(
u'Specify a working directory path to manipulate the video file'))
#
OPTS, ARGS = PARSER.parse_args()
#
## The Concert Cuts option "-C" can optionally include a configuration
## file path. Handle three different situations.
if OPTS.concertcuts == 'N/A':
    OPTS.concertcuts = False
elif OPTS.concertcuts == None and len(ARGS):
    OPTS.concertcuts = ARGS[0]
else:
    OPTS.concertcuts = True
#
#
## Deal with utf8 string in stdout and stderr
class OutStreamEncoder(object):
    """Wraps a stream with an encoder"""
    def __init__(self, outstream, encoding=None):
        self.out = outstream
        if not encoding:
            self.encoding = sys.getfilesystemencoding()
        else:
            self.encoding = encoding

    def write(self, obj):
        """Wraps the output stream, encoding Unicode strings with the
        specified encoding"""
        if isinstance(obj, str):
            try:
                self.out.write(obj.encode(self.encoding))
            except IOError:
                pass
        else:
            try:
                self.out.write(obj)
            except IOError:
                pass

    def __getattr__(self, attr):
        """Delegate everything but write to the stream"""
        return getattr(self.out, attr)
sys.stdout = OutStreamEncoder(sys.stdout, 'utf-8')
sys.stderr = OutStreamEncoder(sys.stderr, 'utf-8')
#
#
class Mythtvlosslesscut(object):
    """Perform loss less cut processing on a MythTV recorded video file
    """

    def __init__(self,
                opts,   # Command line options
                ):
        #
        self.jobstatus = common.JOBSTATUS()
        self.return_code = int(self.jobstatus.UNKNOWN)
        #
        try:
            self.configuration = get_config(opts)
        except Exception as errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'''Processing the configuration file failed. Error(%s)\n''')
                    % errmsg)
            sys.exit(int(self.jobstatus.ABORTED))
        #
        self.logger = create_logger(self.configuration['logfile'], filename=True)
        #
        ## Make verbose output to the log standard
        self.configuration['verbose'] = True
        self.configuration['version'] = __version__
        #
        try:
            self.mythtvinterface = Mythtvinterface(self.logger,
                                                    self.configuration)
        except Exception as errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'''Acquiring access to MythTV failed, aborting script.
Error(%s)\n''') % errmsg)
            sys.exit(int(self.jobstatus.ABORTED))
        #
        ## Set if mythtv v0.24 is installed
        if self.mythtvinterface.OWN_VERSION[1] == 24:
            self.configuration['v024'] = True
        else:
            self.configuration['v024'] = False
        #
        # Determine if the system is 64 or 32 bit architecture
        if (sys.maxsize > 2**32):
            bit_arch = common.BIT_ARCH_64
        else:
            bit_arch = common.BIT_ARCH_32
        # Set the subtitle extraction utilities based on the system
        # architecture
        self.configuration['ccextractor'] = bit_arch % (
                common.APPDIR, common.CCEXTRACTOR)
        # Add location of the ProjectX java app
        self.configuration['projectx_jar_path'] = \
                u'%ssubtitle/ProjectX.jar' % common.APPDIR
        #
        try:
            self.configuration['mythutil'] = check_dependancies(
                    self.configuration)
        except Exception as errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'''
One or more script dependencies could not be satisfied, aborting script.
Error(%s)\n''')
                    % errmsg)
            sys.exit(int(self.jobstatus.ABORTED))
        #
        self.mythtvinterface.stdout = sys.stdout
        self.mythtvinterface.stderr = sys.stderr
        self.mythtvinterface.etree = etree
        #
        ## Xpath filters used to parse mediainfo XML output
        # Find specific track types
        self.tracks_filter = \
                etree.XPath(common.TRACKS_XPATH)
        self.element_filter = \
                etree.XPath(common.ELEMENTS_XPATH)
        #
        ## Remove this recording's files from the working directory
        cleanup_working_dir(self.configuration['workpath'],
                            self.configuration['recorded_name'])
        #
        self.processing_started = datetime.now()
        self.subtitles = None
        #
        ## Check if the user wants to automatically generate a cut list when
        ## it is empty but there is a skip list
        self.configuration['gencutlist'] = False
        if opts.gencutlist:
            self.configuration['gencutlist'] = True
        #
        # end __init__()
#
    def cut_video_file(self):
        '''
        1) Check if display options was selected.
        2) Test the environment and the script dependancies
           was selected.
        3) Process the MythTV recording.
        return nothing
        '''
        if self.configuration['summary']:
            self._display_variables(summary=True)
            sys.exit(int(self.jobstatus.UNKNOWN))
        #
        if self.configuration['test']:
            self._display_variables(summary=True)
            sys.stdout.write(
                _(u'''Congratulations! All script dependencies have been satisfied.
You are ready to perform loss less cuts on MythTV recorded videos.

'''))
            sys.exit(int(self.jobstatus.UNKNOWN))
        #
        # Verify that one and only one of these options have been selected
        sys.stdout.write(common.LL_START_END_FORMAT)
        count = 0
        for key in ['replace', 'mythvideo_export', 'movepath']:
            if self.configuration[key]:
                count += 1
        if count == 0:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            sys.stderr.write(
_(u'''You must select one of these three options "-e", "-m", "r". See:
%s\n''') % (MANDITORY))
            sys.exit(int(self.jobstatus.ABORTED))
        elif count > 1:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            sys.stderr.write(
_(u'''You must ONLY select ONE of these three options "-e", "-m", "r". See:
%s\n''') % (MANDITORY))
            sys.exit(int(self.jobstatus.ABORTED))
        #
        self.logger.info(
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
_(u'''Start loss less commercial cut of "%s" at: %s''') % (
            self.configuration['recordedfile'],
            self.processing_started.strftime(common.LL_START_END_FORMAT).decode))
        #
        self._display_variables()
        #
        self._collect_metadate()
        #
        # Only process subtitles if they need to be included
        if not self.configuration['strip'] and self.subtitles:
            self._process_subtitles()
        #
        self._cut_preprocessing()
        #
        if self.configuration['concertcuts']:
            self._process_concert_cuts()
        else:
            self._lossless_cut()
        #
        self._cleanup()
        #
        return
#
    def _collect_metadate(self,):
        ''' Read the recorded record and collect specific data including
        metadata. If there is no metadata then use the grabbers to get
        missing details.
        Read the recordedseek record for the first and last frame numbers
        return nothing
        '''
        #
        self.subtitles = False
        # Get the xml track info using mediainfo
        self.configuration['trackinfo'] = get_mediainfo(
                        self.configuration['recordedfile'],
                        self.element_filter, self.tracks_filter,
                        etree, self.logger, sys)
        #
        ## Get this recordings metadata and other data from the MyhTV DB
        self.mythtvinterface.get_recorded_data()
        #
        display_recorded_info(self.configuration, self.logger)
        #
        # Check if any subtitles processing is required
        if self.configuration['trackinfo']['total_subtitle']:
            self.subtitles = True
        #
        ## Set the mkv file metadata formatted title
        if self.configuration['subtitle']:
            if self.configuration['inetref']:
                self.configuration['video_title'] = \
                   self.configuration['series'] % self.configuration
            else:
                self.configuration['video_title'] = \
                    u'%(title)s: %(subtitle)s' % self.configuration
        else:
            if self.configuration['releasedate']:
                self.configuration['video_title'] = \
                    self.configuration['movie_format'] % \
                        self.configuration
            else:
                self.configuration['video_title'] = \
                    u'%(title)s' % self.configuration
        #
        self.configuration['iso639_2_lang_codes'] = \
                            read_iso_language_codes(logger=self.logger)
        #
        ## Replace mythvidexport format variables with config key equivalents
        for find_replace in self.configuration['mythvidexport_rep']:
            self.configuration['export_format'] = self.configuration[
                'export_format'].replace(find_replace[0], find_replace[1])
        #
        ## Replace Concert Cuts format variables with config key equivalents
        if self.configuration['concertcuts']:
            for find_replace in self.configuration['mythvidexport_rep']:
                self.configuration['concertcuts'] = self.configuration[
                    'concertcuts'].replace(find_replace[0], find_replace[1])
                for seg_key in self.configuration['segment_names'].keys():
                    self.configuration['segment_names'][seg_key] = \
                        self.configuration['segment_names'][seg_key].replace(
                                    find_replace[0], find_replace[1])
        #
        self.logger.info(_(u'''
Recorded file:
  Channel ID: %(chanid)s
  Start time: %(starttime)s
''') % self.configuration)
        #
        return
#
    def _process_subtitles(self,):
        '''
        If there are subtitle track(s) and they are not in srt format then
        extract the track and convert to an srt subtitle file.
        Copy the original recorded file and new srt file(s). During the
        copy add the new srt file as a subtitle track. Then change the
        recorded file name that gets cut to this new recorded mkv file.
        return nothing
        '''
        #
        self.configuration['srt_files'] = []
        #
        ## Attempt to extract non-SRT subtitle tracks and convert
        ## into srt format
        subtrack_num = 0
        unknown_lang = u'Unknown %s'
        unknown_lang_count = 1
        first_subtitle_track = True
        first_dvb_subtitle_track = True
        for subetree in self.configuration['trackinfo']['subtitle']:
            # Skip subtitle tracks that are already in SRT format
            # as they will be automatically copied by mkvmerge
            code_id_elem = subetree.xpath('./Codec_ID')
            if code_id_elem:
                if code_id_elem[0].text.startswith('S_TEXT'):
                    subtrack_num += 1
                    continue
            #
            try:
                subid = subetree.xpath('./ID')[0]
                subformat = subetree.xpath('./Format')[0].text
                try:
                    sublanguage = subetree.xpath('./Language')[0].text
                except IndexError:
                    # Some recording devices do not declare
                    # the language of a subtitle track
                    sublanguage = unknown_lang % unknown_lang_count
                    unknown_lang_count += 1
                self.configuration['subid'] = u''
                index = (subid.text).find(' ')
                if not index == -1:
                    self.configuration['subid'] = (subid.text)[:index]
                else:
                    verbage = _(
u'''Subtitle streamid %s does not have a recognizable subid in the
ID sudid text "%s", skipping this subtitle track.''') % \
                        (self.configuration['streamid'], subid)
                    self.logger.info(verbage)
                    sys.stdout.write(verbage + u'\n\n')
                    subtrack_num += 1
                    continue
                self.configuration['subpage'] = u''
                index = (subid.text).find(')-')
                if not index == -1:
                    self.configuration['subpage'] = (
                                        subid.text)[index+2:].strip()
            except Exception as errmsg:
                # Deal with problems with the subtitle data
                verbage = _(
u'''Getting Subtitle streamid %s extraction information failed
this subtitle track will be skipped.
Error: "%s"''') % (self.configuration['streamid'], errmsg)
                self.logger.info(verbage)
                sys.stdout.write(verbage + u'\n\n')
                subtrack_num += 1
                continue
            #
            ## Process DVB Subtitles
            if (not self.configuration['include_dvb_subtitles'] and \
                    subformat.find('DVB Subtitle') != -1) or \
                    not first_dvb_subtitle_track:
                subtrack_num += 1
                continue
            elif self.configuration['include_dvb_subtitles'] and \
                    subformat.find('DVB Subtitle') != -1 and \
                    first_dvb_subtitle_track:
                #
                self.configuration['projectx_ini_path'] = \
                        common.PROJECTX_INI_PATH % self.configuration
                try:
                    fileh = open(
                            self.configuration['projectx_ini_path'], 'w')
                except IOError as errmsg:
                    # TRANSLATORS: Please leave %s as it is,
                    # because it is needed by the program.
                    # Thank you for contributing to this project.
                    directory, basefilename = os.path.split(
                            self.configuration['projectx_ini_path'])
                    sys.stderr.write(_(
u'''Could not create the ProjectX "%s" file in directory "%s".
This is likely a directory Read/Write permission issue but
check the error message below to confirm, aborting script.
Error: %s''') % (basefilename, directory, errmsg))
                    exit(int(self.jobstatus.ABORTED))
                #
                fileh.write(self.configuration['projectx_ini'])
                fileh.close()
                #
                arguments = (common.EXTRACT_DVB_SUBTITLES %
                                self.configuration)
                result = commandline_call(
                                    self.configuration['java'], arguments)
                #
                stdout = u''
                if self.configuration['verbose']:
                    stdout = result[1]
                #
                if result[0]:
                    self.logger.info(_(u'''ProjectX command:
> %s %s

%s
''' % (self.configuration['java'], arguments, stdout)))
                    #
                    for filename in glob(
                        (u'%(workpath)s/%(recorded_name)s*' %
                            self.configuration)):
                        if not filename.endswith('.idx'):
                            continue
                        # Unfortunitely even if all the subtitle
                        # tracks have been properly identified the fact that
                        # ProjectX extracts all DVB subtitles in one pass
                        # means that only the first subtitle track's
                        # langauge can be identified. Default to "Unknown"
                        # for any additional subtitle track languages
                        if first_subtitle_track:
                            self.configuration['srt_files'].append(
                                [sublanguage, filename,
                                self.configuration['trackinfo'][
                                    'subtitle_details'][subtrack_num][
                                    'Delay_relative_to_video']])
                        else:
                            sublanguage = unknown_lang % unknown_lang_count
                            unknown_lang_count += 1
                            self.configuration['srt_files'].append(
                                [sublanguage, filename,
                                self.configuration['trackinfo'][
                                    'subtitle_details'][subtrack_num][
                                    'Delay_relative_to_video']])
                        first_dvb_subtitle_track = False
                    subtrack_num += 1
                    continue
                else:
                    verbage = \
_(u'''ProjectX could not extract a DVB Subtitle track.
ID %s, language "%s", Format "%s"
Commandline options: "%s"
%s''') % (subid.text, sublanguage, subformat, arguments, result[1])
                    self.logger.info(verbage)
                    #
                    # ProjectX extracts and converts all DVB Subtitle
                    # tracks in one pass therefore only execute this
                    # code once
                    first_dvb_subtitle_track = False
                subtrack_num += 1
                continue
            #
            # If this is MythTV v0.25+ try the built-in subtitle extractor
###### See ticket: http://code.mythtv.org/trac/ticket/11081
## Added a special command line option "-X" just until the ticket is resolved
## mythccextractor may work for some recording devices
            if not self.configuration['v024'] and \
                            self.configuration['forcemythxxextractor'] and \
                            not first_subtitle_track:
                subtrack_num += 1
                continue
            if not self.configuration['v024'] and \
                            self.configuration['forcemythxxextractor'] and \
                            first_subtitle_track:
                #
                arguments = (self.configuration['mythccextractor_args']) % (
                                self.configuration)
                result = commandline_call(u'mythccextractor', arguments)
                #
                stdout = u''
                if self.configuration['verbose']:
                    stdout = result[1]
                #
                if result[0]:
                    self.logger.info(_(u'''Mythccextractor command:
> %s %s

%s
''' % (u'mythccextractor', arguments, stdout)))
                    for filename in glob(
                        (u'%(recorded_dir)s/%(recorded_name)s*.srt' %
                            self.configuration)):
                        # Unfortunitely even if all the subtitle
                        # tracks being properly identified the fact that
                        # mythccextractor extracts all subtitles in one pass
                        # means that only the first subtitle track's
                        # langauge can be identified. Default to "Unknown"
                        # for any additional subtitle track languages
                        if first_subtitle_track:
                            self.configuration['srt_files'].append(
                                [sublanguage, filename,
                                self.configuration['trackinfo'][
                                    'subtitle_details'][subtrack_num][
                                    'Delay_relative_to_video']])
                        else:
                            sublanguage = unknown_lang % unknown_lang_count
                            unknown_lang_count += 1
                            self.configuration['srt_files'].append(
                                [sublanguage, filename,
                                self.configuration['trackinfo'][
                                    'subtitle_details'][subtrack_num][
                                    'Delay_relative_to_video']])
                        first_subtitle_track = False
                    subtrack_num += 1
                    continue
                else:
                    verbage = \
_(u'''mythccextractor could not extract a subtitle track.
ID %s, language "%s", Format "%s"
Commandline options: "%s"
%s''') % (
                        subid.text, sublanguage, subformat,
                        arguments, result[1])
                    self.logger.info(verbage)
                    #
                    # mythccextractor extracts and converts all subtitle
                    # tracks in one pass therefore only execute this
                    # code once
                    first_subtitle_track = False
            #
            self.configuration['sub_filename'] = os.path.join(
                        self.configuration['workpath'],
                        u'%s_%03d.srt' %
                        (self.configuration['recorded_name'], subtrack_num))
            #
            # Clean up any zero sized srt file
            try:
                os.remove(self.configuration['sub_filename'])
            except:
                pass
            #
            # <ID>5603 (0x15E3)-888</ID>
            self.configuration['streamid'] = u'1'
            try:
                self.configuration['streamid'] = subetree.attrib['streamid']
            except KeyError:
                # There appears to be only one "Text" subtitle track
                # that means there is no streamid attribute in the XML
                # so assume this is streamid "1"
                pass
            #
            # Attempt to extract the non-SRT subtitle tracks
            ## using CCExtractor and convert into SRT format
            arguments = (self.configuration['ccextractor_args']) % (
                            self.configuration)
            if not self.configuration['subpage']:
                arguments = arguments.replace(u'-tpage  ', u'')
            #
            ## Use option '-noteletext' ONLY when subformat.startswith('EIA-')
            ## Currently only HDHomerun recordings seems to need this
            ## option but other devices may have the same issue
            if subformat.startswith('EIA-'):
                arguments += u' -noteletext'
            result = commandline_call(self.configuration['ccextractor'],
                                        arguments)
            stdout = u''
            if self.configuration['verbose']:
                stdout = result[1]
            self.logger.info(_(u'''CCExtractor command:
> %s %s

%s
''' % (self.configuration['ccextractor'], arguments, stdout)))
            #
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = \
_(u'''CCExtractor could not extract a subtitle track.
ID %s, language "%s", Format "%s"
Commandline options: "%s"
%s''') % (subid.text, sublanguage, subformat, arguments, result[1])
                self.logger.info(verbage)
                #
                # Clean up any zero sized srt file
                try:
                    os.remove(self.configuration['sub_filename'])
                except:
                    pass
                #
                subtrack_num += 1
                continue
            #
            self.configuration['srt_files'].append([
                sublanguage, self.configuration['sub_filename'],
                                self.configuration['trackinfo'][
                                    'subtitle_details'][subtrack_num][
                                    'Delay_relative_to_video']])
            subtrack_num += 1
        #
        # Remove any SRT files less than 20 bytes in size
        srt_files = deepcopy(self.configuration['srt_files'])
        for filename in srt_files:
            if os.path.getsize(filename[1]) < 20:
                os.remove(filename[1])
                self.configuration['srt_files'].remove(filename)
                continue
        #
        ## If there are no srt files to process return
        if not self.configuration['srt_files']:
            return
        #
        ## Add the srt file(s)
        cmd_line_args = common.ADD_SRT_CMD % self.configuration
        for srtfile in self.configuration['srt_files']:
            lang_code = u''
            #
            ## The TID "0" in "0:%s" is hardcoded for the language and
            ## vobsub delay.
            if srtfile[0]:
                lang_code = get_iso_language_code(
                                self.configuration['iso639_2_lang_codes'],
                                sublanguage,
                                logger=self.logger)
                if lang_code:
                    lang_code = u'--language 0:%s' % \
                        (lang_code)
            #
            ## Subitle track delay
            if srtfile[2] != None or (self.configuration[
                    'vobsub_delay'] != '0' and \
                    srtfile[1].find('.idx') != -1):
                delay_value = 0
                if srtfile[2] == None:
                    delay_value = self.configuration['vobsub_delay'].strip()
                elif self.configuration['vobsub_delay'] == '0':
                    delay_value = srtfile[2]
                else:
                    delay_value = int(self.configuration[
                                    'vobsub_delay'].strip()) + srtfile[2]
                #
                lang_code += u' --sync 0:%s' % delay_value
            #
            cmd_line_args += u' %s "%s"' % (lang_code, srtfile[1])
        #
        result = commandline_call(common.MKVMERGE, cmd_line_args %
                                self.configuration)
        stdout = u''
        if self.configuration['verbose']:
            stdout = result[1]
        self.logger.info(_(u'''mkvmerge add subtitle track(s) command:
> mkvmerge %s

%s
''' % (cmd_line_args % self.configuration, stdout)))
        if not result[0]:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = \
_(u'''mkvmerge could not add the subtitle track(s), aborting script.
Error: %s''') % (result[1])
            self.logger.critical(verbage)
            sys.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(self.jobstatus.ABORTED))
        #
        ## Clean up the created srt files
        for srtfile in self.configuration['srt_files']:
            try:
                os.remove(srtfile[1])
            except OSError:
                pass
        #
        ## Change the source video file that will be cut then merged
        ## into a final mkv video including srt subtitle track(s).
        self.configuration['sourcefile'] = \
            "%(workpath)s/%(recorded_name)s_tmp.mkv" % self.configuration
        #
        # Refresh the xml track info using mediainfo
        self.configuration['trackinfo'] = get_mediainfo(
                        self.configuration['recordedfile'],
                        self.element_filter, self.tracks_filter,
                        etree, self.logger, sys)
        #
        return
#
    def _cut_preprocessing(self,):
        '''
        Generate the get cutlist
        Get cutlist and massage it to match keyframes
        Create timecode split list using recordseek's fps value
        Build the track appendto list
        Build the merge string of segments
        return nothing
        '''
        # If the video is being exported set the move directory
        # and mkv title to the recorded dir and the filename.
        # With export trick logic into processing the video
        # as if it was a move.
        if self.configuration['mythvideo_export']:
            self.configuration['export_path_file'] = (
                self.configuration['export_format'] % self.configuration)
            #
            # Verify that MythVideo does NOT already have this exact
            # video file name.
            if self.mythtvinterface.is_unique() and \
                    not self.configuration['concertcuts']:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(u'''
The MythVideo already exists, aborting script.
MythVideo: %s''') % (self.configuration['export_path_file'])
                self.logger.critical(verbage)
                sys.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(self.jobstatus.ABORTED))
            #
            directory, filename = os.path.split(
                                self.configuration['export_path_file'])
            self.configuration['movepath'] = \
                                self.configuration['recorded_dir']
            self.configuration['mkv_title'] = filename
        #
        # Set the output name based on having a move path
        if self.configuration['movepath']:
            while True:
                self.configuration['mkv_file'] = os.path.join(
                    self.configuration['movepath'],
                    self.configuration['mkv_title'] + u'.mkv')
                ## Check for a duplicate file in export directory
                if os.path.isfile(self.configuration['mkv_file']):
                    self.configuration['mkv_title'] = \
                        self.configuration['mkv_title'] + u' - ' +\
                        datetime.now().strftime(common.LL_START_END_FORMAT)
                    continue
                break
        else:
            self.configuration['mkv_file'] = os.path.join(
                self.configuration['recorded_dir'],
                self.configuration['recorded_name'] + u'.mkv')
            #
            # Remove any old mkv file that may exist
            try:
                os.remove(self.configuration['mkv_file'])
            except:
                pass
        #
        ## Get track total
        arguments = u'--identify "%(sourcefile)s"'
        result = commandline_call(common.MKVMERGE,
                    arguments % self.configuration)
        stdout = u''
        if self.configuration['verbose']:
            stdout = result[1]
        self.logger.info(_(u'''mkvmerge get total tracks command:
> mkvmerge %s

%s
''' % (arguments % self.configuration, stdout)))
        if not result[0]:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(u'''mkvmerge to read tracks IDs, aborting script.
Error: %s''') % (result[1])
            self.logger.critical(verbage)
            sys.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(self.jobstatus.ABORTED))
        #
        track_ids = result[1].split('\n')
        self.configuration['trackinfo']['total_tracks'] = \
                    len(track_ids) - 1
        #
        self.configuration['strip_args'] = u''
        if self.configuration['strip']:
            video, audio = False, False
            for track in track_ids:
                track_id_index = track.find(':')
                index = track.find('video')
                if not index == -1 and video == False:
                    index = track.find(':')
                    video = u'-d ' + track[:track_id_index].replace(
                                    common.TRACK_ID, u'').strip()
                index = track.find('audio')
                if not index == -1:
                    if self.configuration['tracknumber']:
                        if str(self.configuration['tracknumber']) == \
                                track[:track_id_index].replace(
                                    common.TRACK_ID, u'').strip():
                            audio =  u'-a ' + track[:track_id_index].replace(
                                            common.TRACK_ID, u'').strip()
                    elif audio == False:
                        audio = u'-a ' + track[:track_id_index].replace(
                                        common.TRACK_ID, u'').strip()
            if audio == False:
                audio = u''
            if video == False:
                video = u''
            if self.configuration['concertcuts']:
                video = u'-D'
            self.configuration['strip_args'] = u'%s %s -S ' % (
                                                video, audio, )
            #
            if self.configuration['concertcuts']:
                verbage = _(
u'''Only an "-a" audio track will be used with
all -D video and -S subtitle tracks removed:
%(strip_args)s''') % self.configuration
            else:
                verbage = _(
u'''Only the first of each "-d" video track and "-a" audio track
will be used with all -S subtitle tracks removed:
%(strip_args)s''') % self.configuration
            self.logger.info(verbage)
        #
        self.configuration['concert_cut_list'] = []
        #
        if self.configuration['rawcutlist']:
            #
            ## Create timecode split list using recordseeks fps value
            splitlist = u''
            fps = self.configuration['fps']
            for cut in self.configuration['keyframe_cuts']:
                start_secs = cut[0] / fps
                start_timecode = make_timestamp(start_secs)
                end_secs = cut[1] / fps
                end_timecode = make_timestamp(end_secs)
                if splitlist:
                    splitlist += u','
                split = u'%s-%s' % (start_timecode, end_timecode)
                splitlist += split
                self.configuration['concert_cut_list'].append(split)
            self.configuration['split_list'] = splitlist
            #
            self.logger.info(u'''Cut timestamps: %(split_list)s\n''' %
                                self.configuration)
        else:
            fps = self.configuration['fps']
            # Handle skipping just the first start to the first keyframe
            start_secs = self.configuration[
                                'first_last_keyframes'][0][0] / fps
            start_timecode = make_timestamp(start_secs)
            end_secs = self.configuration[
                                'first_last_keyframes'][0][1] / fps
            end_timecode = make_timestamp(end_secs)
            split = u'%s-%s' % (start_timecode, end_timecode)
            self.configuration['split_list'] = split
            self.configuration['concert_cut_list'].append(split)
            self.logger.info(
u'''Start copying at the first keyframe to the last keyframe, timestamps: %(split_list)s\n''' %
                                self.configuration)
        #
        return
#
    def _lossless_cut(self,):
        '''
        Cut the source video into segments if required.
        Create specific argument strings based on what mkvmerge processing
        is required then call mkvmerge to create the final mkv video file.
        return nothing
        '''
        #
        if self.configuration['rawcutlist']:
            ## Perform the cuts
            #
            # mkvmerge arguments
            mkvmerge = common.MKVMERGE
            ## Add any user specified mkvmerge cut options that may have
            ## been specified in the lossless_cut.cfg file
            if self.configuration['mkvmerge_cut_addon']:
                mkvmerge += u' ' + self.configuration['mkvmerge_cut_addon']
            #
            arguments = common.CUTS_CMD % self.configuration
            result = commandline_call(mkvmerge, arguments)
            stdout = u''
            if self.configuration['verbose']:
                stdout = result[1]
            self.logger.info(_(u'''mkvmerge perform cuts command:
> %s %s
%s
''' % (mkvmerge, arguments, stdout)))
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(
u'''%s failed to cut the video into segments, aborting script.
Error: %s''') % (common.MKVMERGE, result[1])
                self.logger.critical(verbage)
                sys.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(self.jobstatus.ABORTED))
            #
            ## Build the track appendto list
            ## Format for one video, two audio and a subtitle track e.g.
            ## "%s:0:%s:0,%s:1:%s:1,%s:2:%s:2,%s:3:%s:3"
            self.configuration['append_list'] = u''
            if self.configuration['strip']:
                total_tracks = 3 # Only track 0 and 1 to worry about
            else:
                total_tracks = self.configuration['trackinfo']['total_tracks']
            #
            segments = sorted(glob(u'%(workpath)s/%(recorded_name)s-*.mkv' %
                    self.configuration))
            if len(segments) == 1:
                self.configuration['sourcefile'] = segments[0]
            else:
                for segment in range(len(segments))[:-1]:
                    nxt_segment = segment + 1
                    for track in range(total_tracks)[:-1]:
                        if self.configuration['append_list']:
                            self.configuration['append_list'] += u','
                        self.configuration['append_list'] += \
                            common.APPENDTO_FORMAT % (
                                nxt_segment, track, segment, track, )
            #
            self.configuration['merge'] = u''
            for filename in segments:
                if not self.configuration['merge']:
                    self.configuration['merge'] = u'"%s"' % filename
                else:
                    self.configuration['merge'] += u' +"%s"' % filename
        #
            self.logger.info(_(
u'''
Appendto list:  '%(append_list)s'
Merge list:     '%(merge)s'

MKV metadata (only used if add metadata is "true"):
  Program title:       "%(mkv_title)s"
  Program description: "%(mkv_description)s"
''') % self.configuration)
        #
        merge_common = u'-o "%(mkv_file)s"'
        #
        ## Add any user specified mkvmerge merge options that may have
        ## been specified in the lossless_cut.cfg file
        if self.configuration['mkvmerge_merge_addon']:
            merge_common += u' ' + self.configuration['mkvmerge_merge_addon']
        #
        ## Add a video track delay (plus or minus) in millseconds
        ## Only when one was specified on the command line "-D"
        if self.configuration['delayvideo']:
            merge_common += self.configuration['delayvideo']
        #
        merge_one_segment = u' "%(sourcefile)s"'
        merge_metadata = \
u' --title "%(mkv_title)s" --attachment-description "%(mkv_description)s"' % \
            self.configuration
        #
        if not self.configuration['add_metadata']:
            merge_metadata = u''
        if not self.configuration['rawcutlist'] or \
                            not self.configuration['append_list']:
            if self.configuration.has_key('append_list'):
                arguments = u'%s%s%s' % (merge_common, merge_one_segment,
                                            merge_metadata)
            else:
                arguments = u'%s %s' % (merge_common, common.START_CUT_CMD)
        elif self.configuration['append_list']:
            arguments = u'%s%s%s' % \
                (merge_common, merge_metadata,
            u' --append-mode track %(merge)s --append-to %(append_list)s')
        else:
            arguments = u'%s%s%s' % \
                (merge_common, merge_metadata,
                u' --append-mode track %(merge)s')
    #
    #
############# Do not un-comment unless used for debugging ########
#        for key in sorted(self.configuration.keys()):
#            print u'key(%s) value(%s)' % (key, self.configuration[key])
#        print
#        print u'arguments(%s)' % (arguments % self.configuration)
#        #
#        ## Remove this recording's files from the working directory
#        cleanup_working_dir(self.configuration['workpath'],
#                            self.configuration['recorded_name'])
##        exit(int(self.jobstatus.ABORTED))
#################################################################
    #
    #
        arguments = arguments % self.configuration
        result = commandline_call(common.MKVMERGE, arguments)
        stdout = u''
        if self.configuration['verbose']:
            stdout = result[1]
        self.logger.info(_(u'''mkvmerge create final mkv video file command:
> mkvmerge %s

%s
''' % (arguments, stdout)))
        if not result[0]:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(u'''%s failed to create mkv file, aborting script.
Error: %s''') % (common.MKVMERGE, result[1])
            self.logger.critical(verbage)
            sys.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(self.jobstatus.ABORTED))
        #
        ## Perform user error detection processing
        self.configuration['error_detected'] = self.error_detection()
        #
        # Check that the new mkv video file was created
        if not os.path.isfile(self.configuration['mkv_file']):
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''No MKV file "%(mkv_file)s" was created, aborting script.
Check the log file: "%(logfile)s"''') % self.configuration
            self.logger.critical(verbage)
            sys.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(self.jobstatus.ABORTED))
        #
        # Get the new mkv file size in bytes
        self.configuration['filesize'] = os.path.getsize(
                                        self.configuration['mkv_file'])
        #
        ## If this as an mythvidexport then add the MythVideo record
        if self.configuration['mythvideo_export']:
            try:
                self.mythtvinterface.add_to_mythvideo()
            except self.mythtvinterface.MythError as errmsg:
                verbage = _(
u'''The export to MythVideo failed, aborting script.
Error: %s''') % errmsg
                self.logger.critical(verbage)
                sys.stderr.write(verbage + u'\n')
                #
                ## Remove the source MKV file after transfer
                ## to MythVideo
                os.remove(self.configuration['mkv_file'])
                #
                ## Remove this recording's files from the working
                ## directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(self.jobstatus.ABORTED))
        #
        return
#
    def _process_concert_cuts(self):
        ''' Make each cut segment into a separate file.
        return nothing
        '''
        #
        ## If there is no subtitle then remove it from the file name
        ## format string
        default_sub_var = '%(subtitle)s'
        if not self.configuration['subtitle'] and \
                self.configuration['concertcuts'].find(
                                                default_sub_var) != -1:
            self.configuration['concertcuts'] = \
                    self.configuration['concertcuts'].replace(
                                            default_sub_var, u'').strip()
            if self.configuration['concertcuts'][-1:] == ':':
                self.configuration['concertcuts'] = \
                        self.configuration['concertcuts'][:-1]
        #
        mkvmerge = common.MKVMERGE
        #
        ## Add any user specified mkvmerge cut options that may have
        ## been specified in the lossless_cut.cfg file
        if self.configuration['mkvmerge_cut_addon']:
            mkvmerge += u' ' + self.configuration['mkvmerge_cut_addon']
        #
        ## Check if a video delay has been specified
        if not self.configuration['strip'] and \
                            self.configuration['delayvideo']:
            mkvmerge += self.configuration['delayvideo']
        #
        self.configuration['seg_num'] =  1
        for self.configuration['split_list'] in self.configuration[
                                                        'concert_cut_list']:
            #
            if self.configuration['segment_names'].has_key(
                            self.configuration['seg_num']):
                file_name = self.configuration[
                                'segment_names'][
                                self.configuration['seg_num']] % \
                                    self.configuration
            else:
                file_name = self.configuration['concertcuts'] % \
                                self.configuration
            #
            ## For a move make sure the sub directories
            ## already exist. If not then create them
            if self.configuration['mythvideo_export']:
                directory, basefile = os.path.split(file_name)
            else:
                directory, basefile = os.path.split(
                        os.path.join(self.configuration['movepath'],
                                        file_name))
                if not os.path.isdir(directory):
                    os.makedirs(directory)
            #
            self.configuration['segment_filename'] = basefile
            if self.configuration['mythvideo_export']:
                self.configuration['segment_path'] = \
                                            self.configuration['workpath']
            else:
                self.configuration['segment_path'] = directory
            #
            ## Perform the actual segment cut
            arguments = common.CONCERT_CUTS_CMD % self.configuration
            result = commandline_call(mkvmerge,
                        arguments)
            stdout = u''
            if self.configuration['verbose']:
                stdout = result[1]
            self.logger.info(_(u'''mkvmerge perform Concert Cuts command:
> %s %s
%s
''' % (mkvmerge, arguments, stdout)))
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(
u'''%s failed to Concert Cut the video into segments, aborting script.
Error: %s''') % (common.MKVMERGE, result[1])
                self.logger.critical(verbage)
                sys.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's cut files from the working directory
                for filename in glob(u'%s/*' %
                                        self.configuration['workpath']):
                    os.remove(filename)
                exit(int(self.jobstatus.ABORTED))
            #
            ## Perform user error detection processing
            self.configuration['error_detected'] = self.error_detection()
            #
            ## If this is a mythvidexport then add the MythVideo record
            ## and transfer the cut segment to MythVideo
            if self.configuration['mythvideo_export']:
                self.configuration['mkv_file'] = \
                        u"%(segment_path)s/%(segment_filename)s.mkv" % \
                                self.configuration
                self.configuration['mkv_title'] = basefile
                self.configuration['export_path_file'] = file_name
                self.configuration['filesize'] = \
                        os.path.getsize(self.configuration['mkv_file'])
                try:
                    self.mythtvinterface.add_to_mythvideo()
                except self.mythtvinterface.MythError as errmsg:
                    verbage = _(
u'''The export to MythVideo failed, aborting script.
Error: %s''') % errmsg
                    self.logger.critical(verbage)
                    sys.stderr.write(verbage + u'\n')
                    #
                    ## Delete this recording's cut segment files
                    ## from the working directory
                    for filename in glob(u'%s/*' %
                                        self.configuration['workpath']):
                        os.remove(filename)
                    exit(int(self.jobstatus.ABORTED))
                #
                ## Remove the tramsferred segment from the workpath
                ## directory as it is no longer required
                os.remove(self.configuration['mkv_file'])
            #
            self.configuration['seg_num'] += 1
        #
        return
#
    def _cleanup(self,):
        '''
        Update the original recorded record if the mkv file was not exported
        OR remove the original recording if matches the setting is the
        configuration file.
        Remove the recorded video's temporary file in the working directory
        Remove the recorded video's log file if the flag to delete is True
        return nothing
        '''
        #
        ## Update the original recorded record if the mkv file was not exported
        if not self.configuration['movepath'] and \
                not self.configuration['error_detected']:
            arguments = common.CLEAR_CUTLIST % self.configuration
            result = commandline_call(self.configuration['mythutil'],
                                            arguments)
            stdout = u''
            if self.configuration['verbose']:
                stdout = result[1]
            self.logger.info(_(u'''%s clear cut list command:
> %s %s

%s
''' % (self.configuration['mythutil'], self.configuration['mythutil'],
                arguments, stdout)))
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                sys.stderr.write(
_(u'''%s could not clear the cutlist, aborting script.
Error: %s
''') % (self.configuration['mythutil'], result[1]))
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(self.jobstatus.ABORTED))
            #
            # Update the recorded record and cleanup table entries in
            # recordedseek and recordedmarkup that are no longer valid
            self.mythtvinterface.replace_old_recording()
            #
            ## Either rename or delete the orginal recording file
            if self.configuration['delete_old']:
                os.remove(self.configuration['recordedfile'])
                verbage = \
_(u'''The original recording:
"%s" has been deleted.''') % self.configuration['recordedfile']
                self.logger.info(verbage)
                sys.stdout.write(verbage + u'\n')
            else:
                os.rename(self.configuration['recordedfile'],
                    self.configuration['recordedfile'] + u'.old')
                verbage = \
_(u'''The original recording has been renamed to:
"%s"''') % (self.configuration['recordedfile'] + u'.old')
                self.logger.info(verbage)
                sys.stdout.write(verbage + u'\n')
        #
        ## Remove this recording's files from the working directory
        cleanup_working_dir(self.configuration['workpath'],
                            self.configuration['recorded_name'])
        #
        if self.configuration['mythvideo_export'] and \
                not self.configuration['concertcuts']:
            copied_mkv = os.path.join(self.configuration['recorded_dir'],
                self.configuration['mkv_title'] + u'.mkv', )
            os.remove(copied_mkv)
            self.logger.info(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
    _(u'''Removed mkv file "%s" after exporting to MythVideo.''') %
                copied_mkv)
        #
        ## If this is a MythTVExport or a move then check if
        ## the original recording should be removed as specific
        ## in the configuration file "remove_recorded" section
        if (self.configuration['mythvideo_export'] or \
                self.configuration['movepath']) and \
                not self.configuration['error_detected']:
            self.mythtvinterface.match_and_remove()
        #
        self.logger.info(
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
_(u'''End of loss less commercial cut for "%s" at: %s''') % (
            self.configuration['recordedfile'],
            datetime.now().strftime(common.LL_START_END_FORMAT)))
        #
        ## Remove the recorded video's log file if the delete flag is True
        ## and no user errors were detected
        if not self.configuration['keep_log'] and \
                not self.configuration['error_detected']:
            os.remove(self.configuration['logfile'])
        #
        return
#
    def _display_variables(self, summary=False):
        '''
        Display all the variable that would be used if processing commenced.
        This method is generally used for debugging or when testing the
        environment.
        return nothing
        '''
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        verbage = \
                _(u'''
These are the variables and options to be used when performing a
loss less cut of a MythTV recorded video:

  Lossless Cut version:         %(version)s

  MythTV recorded source video: "%(recordedfile)s"

  The Log file location:        "%(logpath)s"
  The Log file:                 "%(logfile)s"

  Move/Save path for mkv file:  "%(movepath)s"
  Working directory path:       "%(workpath)s"

  Add metadata to mkv file:     "%(add_metadata)s"
  Delete the mpg file:          "%(delete_old)s"
  Keep the log file:            "%(keep_log)s"
  Remove subtitles and
  secondary audio tracks:       "%(strip)s"
  Test the script dependencies: "%(test)s"

  Movie metadata format:        "%(movie_format)s"
  TV Series metadata format:    "%(tvseries_format)s"

  Utilities for extracting subtitles:
    mythtvccextractor args:     "%(mythccextractor_args)s"
    ccextractor args:           "%(ccextractor_args)s"

  Mythvidexport format args:
    Television:                 "%(TVexportfmt)s"
    Movie:                      "%(MOVIEexportfmt)s"
    Generic:                    "%(GENERICexportfmt)s"

  Concert Cuts format args:
    File export or move name:   "%(concertcuts)s"

\n''') % self.configuration
        #
        ## If the DVB Subtitles are set to true show the variables
        if self.configuration['include_dvb_subtitles']:
            verbage = verbage[:-1] + _(
u'''
  DVB Subtitle args:
    Include DVB Subtitles:      "%(include_dvb_subtitles)s"
    Java runtime path:          "%(java)s"
    ProjectX jar path:          "%(projectx_jar_path)s"
    ProjectX SUP format args:   "%(format_sup_values)s"
    Move subtitle position:     "%(moveposition)s"
    Delay VobSub track value:   "%(vobsub_delay)s" ms

\n''') % self.configuration
        #
        if summary:
            sys.stdout.write(verbage)
        else:
            self.logger.info(verbage)
        #
        return
#
    def error_detection(self, ):
        ''' Execute user specified error detection. Depending on the
        results:
        1) Return after no issues were detected
        2) Update the job queue comment and status then return
        3) Update the job queue comment and status clean up working files
           then abort processing
        return true to indicate that an error condition was detected
        return false to indicate that no error condition was detected
        '''
        #
        error_detected = False
        # There may be no user error checking specified
        if not self.configuration['error_detection']:
            return error_detected
        #
        for error in self.configuration['error_detection']:
            arguments = error['bash_command'] % self.configuration
            results = exec_commandline(arguments)
            errors, count_arg = "", ""
            if results[0]:
                count_arg = results[0].strip()
            if results[1]:
                errors = results[1].strip()
            #
            self.logger.info(_(u'''User error detection command:
> %s

STDOUT: "%s"
STDERR: "%s"
''' % (arguments, count_arg, errors)))
            #
            command_worked = True
            self.configuration['error_cnt'] = 0
            #
            if count_arg:
                try:
                    self.configuration['error_cnt'] = int(count_arg)
                except (TypeError, ValueError):
                    command_worked = False
                    # TRANSLATORS: Please leave %s as it is,
                    # because it is needed by the program.
                    # Thank you for contributing to this project.
                    verbage = _(
u'''Your error detection bash command:
> %s
Did not return a valid integer count of the errors detected, aborting the script.
STDOUT results should be nothing or an integer: "%s"
''') % (arguments, results[0])
            #
            if errors and command_worked:
                command_worked = False
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(
u'''Your error detection bash command:
> %s
Returned errors on STDERR, aborting the script.
STDERR results: "%s"
''') % (arguments, errors)
            #
            if not command_worked:
                sys.stderr.write(verbage)
                self.logger.critical(verbage)
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(self.jobstatus.ABORTED))
            #
            ## Check if the threshold was exceeded
            if self.configuration['error_cnt'] < error['threshold']:
                continue
            #
            error_detected = True
            #
            comment = error['comment_string'] % self.configuration
            #
            ## Check if the comment exceeds the field size of a
            ## jobqueue record comment field
            if len(comment) > 127:
                comment = comment[:127]
            #
            ## Set the jobqueue status value
            status = self.jobstatus.ERRORED
            if error['type'] == 'abort':
                status = self.jobstatus.ABORTED
            #
            ## Update the jobqueue status and comment
            self.mythtvinterface.update_jobqueue(status, comment)
            #
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''Your error detection command has indicated an %s should occur.
Examine the log file "%s" for further details.
''') % (error['type'], self.configuration['logfile'])
            sys.stderr.write(verbage)
            self.logger.critical(verbage)
            #
            if error['type'] == 'abort':
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                # Cleanup any mkv file that was created
                # as it is considered useless.
                if os.path.isfile(self.configuration['mkv_file']):
                    os.remove(self.configuration['mkv_file'])
                #
                exit(int(self.jobstatus.ABORTED))
        #
        return error_detected
#
#
if __name__ == "__main__":
    # Check for the help or usage option then exit
    if OPTS.usage:
        sys.stdout.write(USAGE_TEXT)
        exit(int(common.JOBSTATUS().UNKNOWN))
    #
    # Display version and author information then exit
    if OPTS.version:
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        sys.stdout.write(_(u"""
Title: (%s); Version: description(%s); Author: (%s)
%s

""") % (__title__, __version__, __author__, __purpose__ ))
        exit(int(common.JOBSTATUS().UNKNOWN))
    #
    # Verify that the recorded file exists
    if OPTS.recordedfile:
        if OPTS.recordedfile[0] == '~':
            if OPTS.recordedfile[1] == '/':
                OPTS.recordedfile = os.path.join(os.path.expanduser("~"),
                                                OPTS.recordedfile[2:])
            else:
                OPTS.recordedfile = os.path.join(os.path.expanduser("~"),
                                                OPTS.recordedfile[1:])
    if not os.path.isfile(OPTS.recordedfile):
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        sys.stderr.write(_(u"The recorded file (%s) does not exist.\n%s\n"
                            ) % (OPTS.recordedfile, MANDITORY))
        sys.exit(int(common.JOBSTATUS().ABORTED))
    #
    # Check if a "~/.mythtv/lossless_cut.cfg" file exists.
    # If it does not exist then create an initial one
    # in the "~/.mythtv" directory.
    if not os.path.isfile(common.CONFIG_FILE):
        try:
            if not os.path.isdir(common.CONFIG_DIR):
                create_cachedir(common.CONFIG_DIR)
        except Exception as errmsg:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            sys.stderr.write(_(u'''Could not create the directory "%s" to
copy the file "%s" to "%s", aborting script.
''') % (common.CONFIG_DIR, common.INIT_CONFIG_FILE, common.CONFIG_FILE))
            exit(int(common.JOBSTATUS().ABORTED))
        #
        # Initialize the new configuration with default values file
        try:
            create_config_file()
        except IOError as errmsg:
            sys.stderr.write(errmsg)
            exit(int(common.JOBSTATUS().ABORTED))
    #
    # Initialize the loss less cut class
    LOSSLESS_CUT = Mythtvlosslesscut(OPTS)
    #
    # Process the recorded video file according to the command line
    # options and the configuration file settings.
    LOSSLESS_CUT.cut_video_file()
    #
    sys.exit(LOSSLESS_CUT.return_code)
