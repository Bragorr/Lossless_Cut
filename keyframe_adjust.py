#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ----------------------
"""
# Name: keyframe_adjust.py   Adjusts commercial cut and skip list
#                            frame numbers to their closest keyframe
#                            equivalent.
#
# Python Script
# Author:   R.D. Vaughan
# Purpose:  This python script adjusts commercial cut and skip list
#           frame numbers to their closest keyframe equivalent.
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
from optparse import OptionParser
from datetime import datetime

## Mythtv loss less cut specific imports
import importcode.common as common
from importcode.utilities import create_cachedir, create_logger, \
        check_dependancies, set_language, get_config, \
        create_config_file, get_mediainfo
from importcode.mythtvinterface import Mythtvinterface
#
try:
    from lxml import etree as etree
except Exception, errmsg:
    sys.stderr.write(u'''
Importing the "lxml" python libraries failed on
Error: %s\n''' % errmsg)
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
__title__ = u"keyframe_adjust.py"
__author__ = common.__author__
#
__version__ = "0.1.4"
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Added the new config file sections
# 0.1.3 Changed automatic cut list generation to be an optional
#       command line switch
# 0.1.4 Added lxml import and call for track info due to changes
#       in the way fps, width and height info is gathered.
#
# Language translation specific to this desktop
_ = set_language()
#
__purpose__ = _('''
This python script adjusts commercial cut and skip list frame numbers
to their closest keyframe equivalent. This script is generally used
as a MythTV user job run right after a recording is commercial flagged.
''')
#
## Local variables
## Help text
MANDITORY = _(
'''Mandatory command line parameter:
  -f "/path/filename.mpg"       MythTV recorded video path and file name

  When this script is used as a MythTV user job always specify the
  file as: "%%DIR%%/%%FILE%%"
''')
#
USAGE_TEXT = _('''
This script adjust a MythTV skip and cut list to their closest keyframe values
as specified in the seek table. This makes manual video editing less onerous.

If a cutlist or skiplist has not been created then the job exits without
changing anything.

MythTV Userjob example: (modify the path to the script so that it matches
your installation)

  /path to/script file/keyframe_adjust.py -f "%%DIR%%/%%FILE%%"

%s
Optional command line parameters:
  Most of these parameters can be set in the automatically
  generated "~/.mythtv/lossless_cut.cfg" configuration file.

  -h or -u                      Display this help/usage text
  -g                            Generate a cut list if one does not exist
                                but there is skip list
  -l "/log directory path"      Specify a directory path to save the jobs
                                log file
  -k                            Keep the log file after the userjob
                                has completed successfully
  -s                            Display a summary of the options that would
                                be used during processing
                                but exit before processing begins. Used this
                                option for debugging. No changes to the mpg
                                file occurs.
  -t                            Perform a test of the environment, display
                                success or failure and exit
  -v                            Display script's version, author's name and
                                purpose.

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
        usage=u"%prog usage: keyframe_adjust.py -fghuklstv [parameters]\n")
PARSER.add_option(  "-f", "--recordedfile", metavar="recordedfile",
                    default="", dest="recordedfile",
                    help=_(
u'The absolute path and file name of the MythTV recording.'))
PARSER.add_option(  "-g", "--gencutlist", action="store_true",
                    default=False, dest="gencutlist",
                    help=_(
u"Generate a cut list if one does not exist but there is a skip list."))
PARSER.add_option(  "-k", "--keeplog", action="store_true",
                    default=False, dest="keeplog",
                    help=_(
u"Keep the log file after the userjob has completed successfully."))
PARSER.add_option(  "-l", "--logpath", metavar="logpath",
                    default="", dest="logpath",
                    help=_(
u'Specify a directory path to save the jobs log file'))
PARSER.add_option(  "-s", "--summary", action="store_true",
                    default=False, dest="summary",
                    help=_(
u'''Display a summary of the options that would be used during processing
but exit before processing begins. Used this for debugging. No changes
to the mpg file occur.'''))
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
class Keyframeadjust(object):
    """Perform keyframe adjustment to a skip or cut list for a
    MythTV recorded video file
    """

    def __init__(self,
                opts,   # Command line options
                ):
        #
        self.jobstatus = common.JOBSTATUS()
        self.return_code = int(self.jobstatus.UNKNOWN)
        #
        try:
            self.configuration = get_config(opts, keyframe_adjust=True)
        except Exception, errmsg:
            sys.stderr.write(
                # TRANSLATORS: Please leave %s as it is,
                # because it is needed by the program.
                # Thank you for contributing to this project.
_(u'''Processing the configuration file failed. Error(%s)\n''')
                    % errmsg)
            sys.exit(int(self.jobstatus.ABORTED))
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
            sys.exit(int(self.jobstatus.ABORTED))
        #
        ## Set if mythtv v0.24 is installed
        if self.mythtvinterface.OWN_VERSION[1] == 24:
            self.v024 = True
        else:
            self.v024 = False
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
            sys.exit(int(self.jobstatus.ABORTED))
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
        ## Check if the user wants to automatically generate a cut list when
        ## it is empty but there is a skip list
        self.configuration['gencutlist'] = False
        if opts.gencutlist:
            self.configuration['gencutlist'] = True
        #
        self.processing_started = datetime.now()
        # end __init__()
#
    def adjust_frame_numbers(self):
        '''
        1) Check if display options was selected.
        2) Test the environment and the script dependencies
           was selected.
        3) Process the MythTV recording
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
You are ready to adjust the skip and/or cut list frame numbers to keyframes
on a MythTV recordings.

'''))
            sys.exit(int(self.jobstatus.UNKNOWN))
        #
        self.logger.info(
            # TRANSLATORS: Please leave %s as it is,
            # because it is needed by the program.
            # Thank you for contributing to this project.
_(u'''Start skip and/or cut list frame number adjustments for "%s" at: %s'''
) % (self.configuration['recordedfile'],
            self.processing_started.strftime(common.LL_START_END_FORMAT)))
        #
        self._display_variables()
        #
        # Get the xml track info using mediainfo
        self.configuration['trackinfo'] = get_mediainfo(
                        self.configuration['recordedfile'],
                        self.element_filter, self.tracks_filter,
                        etree, self.logger, sys)
        #
        self.mythtvinterface.adjust_frame_numbers()
        #
        self._cleanup()
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
_(u'''End of skip and/or cut list frame number adjustments for "%s" at: %s'''
) % (self.configuration['recordedfile'],
            datetime.now().strftime(common.LL_START_END_FORMAT)))
        #
        ## Remove the recorded video's log file if the delete flag is True
        if not self.configuration['keep_log']:
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

    Keyframe Adjust version:    %(version)s

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
        except Exception, errmsg:
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
        except IOError, errmsg:
            sys.stderr.write(errmsg)
            exit(int(common.JOBSTATUS().ABORTED))
    #
    # Initialize the loss less cut class
    KEYFRAME_ADJUST = Keyframeadjust(OPTS)
    #
    # Process the recorded video file according to the command line
    # options and the configuration file settings.
    KEYFRAME_ADJUST.adjust_frame_numbers()
    #
    sys.exit(KEYFRAME_ADJUST.return_code)
