#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ----------------------
# Name: mythtvinterface.py   Provides all metadata collection functions
#                            between indicator and MythTV
# Python Script
# Author:   R.D. Vaughan
# Purpose:  This python script supports the lossless_cut.py.
#           Providing all MythTV interface functionality.
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
# (http://www.gnu.org/licenses/gpl-2.0.html)
#-------------------------------------
#
"""
__version__ = '0.1.8'
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Refresh the recorded record markup data
#       after a cutlist was generated otherwise
#       the markup data is inaccurate.
#       Fix a bug when the seektable does not have a zero keyframe
#       and the first cut point keyframe is being changed to one
#       greater than it should be.
#       Changed the way DB records are collected for a bug archive
#       report.
# 0.1.3 Added edits for missing fps, first and last frames which
#       indicate that the recording does not have valid database
#       records. If these edits do not pass a message is added
#       the log and displayed on the console then the script
#       aborts with a error return code.
# 0.1.4 Added STDOUT display of SQL errors when inserting records
#       Fixed handling quotations characters in a DB string when
#       collecting data base records for a bug report.
#       Fixed a movie title showing a release year of "(None)" when
#       there is no release year in either EPG or grabber data.
#       Added support deletion of a recording which matches the
#       settings in the configuration file "remove_recording"
#       section
# 0.1.5 Changed the method to get fps, first and last frame from
#       a SQL call to use the python bindings which avoids issues
#       with UTC date conversions in MythTV v0.26 and higher.
#       Replace as many SQL calls as possible with python binding
#       equivalents.
#       Removed the python-dateutil dependency
#       Fixed how the SQL starttime and progstart
#       UTC values were determine. On some MythTV 0.26 installs the values
#       were not correct which caused Lossless Cut be unable to find
#       essential markup record data like FPS and therefore gracefully abort
#       For consistency when replacing a recording reset the commflagged
#       indicator
#       Added a check for the UTCTZ datetime class when MythTV v0.26 and
#       higher
# 0.1.6 Add automatic generation of a cut list when it is empty and there is
#       a skip list. Saves the redundant effort of manually
#       loading the skip list through the MythTV edit UI.
# 0.1.7 Changed automatic generation of a cut list to be optional
# 0.1.8 Acquire the fps, height, width from mediainfo rather than the
#       recorded markup table. This is because those records are not
#       created by MythTV when a scheduled recording occurs when a user
#       is watching LiveTV.
#
__title__ = \
'''mythtvinterface - Providing all MythTV interface functionality'''
__purpose__ = '''
This python script supports the lossless_cut script with
all MythTV interface functionality.
'''

# Common function imports
import os
import time
from socket import gethostname

# Indicator specific imports
from importcode.utilities import set_language, commandline_call, cleanup_working_dir, \
    is_not_punct_char, is_punct_char
import importcode.common as common

## Local variables
# Language translation specific to this desktop
__author__ = common.__author__
_ = set_language()


class Mythtvinterface(object):
    """Main interface to all MythTV Recorded data base records.
    Supports several metadata access methods with the MythTV master backend.
    """

    def __init__(self, logger, configuration):
        #
        self.logger = logger
        self.configuration = configuration
        #
        self.mythdb = None
        self.mythbeconn = None
        self.keyframe_adjust = False
        #
        self.error_messages = {
            'BackendConnectFailed':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'MythTV backend connection failed, error(%s)'),
            'BackendConnectionAttempt':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                 _(u'MythTV backend connection attempt, error(%s)'),
            'ConfigError':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                 _(u'Check that (%s) is correctly configured'),
            'ConfigMissing':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                 _(u'A correctly configured (%s) file must exist'),
            'CreateInstance':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                 _(u'''Creating an instance caused an error in:
MythDB, error(%s)'''),
            'BindingsError':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
            _(u'MythTV python bindings could not be imported, error(%s)'),
            'TVGrabberError':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
            _(u'TV Grabber issue, error(%s)'),
            'MovieGrabberError':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
            _(u'Movie grabber issue, error(%s)'),
            'VersionError1':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
_(u'''Lossless Cut supports MythTV versions 0.24+fixes and higher.
Your version is "%s". You will need to upgrade your MythTV install.'''),
            'VersionError2':
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
_(u'''Lossless Cut cannot support your pre-release version of MythTV.
Your version is "%s".
You will need to upgrade your MythTV install to at least a v0.%d+Fixes release.'''),
        }
        #
        # Find out if the MythTV python bindings can be accessed and
        # instances can be created
        try:
            from MythTV import \
                Recorded, RecordedProgram, Video, MythVideo, VideoGrabber, \
                MythDB, MythBE, MythError, MythLog, OWN_VERSION, Job
            self.Recorded = Recorded
            self.RecordedProgram = RecordedProgram
            self.VideoGrabber = VideoGrabber
            self.ttvdb = VideoGrabber('TV')
            self.tmdb = VideoGrabber('Movie')
            self.MythDB = MythDB
            self.MythBE = MythBE
            self.MythError = MythError
            self.MythLog = MythLog
            self.Video = Video
            self.Job = Job
            self.OWN_VERSION = OWN_VERSION
            #
            self.configuration['mythtv_version'] = \
                                '.'.join([str(i) for i in OWN_VERSION])
            #
            if self.OWN_VERSION[0] == 0:
                pre = '0.'
            else:
                pre = 'pre-0.'
            self.configuration['mythtv_version'] = u'%s%d.%d' % (pre,
                    self.OWN_VERSION[1], self.OWN_VERSION[3])
            #
            ## Lossless Cut only supports MythTV v0.24+fixes and higher
            if self.OWN_VERSION[0] <= 0 and self.OWN_VERSION[1] < common.SUPPORTED_VERSIONS:
                verbage = self.error_messages['VersionError1'] \
                                % self.configuration['mythtv_version']
                self.logger.critical(verbage)
                raise Exception(verbage)
            #
            ## Lossless Cut can ONLY support the current git master
            ## pre-released version of MythTV
            if self.OWN_VERSION[0] <= 0 and self.OWN_VERSION[1] <= common.UNSUPPORTED_PRE_VERSION and \
                        not pre.find('pre-') == -1:
                verbage = self.error_messages['VersionError2'] \
                                % (self.configuration['mythtv_version'],
                                    self.OWN_VERSION[1])
                self.logger.critical(verbage)
                raise Exception(verbage)
            #
            # Establish a MythTV data base connection
            try:
                self.mythdb = self.MythDB()
            except self.MythError as errmsg:
                filename = os.path.expanduser("~") + \
                                '/.mythtv/config.xml'
                if not os.path.isfile(filename):
                    verbage = self.error_messages['ConfigMissing'] \
                                            % filename
                    self.logger.critical(verbage)
                    raise Exception(verbage)
                else:
                    verbage = self.error_messages['ConfigError'] \
                                            % filename
                    self.logger.critical(verbage)
                    raise Exception(verbage)
            except Exception as errmsg:
                verbage = self.error_messages['CreateInstance'] % errmsg
                self.logger.critical(verbage)
                raise Exception(verbage)
            # Establish a Master Backend connection
            if self.mythdb:
                self.localhostname = self.mythdb.gethostname()
                try:
                    self.mythbeconn = self.MythBE(
                            backend=self.localhostname, db=self.mythdb)
                except self.MythError as errmsg:
                    verbage = self.error_messages[
                                    'BackendConnectionAttempt'] \
                                    % errmsg.args[0]
                    self.logger.critical(verbage)
                    raise Exception(verbage)
                self.MythVideo = MythVideo(self.mythdb)
        except Exception as errmsg:
            verbage = self.error_messages['BindingsError'] % errmsg
            self.logger.critical(verbage)
            raise Exception(verbage)
        #
        ## Get the mythvidexport settings if they exist in the data base
        format_str = self.mythdb.settings[\
                            self.localhostname]['mythvideo.TVexportfmt']
        if format_str:
            self.configuration['TVexportfmt'] = format_str
        format_str = self.mythdb.settings[\
                            self.localhostname]['mythvideo.MOVIEexportfmt']
        if format_str:
            self.configuration['MOVIEexportfmt'] = format_str
        format_str = self.mythdb.settings[\
                            self.localhostname]['mythvideo.GENERICexportfmt']
        if format_str:
            self.configuration['GENERICexportfmt'] = format_str
        #
        self.recorded = None
        self.recorded_program = None
        self.vid = None
        self.category = None
        self.metadata = {}
        self.studio = None
        self.new_runtime = None
        #
        # Usually there is only on frame difference between what is
        # in the recored markup table Vs the recorded seek table
        self.markup_frame_difference = 1
        self.keyframe_test_diff = 1
        #
        return    # end __init__()

    def get_recorded_data(self, ):
        ''' Collect information about a recorded video.
        return nothing
        '''
        #
        self.configuration['rawcutlist'] = []
        self.configuration['pre_massage_cutlist'] = []
        self.configuration['keyframe_cuts'] = []
        #
        recorded = list(self.mythdb.searchRecorded(
                        basename=self.configuration['base_name']))
        if not recorded:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''There is no MythTV recorded record for video
file "%s", aborting script.''') % self.configuration['base_name']
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        # Use the first recorded record.
        # There should be only one record per base_name
        self.recorded = recorded[0]
        try:
            self.recorded_program = self.recorded.getRecordedProgram()
        except self.MythError as errmsg:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''There is no MythTV recordedprogram record for the video
file "%s", aborting script.''') % self.configuration['base_name']
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        ## Get this recorded video's recorder info
        self._get_recorder_details()
        #
        # Set starttime and SQL_starttime
        self.configuration['starttime'] = self.recorded.starttime
        self.configuration['progstart'] = self.recorded.progstart
        self._set_sql_starttime()
        #
        ## Save specific data:
        self.configuration['chanid'] = self.recorded.chanid
        self.configuration['starttime'] = self.recorded.starttime
        self.configuration['director'] = u''
        self.configuration['genre'] = self._get_program_genre()
        self.configuration['title'] = self.recorded.title
        self.configuration['series'] = self.recorded.title
        self.configuration['subtitle'] = self.recorded.subtitle
        self.configuration['episode'] = self.recorded.subtitle
        self.configuration['description'] = self.recorded.description
        if self.recorded_program['originalairdate']:
            self.configuration['releasedate'] = \
                self.recorded_program['originalairdate'].strftime('%Y')
        elif self.recorded_program['airdate']:
            self.configuration['releasedate'] = \
                                self.recorded_program['airdate']
        else:
            self.configuration['releasedate'] = None
        #
        if self.OWN_VERSION[1] == 24:
            self.configuration['inetref'], \
            self.configuration['season_num'], \
            self.configuration['episode_num'] = None, None, None
        else:
            self.configuration['inetref'] = self.recorded.inetref
            self.configuration['season_num'] = self.recorded.season
            self.configuration['episode_num'] = self.recorded.episode
        #
        ## Determine fps (frames per second), first and last frame, video
        ## width and height in pixels
        self.configuration['fps'], self.configuration['first_frame'], \
        self.configuration['last_frame'], self.configuration['width'],\
        self.configuration['height'] = \
                            self._get_fps_and_more()
        #
        ## Get missing metadata using the grabbers
        if self.configuration['subtitle'] or (
                            self.configuration['episode_num'] and
                            self.configuration['inetref']):
            self._get_tv_metadata(series=self.configuration['title'],
                        episode=self.configuration['subtitle'],
                        inetref=self.configuration['inetref'],
                        season_num=self.configuration['season_num'],
                        episode_num=self.configuration['episode_num'])
            #
            if self.metadata:
                self.configuration['series'] = self.metadata['title']
                self.recorded['title'] = self.metadata['title']
                #
                self.configuration['inetref'] = \
                        self.metadata['inetref']
                self.configuration['episode'] = \
                        self.metadata['subtitle']
                if self.metadata['description']:
                    self.configuration['description'] = \
                        self.metadata['description']
                self.configuration['season_num'] = \
                        self.metadata['season']
                self.configuration['episode_num'] = \
                        self.metadata['episode']
        elif not self.recorded_program.category_type == 'series':
            self._get_movie_metadata(
                    title=self.configuration['title'],
                    inetref=self.configuration['inetref'])
            if self.metadata:
                self.configuration['inetref'] = \
                        self.metadata['inetref']
                self.configuration['series'] = self.metadata['title']
                self.configuration['title'] = \
                        self.metadata['title']
                self.recorded['title'] = \
                        self.metadata['title']
                if self.metadata['releasedate']:
                    self.configuration['releasedate'] = \
                        self.metadata['releasedate'].strftime('%Y')
                if self.metadata['description']:
                    self.configuration['description'] = \
                        self.metadata['description']
        #
        ## Set the mkv metadata
        if self.configuration['subtitle']:
            if self.configuration['season_num'] and \
                                        self.configuration['episode_num']:
                self.configuration['mkv_title'] = \
                        self.configuration['tvseries_format'] % \
                                                    self.configuration
            else:
                self.configuration['mkv_title'] = u'%s: %s' % (
                                            self.configuration['title'],
                                            self.configuration['subtitle'])
        elif self.recorded_program.category_type == 'series' and \
                not self.configuration['subtitle']:
            self.configuration['mkv_title'] = u'%s' % (
                                            self.configuration['title'],)
        else:
            if self.configuration['releasedate'] and \
                    not self.recorded_program.category_type == 'series':
                self.configuration['mkv_title'] =  \
                        self.configuration['movie_format'] % \
                                                    self.configuration
            else:
                self.configuration['mkv_title'] = self.configuration['title']
        #
        # Remove any quotes from the description which may
        # impact the mkvmerge command line
        self.configuration['mkv_description'] = \
                    self.configuration['description'].replace(u'"', u"'")
        #
        ## Set mythvidexport format and information
        self.configuration['contenttype'] = 2 # Default to a TV show
        if self.recorded_program.category_type == 'series':
            if self.configuration['subtitle'] and \
                        self.configuration['episode_num'] > 0:
                self.configuration['export_format'] = \
                            self.configuration['TVexportfmt']
            else:
                self.configuration['export_format'] = \
                            self.configuration['GENERICexportfmt']
                # Only include ":", subtitle in the format when one exists
                if not self.configuration['subtitle']:
                    self.configuration['export_format'] = \
                        self.configuration['export_format'].replace(
                            u':', u'').replace(
                            u'-', u'').replace(
                            u'%SUBTITLE%', u'').strip()
        elif self.recorded_program.category_type == 'movie':
            self.configuration['contenttype'] = 1 # Set to movie
            if self.configuration['releasedate']:
                self.configuration['export_format'] = \
                        self.configuration['MOVIEexportfmt']
            else:
                self.configuration['export_format'] = \
                        self.configuration['MOVIEexportfmt'].replace(
                                        u'(%(releasedate)s)', u'').strip()
        else:
            self.configuration['export_format'] = \
                            self.configuration['GENERICexportfmt']
        #
        ## Check if the user wants %GENRE% as an export subdirectory but
        ## there is no Genre for this recording. Substitute "Unknown"
        ## for the Genre and log the issue.
        if self.category:
            self.configuration['genre'] = self.category
        if self.configuration['export_format'].find('%GENRE%') != -1 and \
                not self.configuration['genre'] and \
                self.configuration['mythvideo_export']:
            self.configuration['genre'] = u'Unknown'
            verbage = _(
u'''The export path and file name format for this recording is:
"%(export_format)s" but no genre can be located, therefore "Unknown"
will be used.
''') % self.configuration
            self.logger.info(verbage)
            self.stderr.write(verbage + u'\n')
            self.configuration['genre'] = u"Unknown"
        #
        if not self.configuration['director']:
            for member in self.recorded.cast:
                if member.role == 'director':
                    self.configuration['director'] = member.name
                break
        self.configuration['storagegroup'] = self.recorded.storagegroup
        self.configuration['hostname'] = self.recorded.hostname
        #
        self.configuration['mythvidexport_rep'] = (
            ('%TITLE%','%(series)s'),
            ('%SUBTITLE%','%(subtitle)s'),
            ('%SEASON%','%(season_num)d'),
            ('%SEASONPAD%','%(season_num)02d'),
            ('%EPISODE%','%(episode_num)d'),
            ('%EPISODEPAD%','%(episode_num)02d'),
            ('%YEAR%','%(releasedate)s'),
            ('%GENRE%','%(genre)s'),
            ('%DIRECTOR%','%(director)s'),
            # Added for Concert Cuts processing
            ('%ARTIST%','%(artist)s'),
            ('%ALBUM%','%(album)s'),
            ('%SEGNUM%','%(seg_num)d'),
            ('%SEGNUMPAD%','%(seg_num)02d'),
        )
        #
        self._get_cutlist_data()
        #
        ## Log what metadata to identify this video has been found
        verbage = _(
u'''The following metadata has been found for this recorded video:
  Internet Reference number: %(inetref)s
  Title: "%(series)s", Subtitle: "%(subtitle)s"
  Series number: %(season_num)s, Episode number: %(episode_num)s
  Release date: %(releasedate)s
  Description: "%(mkv_description)s"

  MKV metadata tite: "%(mkv_title)s"
  Export filename format: "%(export_format)s"
''') % self.configuration
        self.logger.info(verbage)
        #
        return
#
    def _get_cutlist_data(self, ):
        ''' Get cutlist details and massage frame numbers into keyframes.
        return nothing
        '''
        #
        ## If the cutlist exists then adjust to keyframes
        self.configuration['rawcutlist'] = self.recorded.markup.getcutlist()
        #
        if not self.configuration['rawcutlist'] and \
                                self.configuration['gencutlist']:
            ## Generate the cutlist
            arguments = ('--gencutlist ' + common.GEN_GET_CUTLIST_CMD) % \
                            self.configuration
            result = commandline_call(self.configuration['mythutil'],
                                            arguments)
            stdout = u''
            if self.configuration['verbose']:
                stdout = result[1]
            self.logger.info(_(u'''%s generate cut list command:
> %s %s

%s''') % (self.configuration['mythutil'], self.configuration['mythutil'],
                            arguments, stdout))
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = \
_(u'''%s could not generate the cut list, aborting script.
Error: %s''') % (self.configuration['mythutil'], result[1])
                self.logger.critical(verbage)
                self.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
            #
            ## The current recorded record and its data needs to be
            ## Refreshed as the markup table cutlist has changed
            self.recorded = list(self.mythdb.searchRecorded(
                        basename=self.configuration['base_name']))[0]
            #
            ## Now the markup information is accurate
            self.configuration['rawcutlist'] = \
                                    self.recorded.markup.getcutlist()
        #
        if not self.configuration['rawcutlist']:
            self.configuration['first_last_keyframes'] = \
                                self._process_cutlist(first_last=True)
        #
        self.configuration['pre_massage_cutlist'] = \
                        self.recorded.markup.getuncutlist()
        if self.configuration['pre_massage_cutlist']:
            self._process_cutlist()
        #
        return
#
    def _get_fps_and_more(self, ):
        ''' Get a recorded file's fps rate, first frame and last frame.
        return fps, first frame, last frame
        '''
        # Get video track FPS, Height and Width from mediainfo data
        fps = None
        try:
            fps = int(self.configuration['trackinfo'][
                        'video_track_details']['Original_frame_rate'])
        except (ValueError, TypeError):
            pass
        #
        height = None
        try:
            height = int(self.configuration['trackinfo'][
                                'video_track_details']['Height'])
        except (ValueError, TypeError):
            pass
        #
        width = None
        try:
            width = int(self.configuration['trackinfo'][
                                'video_track_details']['Width'])
        except (ValueError, TypeError):
            pass
        #
        ## If mediainfo did not have the required data attempt to get it from
        ## the recordedmarkup table
        #
        if fps == None:
            ## Get the frames per second value
            try:
                fps = [mark.data for mark in self.recorded.markup
                                if mark.type == 32][0]
                if fps == None:
                    raise IndexError
            except IndexError:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(
u'''This MythTV recording has no markup table FPS (frames per second).
It is likely that the markup table records for this recording is
invalid, aborting script.
''')
                self.logger.critical(verbage)
                self.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
        #
        fps = str(fps)
        #
        # fps in database is shifted 3 digits to the left
        # of the decimal point from its true value
        fps = float(fps[:2] + '.' + fps[2:])
        #
        if height == None:
            ## Get video height
            try:
                height = [mark.data for mark in self.recorded.markup
                                    if mark.type == 31][0]
                if height == None:
                    raise IndexError
            except IndexError:
                height = 0
        #
        if width == None:
            ## Get video width
            try:
                width = [mark.data for mark in self.recorded.markup
                                    if mark.type == 30][0]
                if width == None:
                    raise IndexError
            except IndexError:
                width = 0
        #
        ## Get firstframe
        try:
            firstframe = [seek.mark for seek in self.recorded.seek
                                        if seek.type == 9][0]
            if firstframe == None:
                raise IndexError
        except IndexError:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = \
_(u'''This MythTV recording has no recordedseek table first keyframe record.
It is likely that the recordedseek table records for this recording is
invalid, aborting script.
''')
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        ## Get lastframe
        try:
            lastframe = [seek.mark for seek in self.recorded.seek
                                        if seek.type == 9][-1]
            if lastframe == None:
                raise IndexError
        except IndexError:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''This MythTV recording has no recordedseek table last keyframe record.
It is likely that the recordedseek table records for this recording is
invalid, aborting script.
''')
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        return fps, firstframe, lastframe, width, height
#
    def _process_cutlist(self, first_last=False):
        ''' Adjust each cut's start frame number to the next <= keyframe
        Adjust each cut's end frame number to the next >= keyframe
        Log original INCLUSIVE cut list and massaged cutlist
        return nothing
        '''
        #
        ## Find keyframe less than or equal to frame
        def less_than(frame):
            '''Find a keyframe that is less than or equal to a input frame
            return the keyframe or if none found return the original frame
            '''
            try:
                keyframe = [seek.mark for seek in self.recorded.seek
                            if seek.type == 9 and seek.mark <= frame][-1]
                if keyframe == None:
                    raise IndexError
            except IndexError:
                return frame
            #
            return keyframe
        #
        ## Find keyframe greater than or equal to frame
        def greater_than(frame):
            '''Find a keyframe that is less than or equal to a input frame
            return the keyframe or if none found return the original frame
            '''
            try:
                keyframe = [seek.mark for seek in self.recorded.seek
                            if seek.type == 9 and seek.mark >= frame][0]
                if keyframe == None:
                    raise IndexError
            except IndexError:
                return frame
            #
            return keyframe
        #
        # If this is a copy then the cutlist is the first and last keyframes
        if first_last:
            cut_frames = [[self.configuration['first_frame'],
                                self.configuration['last_frame']]]
        else:
            cut_frames = self.configuration['pre_massage_cutlist']
        #
        first_frame_zero = True
        #
        ## !!!!Not sure if the frame difference of "3" is specific
        ## to HDPVR recordings or other devices as well
        if not self.configuration['first_frame'] == 0:
            first_frame_zero = False
            self.markup_frame_difference = 3
            self.keyframe_test_diff = 2
        #
        cutlist = []
        for start_end in cut_frames:
            if start_end[0] >= self.configuration['last_frame'] or \
                    start_end[1] == 0:
                continue
            #
            start, end = 0.0, 0.0
            # Adjust First frame to the next higher keyframe
            # as it prevents corruption at the beginning of the mkv file
            # on at least HDPVR recordings.
            self.configuration['frame'] = None
            if start_end[0] == 0:
                if self.keyframe_adjust:
                    self.configuration['frame'] = 0
                    start = less_than(self.configuration['frame'])
                else:
                    self.configuration['frame'] = \
                            self.configuration['first_frame'] + 1
                    start = greater_than(self.configuration['frame'])
            elif start_end[0]:
                if self.keyframe_adjust:
                    if first_frame_zero:
                        self.configuration['frame'] = start_end[0] + \
                                        self.markup_frame_difference
                        start = less_than(self.configuration['frame'])
                    else:
                        self.configuration['frame'] = start_end[0] - \
                                        self.markup_frame_difference
                        start = greater_than(self.configuration['frame'])
                else:
                    if first_frame_zero:
                        self.configuration['frame'] = start_end[0] - \
                                        self.markup_frame_difference
                    else:
                        self.configuration['frame'] = start_end[0] + \
                                        self.markup_frame_difference
                    start = greater_than(self.configuration['frame'])
            #
            if self.configuration['frame'] != None:
                if not self.keyframe_adjust:
                    start = float(start)
            #
            end = float(self.configuration['last_frame'])
            if start_end[1]:
                # Need to adjust end frame number as the recordedseek
                # keyframes are less than the keyframes
                # that --getcutlist displays
                if self.keyframe_adjust and \
                    not first_frame_zero and start_end[1] <= \
                                    self.configuration['first_frame'] or \
                                    start_end[1] == \
                                    self.configuration['first_frame'] + \
                                    self.markup_frame_difference:
                    self.configuration['frame'] = \
                                    self.configuration['first_frame']
                elif self.keyframe_adjust:
                    self.configuration['frame'] = \
                            start_end[1] - self.markup_frame_difference
                elif not first_frame_zero and start_end[1] <= \
                                    self.configuration['first_frame']:
                    self.configuration['frame'] = \
                                    self.configuration['first_frame'] + 1
                elif not first_frame_zero:
                    self.configuration['frame'] = start_end[1] - \
                        self.markup_frame_difference - 1
                else:
                    self.configuration['frame'] = start_end[1] - \
                        self.markup_frame_difference - 1
                #
                end = greater_than(self.configuration['frame'])
                #
                if not self.keyframe_adjust:
                    end = float(end)
            #
            if start >= self.configuration['last_frame']:
                continue
            if start == end:
                continue
            if start == 0.0 and end == 0.0:
                continue
            #
            cutlist.append([start, end])
        #
        if first_last:
            return cutlist
        else:
            self.configuration['keyframe_cuts'] = cutlist
        #
        if not self.keyframe_adjust:
            verbage = _(u'''
Cutlist:
    Original:           (%(rawcutlist)s)
    Inclusive:          (%(pre_massage_cutlist)s)
    Keyframe adjusted:  (%(keyframe_cuts)s)
''') % self.configuration
            self.logger.info(verbage)
        #
        return
#
    def replace_old_recording(self, ):
        ''' Update the recorded record with new video file name at its size
        Clear the skip list
        Refresh the recording's recordedseek table entries
        Cleanup the recording's recordedmarkup table entries
        return nothing
        '''
        #
        # Clear the skip list
        arguments = common.CLEAR_SKIPLIST % self.configuration
        result = commandline_call(self.configuration['mythutil'], arguments)
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
            verbage = \
_(u'''%(mythutil)s could not clear the skiplist, aborting script.
Error: %s
''') % (self.configuration, result[1])
            self.logger.critical(verbage)
            self.stderr.write(verbage)
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        ## Update the recorded record with the new mkv video filename
        ## and zero out the cutlist and commflagged fields, also
        ## change the filesize
        self.recorded.cutlist = 0
        self.recorded.commflagged = 0
        self.recorded.filesize = self.configuration['filesize']
        self.recorded.basename = self.configuration['recorded_name'] + \
                                                            u'.mkv'
        #
        ## Get the mkv video's duration for the recorded markup
        ## type 33 record update
        self._get_new_duration()
        #
        ## Delete all recordedseek records for this recording
        self.recorded.seek.clean()
        #
        ## Update/change/delete recordedmarkup table records
        # Update recordedmarkup type 33 video duration in milliseconds
        for mark in self.recorded.markup:
            if mark['type'] == 33:
                mark['data'] = self.configuration['new_duration']
                break
        #
        ####### wagnerrp's advice:
        # Remove entries from the recordedmarkup table that are no
        # longer valid
        # Types: MARK_COMM_START, MARK_COMM_END, MARK_CUT_START,
        #        MARK_CUT_END, MARK_PLACEHOLDER, MARK_GOP_START,
        #        MARK_KEYFRAME, MARK_SCENE_CHANGE, and MARK_GOP_BYFRAME
        #        should not show up.
        # --clearskiplist removes: MARK_CUT_START, MARK_CUT_END
        # --clearcut list removes: MARK_COMM_START, MARK_COMM_END
        # Gets properly reset with --clear cut and skip list:
        # MARK_UPDATED_CUT    = -3
        # MARK_PLACEHOLDER    = -2
        ### Values that do not need to be modified even when
        ### the cut mkv replaces the recorded records basename
        ### field value
        # MARK_ASPECT_1_1     = 10
        # MARK_ASPECT_4_3     = 11
        # MARK_ASPECT_16_9    = 12
        # MARK_ASPECT_2_21_1  = 13
        # MARK_ASPECT_CUSTOM  = 14
        # MARK_VIDEO_WIDTH    = 30
        # MARK_VIDEO_HEIGHT   = 31
        # MARK_VIDEO_RATE     = 32
        #
        ### Types to be removed:
        # MARK_UNSET          = -10
        # MARK_PLACEHOLDER    = -2
        # MARK_BOOKMARK       = 2
        # MARK_BLANK_FRAME    = 3
        # MARK_GOP_START      = 6
        # MARK_KEYFRAME       = 7
        # MARK_SCENE_CHANGE   = 8
        # MARK_GOP_BYFRAME    = 9
        # MARK_TOTAL_FRAMES   = 34
        #
        ## Delete all recordedmarkup records of specific types
        ## for this recording
        self.recorded.markup[:] = [mark for mark in self.recorded.markup
                                    if not mark['type'] in
                                    [-10, -2, 2, 3, 6, 7, 8 , 9, 34 ] ]
        #
        ## Commit all of the changes
        self.recorded.update()
        #
        return
#
    def _get_new_duration(self,):
        ''' Calculate the new mkv file's play time (duration).
        return nothing
        '''
        ## Get the mkv video's duration for the recorded markup
        ## type 33 record update
        result = commandline_call('mkvinfo',
                        u'"%s"' % self.configuration['mkv_file'])
        stdout = u''
        if self.configuration['verbose']:
            stdout = result[1]
        self.logger.info(
_(u'''mkvinfo used to find final mkv file playback duration:
> mkvinfo "%s"

%s
''') % (self.configuration['mkv_file'], stdout))
        if not result[0]:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = \
_(u'''mkvinfo could not get mkv file information, aborting script.
Error: %s''') % (result[1])
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        dur_str = u' Duration: '
        dur_len = len(dur_str)
        index = result[1].find(dur_str)
        if index == -1:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = \
_(u'''mkvinfo could not find the mkv video's duration, aborting script.''')
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        index += dur_len
        index2 = result[1][index:].find('s') + index
        # Video length in rounded minutes
        self.new_runtime = int(round(float(result[1][index:index2]) / 60))
        # Video duration in milliseconds
        self.configuration['new_duration'] = int(result[1][
                                        index:index2].replace(u'.', u''))
        #
        return
#
    def adjust_frame_numbers(self, ):
        '''
        Check if the recording has either a skip list and or cutlist.
        If neither log a message and exit otherwise adjust the corresponding
        recordedmarkup records with the closest keyframe found in the
        recordedseek table.
        Start frame numbers are adjusted with the <= seek table value
        End frame numbers are adjusted with the >= seek table value
        return nothing
        '''
        self.keyframe_adjust = True
        #
        ## Find the recorded record for this MythTV recording
        recorded = list(self.mythdb.searchRecorded(
                        basename = self.configuration['base_name']))
        if not recorded:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''There is no MythTV recorded record for video
file "%s", aborting script.''') % self.configuration['base_name']
            self.logger.critical(verbage)
            self.stderr.write(verbage + u'\n')
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        # Use the first recorded record.
        # There should be only one record per base_name
        self.recorded = recorded[0]
        self.configuration['chanid'] = self.recorded.chanid
        self.configuration['starttime'] = self.recorded.starttime
        self.configuration['progstart'] = self.recorded.progstart
        #
        if not self.configuration.has_key('SQL_starttime') or \
                not self.configuration.has_key('SQL_progstart'):
            self._set_sql_starttime()
        #
        ## Get the skip and cut list values
        skiplist = self.recorded.markup.getskiplist()
        cutlist = self.recorded.markup.getcutlist()
        #
        ## Log a message and exit if no values found
        if not skiplist and not cutlist:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            verbage = _(
u'''There are no skip or cut lists for video
file "%s", nothing for this script to do.''') % self.configuration['base_name']
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            return
        #
        ## Determine fps (frames per second) and the first and last frame
        self.configuration['fps'], self.configuration['first_frame'], \
        self.configuration['last_frame'], self.configuration['width'],\
        self.configuration['height'] = \
                            self._get_fps_and_more()
        #
        ## Find a corresponding keyframe number for each skip or cut frame
        skip_done = False
        for frame_list in [skiplist, cutlist]:
            #
            if skip_done:
                which_list = u'Cut list'
            else:
                which_list = u'Skip list'
            #
            if not frame_list:
                verbage = _(
        u'''The %s is empty''') % which_list
                self.logger.info(verbage)
                self.stderr.write(verbage + u'\n')
                skip_done = True
                continue
            if not skip_done:
                startend_types = [4, 5]
            else:
                startend_types = [0, 1]
            #
            self.configuration['keyframe_cuts'] = []
            self.configuration['pre_massage_cutlist'] = frame_list
            self._process_cutlist()
            #
            ## Check if the skip list frame numbers are already keyframes
            ## All key frames get an offset added to them to account for
            ## the recordedmarkup table using frame numbers that are
            ## higher than those in the recordedseek table
            change = False
            for count in range(len(self.configuration['keyframe_cuts'])):
                for startend in range(0, 2):
                    if (self.configuration['keyframe_cuts'][
                                    count][startend] == \
                                    frame_list[count][startend]) or \
                        (self.configuration['keyframe_cuts'][
                            count][startend] + \
                                self.markup_frame_difference == \
                                frame_list[count][startend]):
                        continue
                    if startend == 1 and \
                            frame_list[count][startend] == 9999999:
                        continue
                    self.configuration['keyframe_cuts'][
                            count][startend] += self.markup_frame_difference
                    change = True
            if not change:
                verbage = _(
    u'''The %s already has keyframe values''') % which_list
                self.logger.info(verbage)
                self.stdout.write(verbage + u'\n')
                skip_done = True
                continue
            #            #
            verbage = _(
u'''The %s and it's equivalent keyframe values:
%s:            %s
%s keyframes:  %s
''') % (which_list, which_list, frame_list,
                which_list, self.configuration['keyframe_cuts'])
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            #
            for count in range(len(self.configuration['keyframe_cuts'])):
                for count in range(len(frame_list)):
                    for startend in range(0, 2):
                        for markuptype in startend_types:
                            mark = frame_list[count][startend]
                            key_mark = self.configuration['keyframe_cuts'][
                                                    count][startend]
                            for markup in self.recorded.markup:
                                if markup['mark'] == mark and \
                                        markup['type'] == markuptype:
                                    markup['mark'] = key_mark
            #
            skip_done = True
        #
        ## Commit the changes
        self.recorded.update()
        #
        ## Load the adjusted skip list as a cut list if
        ## there is no existing cutlist
        if self.configuration['gencutlist'] and (skiplist and not cutlist):
            # Generate the cut list
            arguments = common.GEN_CUTLIST % self.configuration
            result = commandline_call(
                            self.configuration['mythutil'], arguments)
            #
            self.logger.info(_(u'''%s Generate the cut list command:
> %s %s

%s
''' % (self.configuration['mythutil'], self.configuration['mythutil'],
                                arguments, result[1])))
            if not result[0]:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = \
_(u'''%(mythutil)s could not Generate the cutlist, aborting script.
Error: %s
''') % (self.configuration, result[1])
                self.logger.critical(verbage)
                self.stderr.write(verbage)
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
            #
            self.stderr.write(
                    _(u'''Successfully generated a new cut list\n\n'''))
        #
        return
#
    def _set_sql_starttime(self,):
        ''' Set the SQL starttime based on whether the starttime
        is a UTC aware value like in MythTV v0.26 and higher or
        the UTC unaware values like in MythTV v0.24 and 0.25
        return nothing
        '''
        #
        if self.OWN_VERSION[1] >= 26:
            if str(type(self.recorded.starttime)).find(
                                    "MythTV.utility.dt.datetime") == -1:
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                verbage = _(
u'''Your installed version of MythTV does not support the UTCTZ
datetime class. You must upgrade you install of v0.26+fixes and higher
or downgrade to an earlier version.
Your installed version has been detected as "%s", aborting script.''') % \
                    self.configuration['mythtv_version']
                self.logger.critical(verbage)
                self.stderr.write(verbage + u'\n')
                #
                ## Remove this recording's files from the working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
            #
            self.configuration['SQL_starttime'] = \
                self.configuration['starttime'].astimezone(
                        self.configuration['starttime'].UTCTZ()).strftime(
                                            common.DATETIME_SQL_FORMAT)
            self.configuration['SQL_progstart'] = \
                self.configuration['progstart'].astimezone(
                        self.configuration['progstart'].UTCTZ()).strftime(
                                            common.DATETIME_SQL_FORMAT)
        else:
            self.configuration['SQL_starttime'] = \
                        self.configuration['starttime']
            self.configuration['SQL_progstart'] = \
                        self.configuration['progstart']
        #
        return
#
    def _get_recorder_details(self, ):
        ''' Using the channel number for the recorded video to get
        the recording device details to be used for display,
        bug and script success reporting.
        return nothing
        '''
        #
        self.configuration['recorder_displayname'] = "Unknown"
        self.configuration['recorders_cardtype'] = "Unknown"
        self.configuration['recorders_defaultinput'] = "Unknown"
        self.configuration['recorders_videodevice'] = "Unknown"
        self.configuration['recorders_audiodevice'] = "Unknown"
        self.configuration['recorders_hostname'] = "Unknown"
        #
        ## Get a MythTV data base cursor
        cursor = self.mythdb.cursor()
        #
        sql_cmd = common.SQL_GET_SOURCEID % self.recorded.chanid
        cursor.execute(sql_cmd)
        channel = cursor.fetchall()
        if not len(channel) > 0:
            self.logger.info(
_(u'''There is no channel record for chanid "%d", skipping getting recorder details.''' %
                self.recorded.chanid))
            return
        #
        sql_cmd = common.SQL_GET_CARDINFO % channel[0][0]
        cursor.execute(sql_cmd)
        cardinfo = cursor.fetchall()
        if not len(cardinfo) > 0:
            self.logger.info(
_(u'''There is no cardinfo record for sourceid "%d", skipping getting recorder details.''' %
                    channel[0][0]))
            return
        #
        sql_cmd = common.SQL_GET_CARDID % cardinfo[0][0]
        cursor.execute(sql_cmd)
        capturecard = cursor.fetchall()
        if not len(capturecard) > 0:
            self.logger.info(
_(u'''There is no capturecard record for cardid "%d", skipping getting recorder details.''' %
                    cardinfo[0][0]))
            return
        #
        self.configuration['recorder_displayname'] = cardinfo[0][1]
        self.configuration['recorders_cardtype'] = capturecard[0][0]
        self.configuration['recorders_defaultinput'] = capturecard[0][1]
        self.configuration['recorders_videodevice'] = capturecard[0][2]
        self.configuration['recorders_audiodevice'] = capturecard[0][3]
        self.configuration['recorders_hostname'] = capturecard[0][4]
        #
        cursor.close()
        #
        return
#
    def _get_program_genre(self, ):
        ''' Get the first genre in the program guide for the recorded video.
        return the first genre from the program guide
        '''
        ## Get a MythTV data base cursor
        cursor = self.mythdb.cursor()
        #
        sql_cmd = common.SQL_GET_GENRE % self.configuration
        cursor.execute(sql_cmd)
        program = cursor.fetchall()
        #
        cursor.close()
        #
        if not len(program) > 0:
            self.logger.info(
_(u'''There is no program guide for this recorded video, skipping getting the genre.'''))
            return u""
        #
        return program[0][0]
#
    def is_unique(self, ):
        ''' Check if the MythVideo file already exists.
        return True or False
        '''
        try:
            list(self.MythVideo.searchVideos(custom=(("filename=%s",
                    self.configuration['export_path_file'] + u'.mkv'),)))[0]
        except IndexError:
            return False
        #
        return True
#
    def add_to_mythvideo(self, ):
        ''' Add the exported video to MythVideo.
        return nothing
        '''
        #
        # Set recorded record basename to the new mkv file
        self.recorded.basename = self.configuration['mkv_title'] + u'.mkv'
        self.recorded.filesize = self.configuration['filesize']
        #
        # Make an empty MythVideo record
        self.vid = self.Video(db=self.mythdb).create({
                'title':'',
                'filename': self.configuration['export_path_file'] + u'.mkv',
                'host': gethostname()})
        self.vid._db.gethostname()
        #
        # Add the metadata
        if self.metadata:
            self.vid.importMetadata(self.metadata)
            if self.metadata.has_key('releasedate'):
                self.vid.releasedate = self.metadata['releasedate']
            if self.studio:
                self.vid.studio = self.studio
            if self.category:
                self.vid.category = self.category
        else:
            self._get_generic()
        self.vid.contenttype = self.configuration['contenttype']
        #
        ## Add the artwork if it already exists
        if not self.configuration['v024'] and \
                    self.configuration['inetref']:
            artworkArray = list(self.mythdb.searchArtwork(
                                inetref=self.configuration['inetref']))
            keys = ['coverart', 'fanart', 'banner']
            if len(artworkArray):
                first_match = None
                for artwork in artworkArray:
                    # Make sure that this artwork record is not
                    # just a duplicate inetref between the two grabber sites
                    if not \
                        self.recorded_program.category_type == 'series' and \
                            not self.configuration['subtitle'] and \
                            self.configuration['season_num'] == 0:
                        if not artwork.season == 0:
                            continue
                    if not first_match:
                        first_match = artwork
                    #
                    ## Try to find the graphics for the specific season
                    if not self.configuration['season_num'] == \
                            artwork.season:
                        continue
                    for key in keys:
                        if key == 'coverart':
                            self.vid['coverfile'] = artwork[key]
                        else:
                            self.vid[key] = artwork[key]
                    break
                else:
                    # Default to the artwork even when it does not match
                    # the specific season
                    if first_match:
                        for key in keys:
                            if key == 'coverart':
                                self.vid['coverfile'] = artwork[key]
                            else:
                                self.vid[key] = artwork[key]
        #
        self.logger.info(_(u'''Updating video metadata complete'''))
        #
        # Copy to MythVideo
        try:
            self.copy()
        except Exception as errmsg:
            self.logger.critical(
_(u'''Export to MythVideo, aborting script.
Error: %s''') % errmsg)
            # Clean up the unused MythVideo record
            self.Video(self.vid[u'intid'], db=self.mythdb).delete()
            #
            ## Remove this recording's files from the working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        # Adjust the duration that the video plays after cutting
        self._get_new_duration()
        self.vid.length = self.new_runtime
        #
        ## For Concert Cuts leave the season unchanged
        ## When none set the episode to the segment number
        if self.configuration['concertcuts'] and not self.vid.episode:
            self.vid.episode = self.configuration['seg_num']
        #
        # Update the MythVideo record
        self.vid.update()
        #
        return
#
    def copy(self):
        '''Copy the lossless cut mkv file to the
        proper MythVideo storage group which could be on a different machine.
        return nothing
        '''
        #
        stime = time.time()
        if self.configuration['concertcuts']:
            srcsize = os.path.getsize(self.configuration['mkv_file'])
        else:
            srcsize = self.recorded.filesize
        htime = [stime, stime, stime, stime]
        #
        verbage = (_(u'''
Copying "%s"''') % self.configuration['mkv_file']
                    + _(u" to myth://Videos@%s/%s") %
                    (self.vid.host, self.vid.filename))
        self.logger.info(verbage)
#        self.stdout.write((verbage + u'\n\n'))
        #
        self.logger.info('1')
        srcfp = open((self.configuration['mkv_file']).encode('utf-8'), 'r')
        self.logger.info('2')
        dstfp = self.vid.open('w')
        self.logger.info('3')
        #
        tsize = 2**24
        while tsize == 2**24:
            self.logger.info('4')
            tsize = min(tsize, srcsize - dstfp.tell())
            self.logger.info('5')
            dstfp.write(srcfp.read(tsize))
            self.logger.info('6')
            htime.append(time.time())
        #
        self.logger.info('7')
        srcfp.close()
        self.logger.info('8')
        dstfp.close()
        self.logger.info('9')
        #
        self.vid.hash = self.vid.getHash()
        #
        self.logger.info(_(u"Transfer Complete %d seconds elapsed") %
                        int(time.time()-stime))
        #
        return
#
    def _get_tv_metadata(self, series=None, episode=None, inetref=False,
                                    season_num=None, episode_num=None):
        ''' Use the grabber (internal ttvdb) or grabber in the settings
        to get episode specific metadata.
        return nothing
        '''
        self.metadata = {}
        self.studio = None
        self.category = None
        #
        try:
            if inetref:
                try:
                    self.metadata = self.ttvdb.grabInetref(inetref,
                                    season=season_num, episode=episode_num)
                    # Default to the first studio and category
                    if self.metadata.studios:
                        self.studio = self.metadata.studios[0]
                    if self.metadata.categories:
                        self.category = self.metadata.categories[0]
                    self.logger.info(
                            _(u'''Found TV series "%s" Episode "%s".''') %
                            (self.metadata['title'],
                            self.metadata['subtitle']))
                except StopIteration:
                    pass
            #
            if not self.metadata and series and episode:
                try:
                    self.metadata = self.ttvdb.sortedSearch(
                                    series, episode)
                    self.logger.info(
                            _(u'''Found TV series "%s" Episode "%s".''') %
                            (self.metadata[0]['title'],
                            self.metadata[0]['subtitle']))
                except IndexError:
                    self.logger.info(
                            _(u'''Falling back to generic export.'''))
                    if not self.configuration['v024']:
                        self.metadata = self.recorded.exportMetadata()
                    return
                #
                if (len(self.metadata) > 1) & \
                        (self.metadata[0].levenshtein > 0):
                    self.logger.info(
                            _(u'''Falling back to generic export.'''))
                    if not self.configuration['v024']:
                        self.metadata = self.recorded.exportMetadata()
                else:
                    self.metadata = self.metadata[0]
                    # Default to the first studio and category
                    if self.metadata.studios:
                        self.studio = self.metadata.studios[0]
                    if self.metadata.categories:
                        self.category = self.metadata.categories[0]
        except self.MythError as errmsg:
            self.logger.info(
                _(u'''MythError, falling back to generic export.
Error %s''') % errmsg)
            if not self.configuration['v024']:
                self.metadata = self.recorded.exportMetadata()
        #
        return
#
    def _get_movie_metadata(self, title=None, inetref=False):
        ''' Use the grabber (internal tmdb/tmdb3) or grabber in the settings
        to get movie specific metadata.
        return nothing
        '''
        self.metadata = {}
        self.studio = None
        self.category = None
        #
        try:
            if inetref:
                try:
                    self.metadata = self.tmdb.grabInetref(inetref)
                    self.logger.info(
                            _(u'''Found Movie "%s".''') %
                            (self.metadata['title']))
                    # Default to the first studio and category
                    if self.metadata.studios:
                        self.studio = self.metadata.studios[0]
                    if self.metadata.categories:
                        self.category = self.metadata.categories[0]
                except StopIteration:
                    pass
            #
            if not self.metadata and title:
                try:
                    self.metadata = self.tmdb.sortedSearch(title)
                    self.logger.info(
                            _(u'''Found Movie "%s".''') %
                            (self.metadata[0]['title']))
                except IndexError:
                    self.logger.info(
                            _(u'''Falling back to generic export.'''))
                    if not self.configuration['v024']:
                        self.metadata = self.recorded.exportMetadata()
                    return
                #
                if (len(self.metadata) > 1) & \
                        (self.metadata[0].levenshtein > 0):
                    self.logger.info(
                        _(u'''Falling back to generic export.'''))
                    if not self.configuration['v024']:
                        self.metadata = self.recorded.exportMetadata()
                else:
                    self.metadata = self.metadata[0]
                    # Default to the first studio and category
                    if self.metadata.studios:
                        self.studio = self.metadata.studios[0]
                    if self.metadata.categories:
                        self.category = self.metadata.categories[0]
        except self.MythError as errmsg:
            self.logger.info(
                _(u'''MythError, falling back to generic export.
Error %s''') % errmsg)
            if not self.configuration['v024']:
                self.metadata = self.recorded.exportMetadata()
        #
        return
#
    def _get_generic(self, ):
        ''' For v0.24 get generic EPG metadata
        return nothing
        '''
        self.metadata = {}
        self.studio = None
        self.category = None
        #
        self.vid.title = self.recorded.title
        if self.recorded.subtitle:
            self.vid.subtitle = self.recorded.subtitle
        if self.recorded.description:
            self.vid.plot = self.recorded.description
        if self.recorded.originalairdate:
            self.vid.year = self.recorded.originalairdate.year
            self.vid.releasedate = self.recorded.originalairdate
        self._get_new_duration()
        self.vid.length = self.new_runtime
        for member in self.recorded.cast:
            if member.role == 'director':
                self.vid.director = member.name
            elif member.role == 'actor':
                self.vid.cast.append(member.name)
        #
        ## If this is not v0.24 there may be season & episode numbers
        try:
            if self.recorded.episode:
                self.configuration['season_num'] = self.recorded.season
                self.configuration['episode_num'] = self.recorded.episode
            if self.recorded.inetref:
                self.configuration['inetref'] = self.recorded.inetref
        except Exception:
            pass
        #
        return
#
    def calc_dd_blocks(self, starttime):
        ''' Using the seek table find out the closest seek point
        into the file that matches the given starttime.
        return the number of bytes closest to the starttime
        '''
        #
        frame_offset = 0
        #
        if self.configuration['fps']:
            self.configuration['frame'] = \
                        int(starttime * self.configuration['fps'])
            #
            frame_offset = [seek.offset for seek in self.recorded.seek
                    if seek.type == 9 and seek.mark <=
                                    self.configuration['frame']][-1]
            #
            if frame_offset == None:
                self.logger.info(
_(u'''There was no offset found for frame %(frame)s, returning start block equal to zero.''')
% self.configuration)
        else:
            self.logger.info(
_(u'''There is not FPS value to calculate an offset, returning start block equal to zero.'''))
        #
        return frame_offset
#
    def get_all_recording_data(self,):
        '''Get all of a recording's DB data. This includes the recorded,
        recordedprogram, program, programres, recordedseek and
        recordedmarkup data.
        return a dictionary of arrays containing all relevant DB data
        '''
        recorded_data = {}
        for key in common.SQL_GET_OR_INSERT['insert_sql'].keys():
            recorded_data[key] = []
        #
        ## Get a MythTV data base cursor
        cursor = self.mythdb.cursor()
        #
        ## Get specific records for a recorded video
        for table in recorded_data.keys():
            # Get the list of fields in this table record
            if common.SQL_GET_OR_INSERT['insert_sql'][table].has_key('All'):
                version = 'All'
            elif self.OWN_VERSION[1] == 24:
                version = 24
            else:
                version = 25
            fields = common.SQL_GET_OR_INSERT['insert_sql'][ \
                                                table][version][0]
            #
            self.configuration['table'] = table
            #
            for key_starttime in ['SQL_starttime', 'SQL_progstart']:
                #
                self.configuration['SQL_start'] = \
                                self.configuration[key_starttime]
                sql_cmd = common.SQL_GET_OR_INSERT['get_sql'] % \
                                self.configuration
                cursor.execute(sql_cmd)
                records = cursor.fetchall()
                if len(records) > 0:
                    break
            #
            verbage = _(
u'''Read %d records from the %s table for chanid "%s" with starttime "%s".''') % \
                        (len(records), table,
                        self.configuration['chanid'],
                        self.configuration['SQL_starttime'])
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            #
            for record in records:
                rec_dict = {}
                count = 0
                for field in fields:
                    # Deal with quote characters in the text
                    if type(record[count]) == type(''):
                        rec_dict[field] = record[count].replace("'", "\\'")
                    elif type(record[count]) == type(u''):
                        rec_dict[field] = record[count].replace(u"'", u"\\'")
                    elif record[count] == None:
                        rec_dict[field] = 'NULL'
                    else:
                        rec_dict[field] = record[count]
                    count += 1
                recorded_data[table].append(rec_dict)
        #
        cursor.close()
        #
        return recorded_data
#
    def insert_all_recording_data(self, recorded_data):
        '''Insert all of a recording's DB data. This includes the recorded,
        recordedprogram, program, programres, recordedseek and
        recordedmarkup data.
        return nothing
        '''
        #
        # Adjust the various records to match the install environment
        recorded_data['recorded'][0]['hostname'] = self.localhostname
        recorded_data['recorded'][0]['storagegroup'] = u'Default'
        if self.configuration['base_name'].find('_LOSSLESS_BUG') != -1:
            verbage = _(
u'''Adjust the DB records as this is only a sample video file.''')
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            recorded_data['recorded'][0]['basename'] = \
                                    self.configuration['base_name']
            self.configuration['mkv_file'] = self.configuration['base_name']
            recorded_data['recorded'][0]['filesize'] = \
                            os.path.getsize(self.configuration['base_name'])
            #
            new_markuptable = []
            for markup_record in recorded_data['recordedmarkup']:
                if markup_record['type'] == 32:
                    fps_str = str(markup_record['data'])
                    self.configuration['fps'] = float(fps_str[:2] + '.' +
                                                        fps_str[2:])
                elif markup_record['type'] == 33:
                    # Duration in millseconds
                    markup_record['data'] = recorded_data[
                                            'video_duration'] * 1000
                # Skip any skip or cut frames as they are no longer
                # accurate
                if markup_record['type'] in [0, 1, 4, 5, 34]:
                    continue
                new_markuptable.append(markup_record)
            #
            recorded_data['recordedmarkup'] = new_markuptable
            #
            new_seektable = []
            for seekrecord in recorded_data['recordedseek']:
                if seekrecord['type'] == 9:
                    if seekrecord['mark'] == 0 and \
                                seekrecord['offset'] == 0:
                        new_seektable.append(seekrecord)
                        continue
                    #
                    # Set when the keyframe's timestamp
                    timestamp = seekrecord['mark'] / self.configuration['fps']
                    if recorded_data['sample_starttime'] == 0:
                        if timestamp > recorded_data['video_duration']:
                            continue
                        new_seektable.append(seekrecord)
                    elif timestamp < recorded_data['sample_starttime'] or \
                            timestamp > recorded_data['video_duration']:
                        previous_offset = seekrecord['offset']
                    else:
                        seekrecord['offset'] = \
                            seekrecord['offset'] - previous_offset
                        new_seektable.append(seekrecord)
                else:
                    new_seektable.append(seekrecord)
            recorded_data['recordedseek'] = new_seektable
        #
        ## Get a MythTV data base cursor
        cursor = self.mythdb.cursor()
        #
        ## Remove any old records that may already be in the db
        del_data = {
            'table': '',
            'chanid': recorded_data['recorded'][0]['chanid'],
        }
        #
        for table in common.SQL_GET_OR_INSERT['insert_sql'].keys():
            verbage = _(u'''Delete old records in the %s table.''') % table
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            del_data['table'] = table
            #
            del_data['SQL_start'] = recorded_data[
                                'recorded'][0]['starttime']
            if table in common.SQL_GET_OR_INSERT['progstart']:
                del_data['SQL_start'] = \
                                recorded_data['recorded'][0]['progstart']
            if len(recorded_data[table]):
                sql_cmd = common.SQL_GET_OR_INSERT['delete_sql'] % del_data
                try:
                    cursor.execute(sql_cmd)
                except Exception as errmsg:
                    verbage = _(u'''This SQL command caused an exception:
%s
Error: %s''') % (sql_cmd, errmsg)
                    self.logger.info(verbage)
                    self.stdout.write(verbage + u'\n')
        #
        ## Insert various records for a recorded video
        for table in common.SQL_GET_OR_INSERT['insert_sql'].keys():
            #
            verbage = _(u'''Inserting %d records in the %s table.''') % \
                        (len(recorded_data[table]), table)
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            # Get the list of fields in this table record
            if common.SQL_GET_OR_INSERT['insert_sql'][table].has_key('All'):
                version = 'All'
            elif self.OWN_VERSION[1] == 24:
                version = 24
            else:
                version = 25
            #
            self.configuration['table'] = table
            for record in recorded_data[table]:
                sql_cmd = common.SQL_GET_OR_INSERT['insert_sql'][ \
                                                table][version][1] % record
                try:
                    cursor.execute(sql_cmd)
                except Exception as errmsg:
                    # There are cases where failed inserts are OK like
                    # With duplicate program genre's
                    if table == 'program' or table == 'programgenres':
                        continue
                    verbage = (_(u'''This SQL command failed:
SQL command: "%s"
Error: "%s"''') % (sql_cmd, errmsg))
                    self.logger.info(verbage)
                    self.stdout.write(verbage + u'\n')
                    exit(int(common.JOBSTATUS().ABORTED))
        #
        cursor.close()
        #
        verbage = _(
u'''All DB records inserted.''')
        self.logger.info(verbage)
        self.stdout.write(verbage + u'\n')
        #
        return recorded_data
#
    def add_video_to_storage_group(self, db_record, videofile):
        ''' Copy a video file to a storage group.
        return nothing
        '''
        srcsize = os.path.getsize(videofile)
        #
        verbage = _(u"Copying %s") % (videofile) + \
               u" to myth://%s@%s/%s" % \
               (db_record.storagegroup, db_record.hostname,
                db_record.basename)
        self.logger.info(verbage)
        self.stdout.write(verbage + u'\n\n')
        srcfp = open(self.configuration['base_name'], 'r')
        dstfp = db_record.open('w')
        #
        tsize = 2**24
        while tsize == 2**24:
            tsize = min(tsize, srcsize - dstfp.tell())
            dstfp.write(srcfp.read(tsize))
        #
        srcfp.close()
        dstfp.close()
        #
        return
#
    def match_and_remove(self,):
        ''' Match the channel number and program title with the recording.
        If they match delete the recording and its recording record.
        return nothing
        '''
        #
        match_found = self.check_for_match()
        #
        if match_found:
            program = self.mythbeconn.getRecording(
                            chanid=self.recorded.chanid,
                            starttime=self.recorded.starttime)
            if program == None:
                verbage = (_(u'''
There is no Program record for the recording:
Title: "%s" on channel %s with start time "%s"
This recording cannot be deleted, aborting script''') %
(self.recorded.title, (u'%s' % self.recorded.chanid)[1:],
self.recorded.starttime))
                self.logger.info(verbage)
                self.stdout.write(verbage + u'\n')
                #
                ## Remove this recording's files from the
                ## working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
            #
            result = self.mythbeconn.deleteRecording(program, force=True)
            if result == u'-1':
                verbage = _(_(u'''
Successfully removing the recording:
Title: "%s" on channel %s with start time "%s"
''') %
(self.recorded.title, (u'%s' % self.recorded.chanid)[1:],
self.recorded.starttime))
                self.logger.info(verbage)
                self.stdout.write(verbage + u'\n')
            else:
                verbage = (_(u'''
Removing the recording failed:
Title: "%s" on channel %s with start time "%s", aborting script.
''') %
(self.recorded.title, (u'%s' % self.recorded.chanid)[1:],
self.recorded.starttime))
                self.logger.info(verbage)
                self.stdout.write(verbage + u'\n')
                #
                ## Remove this recording's files from the
                ## working directory
                cleanup_working_dir(self.configuration['workpath'],
                                    self.configuration['recorded_name'])
                exit(int(common.JOBSTATUS().ABORTED))
        #
        return
#
    def check_for_match(self, ):
        '''Check if the recorded file should be deleted.
        return True or False
        '''
        match_found = False
        if self.configuration['remove_recorded']:
            for match in self.configuration['remove_recorded']:
                if match[0] == True and match[1] == True:
                    match_found = True
                    break
                elif match[0] == False and filter(is_not_punct_char,
                        self.recorded.title.strip().lower()) == match[1]:
                    match_found = True
                    break
                elif match[1] == False and (
                            u'%s' % self.recorded.chanid)[1:] == match[0]:
                    match_found = True
                    break
                elif (u'%s' % self.recorded.chanid)[1:] == match[0] and \
                        filter(is_not_punct_char,
                            self.recorded.title.strip().lower()) == match[1]:
                    match_found = True
                    break
        #
        return match_found
#
    def update_jobqueue(self, status, comment):
        ''' Update the JobQueue status and add a comment.
        return nothing
        '''
        # The script may be running from the command line. In that
        # case there is no JobQueue entry to update, just return
        #
        ## Find the JobQueue record
        try:
            job = self.Job(self.configuration['jobid'])
        except self.MythError:
            verbage = _(u'''
No matching userjob for JobID "%s" was found therefore the comment
and status was not updated, aborting the script.
''') % self.configuration['jobid']
            self.logger.info(verbage)
            self.stdout.write(verbage + u'\n')
            #
            ## Remove this recording's files from the
            ## working directory
            cleanup_working_dir(self.configuration['workpath'],
                                self.configuration['recorded_name'])
            exit(int(common.JOBSTATUS().ABORTED))
        #
        # Update the userjob's comment and status
        job.setComment(comment)
        job.setStatus(status)
        #
        return
