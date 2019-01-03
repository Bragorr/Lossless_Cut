#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ----------------------
"""
# Name: ll_report.py
#
# Python Script
# Author:   R.D. Vaughan
# Purpose: Create various reports for lossless.py including
#          bug and success reports. Also for bug reports
#          optionally create a 25Mg example video file
#          from the recording that has issues.
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
import tarfile
from pickle import dump
from glob import glob
from optparse import OptionParser
from datetime import datetime

## Mythtv loss less cut specific imports
import importcode.common as common
from importcode.utilities import create_cachedir, create_logger, \
        check_dependancies, set_language, get_config, \
        display_recorded_info, commandline_call, get_mediainfo, \
        create_config_file
from importcode.mythtvinterface import Mythtvinterface
#
try:
    from lxml import etree as etree
except Exception, errmsg:
    sys.stderr.write(u'''
Importing the "lxml" python libraries failed on
Error: %s\n''' % errmsg)
    sys.exit(1)
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
    sys.exit(1)
#
## Initialize local variables
__title__ = u"ll_report"
__author__ = common.__author__
#
__version__ = "0.1.4"
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Fixed identification of the MythTV version being used
# 0.1.3 Added columns for the recording device manufacturer
#       and model
# 0.1.4 Added the new config file sections
#
# Language translation specific to this desktop
_ = set_language()
#
__purpose__ = _('''
Create various reports for lossless.py including bug, success reports.
Also for bug reports optionally create a 25Mg example video file
from the recording that has issues.
''')
#
## Local variables
## Help text
MANDITORY = _(
'''Mandatory command line parameter:
  -f "/path/filename.mpg"       MythTV recorded video path and file name

''')
#
USAGE_TEXT = _('''
This script creates various reports for lossless.py including bug,
success reports. Also for bug reports optionally create a 25Mg example
video file from the recording that has issues.

%s

Optional command line parameters:
  Most of these parameters can be set in the automatically
  generated "~/.mythtv/lossless_cut.cfg" configuration file.

  -h or -u     Display this help/usage text
  -A           Add the entier recorded file to the bug report archive. This
               option is only valid when accompanied by the -B option.
  -b           Display a bug report WITHOUT to the console and create
               a text file containing the same information named:
               "/current directory/base_video_file_name_LOSSLESS_BUG.txt"
  -B           Create a bug report as with option "-b" but also create a
               sample file of the first 25Mg of the video file. In the current
               directory add both the sample video file, log if it exists and
               bug report to an archive file:
               "/current directory/base_video_file_name_LOSSLESS_BUG.tar.bz2"
  -s HH:MM:SS  Sample start time. This option must be used with the -B option.
               The 25Mg video sample will start at the time specified.
  -t           Perform a test of the environment, display
               success or failure and exit
  -w           Display a Wiki page table entry that can be used to identify
               recording device's whose recorded videos either work or fail
               with lossless_cut.py

This script requires the following to be installed and accessible:
  1) This script is included with the "lossless_cut" utility which needs to be
     installed on a MythTV backend
  2) A properly configured: config.xml or mysql.txt file.

''') % (MANDITORY)
#
MANDITORY = (MANDITORY + "%s") % u''
#
## Command line options and arguments
PARSER = OptionParser(
        usage=u"%prog usage: ll_report.py -fhubBAstw [parameters]\n")
PARSER.add_option(  "-f", "--recordedfile", metavar="recordedfile",
                    default="", dest="recordedfile",
                    help=_(
u'The absolute path and file name of the MythTV recording.'))
PARSER.add_option(  "-b", "--bugtext", action="store_true",
                    default=False, dest="bugtext",
                    help=_(
u'''Create a text bug report file:
    "/current directory/videoname_LOSSLESS_BUG.txt"'''))
PARSER.add_option(  "-A", "--all", action="store_true",
                    default=False, dest="all",
                    help=_(
u'''Copy the whole recorded video to the bug report archive.
This option overrides the 25Mg limitation and should only be used
by the developer for problem analysis. The files would be far to
large for being uploaded by users and likely violate copyright laws.'''))
PARSER.add_option(  "-B", "--bugarchive", action="store_true",
                    default=False, dest="bugarchive",
                    help=_(
u'''Create a text bug report and 25Mg sample video file:
    "/current directory/videoname_LOSSLESS_BUG.tar.bz2"'''))
PARSER.add_option(  "-s", "--starttime", metavar="recordedfile",
                    default="", dest="starttime",
                    help=_(
u'Video file sample start time in HH:MM:SS format.'))
PARSER.add_option(  "-t", "--test", action="store_true",
                    default=False, dest="test",
                    help=_(
u"Test that the environment meets all the scripts dependencies."))
PARSER.add_option(  "-u", "--usage", action="store_true",
                    default=False, dest="usage",
                    help=_(u"Display this help/usage text and exit."))
PARSER.add_option(  "-v", "--version", action="store_true",
                    default=False, dest="version",
                    help=_(u"Display version and author information"))
PARSER.add_option(  "-w", "--wiki", action="store_true",
                    default=False, dest="wiki",
                    help=_(
u'''Display a Wiki page table entry that can be used to identify recording
device's whose recorded videos either work or fail with lossless_cut.py'''))
#
OPTS, ARGS = PARSER.parse_args()
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
        if isinstance(obj, unicode):
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
sys.stdout = OutStreamEncoder(sys.stdout, 'utf8')
sys.stderr = OutStreamEncoder(sys.stderr, 'utf8')
#
#
class Losslessreport(object):
    """Creates reports and archives video examples for a MythTV
    recorded video file.
    """

    def __init__(self,
                opts,   # Command line options
                ):
        #
        try:
            self.configuration = get_config(opts, ll_report=True)
        except Exception, errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
_(u'''Processing the configuration file failed. Error(%s)\n''')
                    % errmsg)
            sys.exit(1)
        #
        self.configuration['version'] = __version__
        #
        self.logger = create_logger(
                self.configuration['logfile'], filename=True)
        #
        try:
            self.mythtvinterface = Mythtvinterface(self.logger,
                                                    self.configuration)
        except Exception, errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'''Acquiring access to MythTV failed, aborting script.
Error(%s)\n''')
                    % errmsg)
            sys.exit(1)
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
        #
        # Set the subtitle extraction utilities based on the system
        # architecture
        self.configuration['ccextractor'] = bit_arch % (
                common.APPDIR, common.CCEXTRACTOR)
        #
        try:
            self.configuration['mythutil'] = check_dependancies(
                    self.configuration)
        except Exception, errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
                _(u'''
One or more script dependencies could not be satisfied, aborting script.
Error(%s)\n''')
                    % errmsg)
            sys.exit(1)
        #
        self.mythtvinterface.stdout = sys.stdout
        self.mythtvinterface.stderr = sys.stderr
        #
        ## Xpath filters used to parse mediainfo XML output
        # Find specific track types
        self.tracks_filter = \
                etree.XPath(common.TRACKS_XPATH)
        self.element_filter = \
                etree.XPath(common.ELEMENTS_XPATH)
        #
        self.processing_started = datetime.now()
        self.filename = u''
        self.subtitles = u''
        # end __init__()
#
    def ll_report(self):
        '''
        1) Check if display options was selected.
        2) Test the environment and the script dependencies
           was selected.
        3) Process the MythTV recording
        return nothing
        '''
        if self.configuration['test']:
            self._display_variables(summary=True)
            sys.stdout.write(
_(u'''Congratulations! All script dependencies have been satisfied.
You are ready to create bugs or success reports for lossless_cut.py

'''))
            sys.exit(0)
        #
        # Check that at least one report type was selected
        if not self.configuration['bugtext'] and \
                not self.configuration['bugarchive'] and \
                not self.configuration['wiki']:
            sys.stdout.write(USAGE_TEXT)
            sys.stderr.write(
_(u'''You must specify at least one report type (-b, -B, -w) on the command line!\n'''))
            sys.exit(1)
        #
        # Get the xml track info using mediainfo
        self.configuration['trackinfo'] = get_mediainfo(
                        self.configuration['recordedfile'],
                        self.element_filter, self.tracks_filter,
                        etree, self.logger, sys)
        #
        ## Get this recordings metadata and other data from the MyhTV DB
        self.mythtvinterface.get_recorded_data()
        #
        self.subtitles = False
        self._display_variables()
        #
        if self.configuration['bugtext']:
            self.bug_report()
        #
        if self.configuration['bugarchive']:
            self.bug_archive()
        #
        if self.configuration['wiki']:
            self.wiki_table_row()
        #
        self._cleanup()
        #
        return
#
    def bug_report(self, create_only=False):
        ''' Create a bug report and display to the STDOUT and a
        text file.
        return nothing
        '''
        #
        verbage = '''Bug report for "lossless_cut.py":
  Recorded file: "%(recordedfile)s"
''' % self.configuration
        #
        # System details
        verbage += '''
Installation details:

%(system_info)s
MythTV version:             %(mythtv_version)s
mkvmerge version:           %(mkvmerge_version)s
mediainfo version:          %(mediainfo_version)s
ll_report version:          %(version)s
''' % self.configuration
        verbage += display_recorded_info(self.configuration, logger=False)
        #
        sys.stdout.write(verbage + u'\n')
        #
        self.filename = u"%(recorded_name)s_LOSSLESS_BUG.txt" % self.configuration
        fileh = open(self.filename, 'w')
        fileh.write(verbage)
        fileh.close()
        #
        if not create_only:
            sys.stdout.write(
                (_('''Bug report file "%s" created.
You can copy and paste this report onto "http://mythtv.pastebin.com/", then post the URL
on the MythTV mailing list with an explanation of the issues.''') % self.filename)
                + u'\n\n')
        #
        return
#
    def bug_archive(self, ):
        ''' Create a bug report and display to the STDOUT and a
        text file. Create a 25Mg copy of the MythTV recording.
        Create an tar.gz file containing the bug test and 25Mg
        example video file. Delete the temporary files and display
        the tar.gz file name.
        return nothing
        '''
        self.bug_report(create_only=True)
        #
        if not self.configuration['all']:
            # Create the 25Mg sample video file
            self.configuration['bug_sample'] = \
u"%(recorded_name)s_LOSSLESS_BUG.%(recorded_ext)s" % self.configuration
            self.configuration['sample_startblock'] = 0
            if self.configuration['sample_starttime']:
                self.configuration['sample_startblock'] = \
                    self.mythtvinterface.calc_dd_blocks(
                                    self.configuration['sample_starttime'])
            arguments = common.VIDEO_SAMPLE_FILE_CMD % self.configuration
            verbage = _(
u'''Creating a 25Mg video sample file with the command below, please wait ...
dd %s
'''  % arguments)
            self.logger.info(verbage)
            sys.stdout.write(verbage + u'\n')
            #
            result = commandline_call(u'dd', arguments)
            if not result[0]:
                if result[1].find('25 MB') == -1:
                    # TRANSLATORS: Please leave %s as it is,
                    # because it is needed by the program.
                    # Thank you for contributing to this project.
                    verbage = \
        _(u'''dd could not make the sample video file, aborting script.
Error: %s''') % (result[1])
                    self.logger.critical(verbage)
                    sys.stderr.write(verbage + u'\n')
                    exit(1)
        #
        # Get the relevant database records
        verbage = _(
u'''Getting the relevant database records for this recording, please wait ...
''')
        self.logger.info(verbage)
        sys.stdout.write(verbage + u'\n')
        pickle_filename = \
                u"%(recorded_name)s_LOSSLESS_BUG.pickle" % self.configuration
        records = self.mythtvinterface.get_all_recording_data()
        # Add the exact filename and path to the archive
        if self.configuration['all']:
            records['video_filename'] = self.configuration['recordedfile']
        else:
            records['video_filename'] = self.configuration['bug_sample']
        #
        # Get the xml track info using mediainfo
        trackinfo = get_mediainfo(
                    records['video_filename'],
                    self.element_filter, self.tracks_filter,
                    etree, self.logger, sys)
        # Add sample starttime information
        records['sample_starttime'] = 0
        records['sample_startblock'] = 0
        if self.configuration['sample_starttime']:
            records['sample_starttime'] = \
                        self.configuration['sample_starttime']
            records['sample_startblock'] = \
                        self.configuration['sample_startblock']
        records['video_duration'] = trackinfo['video_duration']
        dump(records, open(pickle_filename, "wb" ))
        #
        # Create the tar.gz file containing the bug sample video,
        # text report and database records pickle file
        verbage = _(
u'''Creating the bug report archive file, please wait ...
''')
        self.logger.info(verbage)
        sys.stdout.write(verbage + u'\n')
        files_to_tar = glob(u'%(recorded_name)s_LOSSLESS_BUG.*' %
                        self.configuration)
        #
        # If there is a log file then include it in the archive
        logfile = os.path.join(self.configuration['logpath'],
                            self.configuration['recorded_name'] + u'.log')
        if os.path.isfile(logfile):
            files_to_tar.append(logfile)
        else:
            sys.stderr.write('''There is no associated log file "%s"
to add to the bug report archive.''' % logfile + u'\n\n')
        #
        # If the -A option was selcted then copy the whole
        # recorded video file to the archive.
        if self.configuration['all']:
            files_to_tar.append(self.configuration['recordedfile'])
            sys.stderr.write(_(
u'''The whole recorded video file will be add to the bug report archive:
"%s"
This will take several minutes, please wait ...''') %
            self.configuration['recordedfile'] + u'\n\n')
        #
        tar_filename = u'%(recorded_name)s_LOSSLESS_BUG.tar.bz2' % \
                        self.configuration
        tar = tarfile.open(tar_filename, 'w:bz2')
        for filename in files_to_tar:
            dummy, base_filename = os.path.split(filename)
            tar.add(filename, arcname=base_filename)
        tar.close()
        #
        # Remove the bug sample video, db pickle and text report
        os.remove(self.filename)
        os.remove(pickle_filename)
        if not self.configuration['all']:
            os.remove(self.configuration['bug_sample'])
        #
        sys.stdout.write((_(
u'''Bug report file "%s" created.
You can upload archive file to a file site such as mediafire.com, then post
the download URL on the MythTV mailing list with an explanation of the issues.
''') % tar_filename)
            + u'\n')
        #
        return
#
    def wiki_table_row(self, ):
        ''' Display text that can be cut and paste into the wiki
        table for devices whose recorded video files can be successfully
        loss less cut or fails to work with the lossless_cut.py script
        return nothing
        '''
        #
        encodes = {}
        for key in common.TRACK_DISPLAY_ORDER:
            encodes[key] = u''
        #
        ## Build track by track details
        #
        for track_type in common.TRACK_DISPLAY_ORDER:
            if self.configuration['trackinfo']['total_%s' % track_type] == 0:
                continue
            #
            encodes[track_type] = u''
            for detail_dict in self.configuration['trackinfo'][
                                            '%s_details' % track_type]:
                track_details = u''
                for key in common.WIKI_TRACK_ELEM_DICT[track_type]:
                    if not detail_dict[key]:
                        continue
                    if track_details:
                        track_details += u' '
                    if key == u"Codec_ID":
                        track_details += _(u'''codec-%s''') % (
                                                    detail_dict[key])
                    else:
                        track_details += _(u'''%s''') % (detail_dict[key])
                #
                if encodes[track_type].find(track_details.strip()) != -1:
                    continue
                if encodes[track_type]:
                    encodes[track_type] += u', '
                encodes[track_type] += track_details.strip()
        #
        wiki_table_row = common.WIKI_FIRST_COLUMN
        wiki_table_row += common.WIKI_MANUFACTURER_COLUMN
        wiki_table_row += common.WIKI_MODEL_COLUMN
        wiki_table_row += common.WIKI_ROW % (self.configuration)
        for track_type in common.TRACK_DISPLAY_ORDER:
            wiki_table_row += common.WIKI_TABLE_COLUMN % encodes[track_type]
        #
        if self.configuration['bugtext'] or self.configuration['bugarchive']:
            verbage = _(u'''At: %s
Please replace "Manufacturer Name" and "Device Model" with your specific info,
then update the Loss Less Cut wiki's Unsupported device table by cutting and
pasting the following text lines as a table row:
%s''') % (common.WIKI_UNSUPPORTED_DEVICE_TABLE_URL, wiki_table_row)
        else:
            verbage = _(u'''At: %s
Please replace "Manufacturer Name" and "Device Model" with your specific info,
then update the Loss Less Cut wiki's Supported device table by cutting and
pasting the following text lines as a table row:
%s''') % (common.WIKI_SUPPORTED_DEVICE_TABLE_URL, wiki_table_row)
        #
        sys.stdout.write(verbage + u'\n\n')
        #
        return
#
    def _cleanup(self,):
        '''
        Remove the log file if the flag to delete is True
        return nothing
        '''
        #
        self.logger.info(
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
_(u'''End of report creation for "%s" at: %s'''
) % (self.configuration['recordedfile'],
            datetime.now().strftime(common.LL_START_END_FORMAT)))
        #
        ## Remove the recorded video's log file if the delete flag is True
        if self.configuration['keep_log']:
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

  ll_report version:            %(version)s

  MythTV recorded source video: "%(recordedfile)s"

  The Log file location:        "%(logpath)s"
  The Log file:                 "%(logfile)s"

  Keep the log file:            "%(keep_log)s"

\n''') % self.configuration
        #
        if summary:
            sys.stdout.write(verbage)
        else:
            self.logger.info(verbage)
        #
        return
#
#
if __name__ == "__main__":
    # Check for the help or usage option then exit
    if OPTS.usage:
        sys.stdout.write(USAGE_TEXT)
        exit(0)
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
        exit(0)
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
        sys.exit(0)
    #
    # Check if a "~/.mythtv/lossless_cut.cfg" file exists.
    # If it does not exist then create an initial one
    # in the "~/.mythtv" directory.
    if not os.path.isfile(common.CONFIG_FILE):
        try:
            if not os.path.isdir(common.CONFIG_DIR):
                create_cachedir(common.CONFIG_DIR)
        except Exception, errmsg:
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
            sys.stderr.write(_(u'''Could not create the directory "%s" to
copy the file "%s" to "%s", aborting script.
''') % (common.CONFIG_DIR, common.INIT_CONFIG_FILE, common.CONFIG_FILE))
            exit(1)
        #
        # Initialize the new configuration with default values file
        try:
            create_config_file()
        except IOError, errmsg:
            sys.stderr.write(errmsg)
            exit(1)
    #
    # Initialize the loss less cut class
    LL_REPORT = Losslessreport(OPTS)
    #
    # Process the recorded video file according to the command line
    # options and the configuration file settings.
    LL_REPORT.ll_report()
    #
    sys.exit(0)
