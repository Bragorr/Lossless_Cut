#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ----------------------
"""
# Name: load_db.py
#
# Python Script
# Author:   R.D. Vaughan
# Purpose: Load a bug report pickle records to the MythTV database.
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
from pickle import load
from optparse import OptionParser
from datetime import datetime

## Mythtv loss less cut specific imports
import common as common
from utilities import create_cachedir, create_logger, \
        check_dependancies, set_language, get_config, \
        create_config_file
from mythtvinterface import Mythtvinterface
#
## Initialize local variables
__title__ = u"load_db"
__author__ = common.__author__
#
__version__ = "0.1.3"
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Fixed tabbing on command line option help
# 0.1.3 Added the new config file sections
#
# Language translation specific to this desktop
_ = set_language()
#
__purpose__ = _('''
Load the database with records captured in a bug report archive and
copy the sample video file into the recording storage group.
''')
#
## Local variables
## Help text
MANDITORY = _(
'''Mandatory command line parameter:
  -f "/path/filename.tar.bz2"   MythTV bug archive path and file name

''')
#
USAGE_TEXT = _('''
This script extracts from the bug report archive the sample video and
database records pickle. Move the sample to the Default directory then
insert the records into the database.

%s

Optional command line parameters:
  Most of these parameters can be set in the automatically
  generated "~/.mythtv/lossless_cut.cfg" configuration file.

  -h or -u     Display this help/usage text
  -k           Keep the log file after the userjob
               has completed successfully
  -t           Perform a test of the environment, display
               success or failure and exit

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
        usage=u"%prog usage: load_and_insert.py -fhut [parameters]\n")
PARSER.add_option(  "-f", "--archivefile", metavar="archivefile",
                    default="", dest="archivefile",
                    help=_(
u'The absolute path and file name of the MythTV recording.'))
PARSER.add_option(  "-k", "--keeplog", action="store_true",
                    default=False, dest="keeplog",
                    help=_(
u"Keep the log file after the script has completed successfully."))
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
class Loadbugarchive(object):
    """Install the sample video file and insert the database
    records from the bude report archive.
    """

    def __init__(self,
                opts,   # Command line options
                ):
        #
        try:
            self.configuration = get_config(opts, load_db=True)
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
            self.v024 = True
        else:
            self.v024 = False
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
        self.processing_started = datetime.now()
        self.filename = u''
        self.subtitles = u''
        self.configuration['verbose'] = True
        # end __init__()
#
    def load_and_insert(self):
        '''
        1) Test the environment and the script dependencies
           was selected.
        3) Process the MythTV bug report archive
        return nothing
        '''
        if self.configuration['test']:
            self._display_variables(summary=True)
            sys.stdout.write(
_(u'''Congratulations! All script dependencies have been satisfied.
You are ready to install the sample video file and insert the db records.
'''))
            sys.exit(0)
        #
        self._extract_install()
        #
        self._cleanup()
        #
        return
#
    def _extract_install(self, ):
        ''' Extract the sample video file to the default
        directory. Extract the database records pickle then
        insert those records in the MythTV database.
        return nothing
        '''
        #
        # Open the archive file
        sys.stdout.write(_(
u'''Open the archive file "%s".
''') % self.configuration['archivefile'] + u'\n')
        tar = tarfile.open(self.configuration['archivefile'], 'r:bz2')
        members = tar.getmembers()
        #
        # Extract the database Pickle file and the sample video
        for member in members:
            if member.name.endswith(u'pickle'):
                dummy, pickle_filename = os.path.split(member.name)
                tar.extract(member, path="")
                sys.stdout.write(_(
u'''Extract the database pickle file "%s".
''') % member.name + u'\n')
                break
        #
        # Load the pickle file
        sys.stdout.write(_(
u'''Open the DB pickle file "%s".
''') % pickle_filename + u'\n')
        records = load(open(pickle_filename, "rb" ))
        dummy, self.configuration['base_name'] = os.path.split(
                                            records['video_filename'])
        # Extract the recorded video file or the sample
        for member in members:
            if member.name == self.configuration['base_name']:
                tar.extract(member, path="")
                sys.stdout.write(_(
u'''Extract the video file "%s".
''') % member.name + u'\n')
                break
        #
        # Insert the database records from the pickle file
        sys.stdout.write(_(u'''Insert the database records.
''') + u'\n')
        self.mythtvinterface.insert_all_recording_data(records)
        #
        # Install the whole or sample video file into the Default
        # storage group
        sys.stdout.write(_(
u'''Install the video file "%s".
''') % self.configuration['base_name'] + u'\n')
        db_record = list(self.mythtvinterface.mythdb.searchRecorded(
                        basename=self.configuration['base_name']))[0]
        self.mythtvinterface.add_video_to_storage_group(
                    db_record, self.configuration['base_name'])
        # Close the archive file
        # Remove the bug sample video and db pickle
        tar.close()
        os.remove(pickle_filename)
        os.remove(self.configuration['base_name'])
        #
        sys.stdout.write(_(
u'''Bug sample video file and records inserted.
''') + u'\n\n')
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
_(u'''End of install archive data for "%s" at: %s'''
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

  load_db version:              %(version)s

  Bug Report Archive file:      "%(archivefile)s"

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
    if OPTS.archivefile:
        if OPTS.archivefile[0] == '~':
            if OPTS.archivefile[1] == '/':
                OPTS.archivefile = os.path.join(os.path.expanduser("~"),
                                                OPTS.archivefile[2:])
            else:
                OPTS.archivefile = os.path.join(os.path.expanduser("~"),
                                                OPTS.archivefile[1:])
    if not os.path.isfile(OPTS.archivefile):
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        sys.stderr.write(_(u"The archive file (%s) does not exist.\n%s\n"
                            ) % (OPTS.archivefile, MANDITORY))
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
    LOAD_BUG_ARCHIVE = Loadbugarchive(OPTS)
    #
    # Process the recorded video file according to the command line
    # options and the configuration file settings.
    LOAD_BUG_ARCHIVE.load_and_insert()
    #
    sys.exit(0)
