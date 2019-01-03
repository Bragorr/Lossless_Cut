#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ----------------------
# Name: utilities.py   Provides various utility functions globally
#                      used by lossless_cut
# Python Script
# Author:   R.D. Vaughan
# Purpose:  This python script supports the lossless_cut.py Unity/Gnome3
#           indicator. Providing all Recording metadata information
#           and MythTV general data.
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
__version__ = '0.1.6'
# Version change log:
# 0.1.0 Initial development
# 0.1.1 Alpha release
# 0.1.2 Added display of output when dependancy tests
#       fail.
# 0.1.3 Fixed a bug where the removal of the old recording
#       option "delete_old" was being ignore when the the
#       replace "-r" option was used.
# 0.1.4 Fixed a bug where the cfg setting "keep_log" was ignored
#       Added a method to create ffmpeg/avconv compatible startime
#       and duration strings for lossless cuts
#       Added support for OPTS.forcemythxxextractor
#       Added support for OPTS.concertcuts
#       Added support for OPTS.tracknumber
#       Added support for OPTS.delayvideo
#       Added support for the two new config file sections
#       Added calculation for subtitle delay verus video track
# 0.1.5 Added a new configuration file section called
#       "mkvmerge_user_settings". This section allows a user to
#       customize the command line for either/or the mkvmerge cut or
#       merge processing. This is an "use at your own risk" set of
#       variables.
#       Added a common routine to create a lossless_cut.cfg file
#       Changed the java runtime dependancy error message to
#       display properly
#       Fixed a bug where the bug report sample starttime was not properly
#       converting hours into seconds
# 0.1.6 Handle abort when mediainfo cannot find a video's duration. The issue
#       is likely caused by a corrupt recording.
#
#
## Common function imports
import os
import ConfigParser
import subprocess
import locale
import logging
import string
from glob import glob
from datetime import datetime, timedelta
# Used for multilanguage support
import gettext
#
# Indicator specific imports
import common
#
## Local variables
_ = gettext.gettext
__author__ = common.__author__
__title__ = \
    _(u"""utilities.py - Provides various utility functions globally
used by lossless_cut""")
__purpose__ = _(u"""
This python script supports the lossless_cut loss less recording
editor various utility functions.
""")
#
# Used for for program title matching
def is_punct_char(char):
    '''check if char is punctuation char
    return True if char is punctuation
    return False if char is not punctuation
    '''
    return char in string.punctuation

def is_not_punct_char(char):
    '''check if char is not punctuation char
    return True if char is not punctuation
    return False if chaar is punctuation
    '''
    return not is_punct_char(char)
#
def get_filename_parts(filename):
    """Get the file name parts path, name and extension.
    return the file name components less the extension separator character
    """
    (dir_name, file_name) = os.path.split(filename)
    (file_base_name, file_extension) = os.path.splitext(file_name)
    return (dir_name, file_base_name, file_extension[1:])
# end getExtention

def set_language():
    """ Use the locale information to get the correct translation file
    that use used for all text labels.
    return the localized translation of message,
           based on the current global domain, language, and locale directory
    """
    locale.setlocale(locale.LC_ALL, '')
    gettext.bindtextdomain(common.APP, common.LANGDIR)
    gettext.textdomain(common.APP)
    return (gettext.gettext)
# end set_language()

def create_logger(log_file, log_name=u"lossless_cut", filename=False):
    """ Create a logger.
    return the logger object
    """
    # Create logger
    logger = logging.getLogger(log_name)
    # Create handler and set level to debug
    if filename:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler()
    # Create formatter
    formatter = logging.Formatter(\
        u"%(asctime)s - %(levelname)s - %(message)s")

    # Add formatter to handler
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger # end create_logger()

def exec_commandline(command):
    """Execute a command line and read the STDIO and STDERR results.
    return None if the command line failed
    return array of the stdout and stderr results
    """
    results = [u'', u'']

    try:
        process = subprocess.Popen(command, shell=True,
                bufsize=4096, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
    except Exception:
        return False

    # Get output from command line call
    try:
        results[0] = unicode(process.stdout.read(), u"utf-8")
    except (UnicodeEncodeError, TypeError):
        pass

    # Get error output from command line call (if any)
    try:
        results[1] = unicode(process.stderr.read(), u"utf-8")
    except (UnicodeEncodeError, TypeError):
        pass

    return results
 # end exec_commandline()

def create_cachedir(full_path):
    """ Check if a directory exists and create it if
    it does not exist.
    return nothing
    """
    if full_path[0] == '~':
        full_path = os.path.expanduser(u"~") + full_path[1:]
    if not os.path.isdir(full_path):
        os.makedirs(full_path)
    return  # end create_cachedir()

def commandline_call(command, args):
    """ Run a command line or read the text file contents
    return string of text data from a text file (*.txt)
    return True and STDIO text command results
    return False and STDERR if results had errors
    """
    textdata = u''
    commandline = u'%s %s' % (command, args)
    # An absolute path is required.
    path, file_basename, ext = \
            get_filename_parts(command)
    # If this is just a text file then read the file data
    if ext == u'txt' or ext == u'log':
        try:
            filepointer = open(command, 'r')
            textdata = filepointer.read()
            filepointer.close()
            return [True, textdata]
        except:
            return [False, _(u'File could not be opened')]
    # Execute the command
    success = True
    result = exec_commandline(commandline)
    if result[0]:
        textdata = result[0]
    else:
        success = False
        textdata = result[1]
    #
    return [success, textdata]   # end get_textdata()

def get_config(opts, keyframe_adjust=False, ll_report=False,
                      load_db=False):
    """ Read the scripts cfg file and override the setting from
    user specified conmand line options.
    return a configuration dictionary
    """
    err_invalid_variable  = _(
u'''The value for the configuration file variable "%%s" is invalid.
Check the "%s" for valid options.''') % common.CONFIG_FILE
    err_true_false = _(
u'''The value for the configuration file variable "%s" is invalid.
It must be either "true" or "false".''')
    err_bad_path = _(
u'''The value for the configuration file variable "%s" is invalid.
The directory path "%s" does not exist.
%s''')
    err_read_write = _(
u'''The script does not have read and write permissions for the "%s" variables
path: "%s"''')
    err_working_diskspace = _(
u'''There is not enough available disk space in the working directory "%s" available "%s" bytes
to loss less cut recording "%s", size "%s" bytes.''')
    err_missing_subtitle_args = _(
u'''The "%%s" subtitle utility arguments variable is missing from the
configuration file "%s".''') % common.CONFIG_FILE
    err_concert_cuts_0 = _(
u'''The track numbers option "-T" must only be accompanied with the
Stip option "-S".''')
    err_concert_cuts_1 = _(
u'''The Concert Cuts option "-C" must be accompanied with either a "-e" export
or a "-m" move option. Replace "-r" is not valid.''')
    err_concert_cuts_2 = _(
u'''The Concert Cuts option "-C" configuration file
"%s" does not exist.''')
    err_invalid_sequence_number  = _(
u'''The value for the configuration file variable "%s" must end with
a valid integer in the format "delete_rec_01".
''')
    err_no_jobid = _(
u'''There must be a -j "%%JOBID%%" command line argument present when
you use the "error_detection" configuration variables.
You have the following "error_detection" configuration variables active:
%s
''')
    err_invalid_jobid = _(
u'''The job ID -j "%%JOBID%%" command line argument must be an integer.
Your invalid JobID is "%s".
''')
    err_invalid_detection_values = _(
u'''The error detection variable "%s" with configuration arguments:
%s
is not valid.
You may not have replaced all instances of ";" semicolons with "\\;" or
have not provided all four required arguments. Check the
configuration file documentation for the "error_detection" section.
''')
    #
    configuration = {}
    #
    configuration['movepath'] = u''
    configuration['TVexportfmt'] = u''
    configuration['MOVIEexportfmt'] = u''
    configuration['GENERICexportfmt'] = u''
    configuration['keep_log'] = False
    configuration['remove_recorded'] = []
    configuration['mkvmerge_cut_addon'] = None
    configuration['mkvmerge_merge_addon'] = None
    configuration['error_detection'] = []
    #
    ## Initialize the default DVB Subtitle settings
    for key in common.DEFAULT_CONFIG_SETTINGS[
                                    'dvb_subtitle_defaults'].keys():
        configuration[key] = common.DEFAULT_CONFIG_SETTINGS[
                                    'dvb_subtitle_defaults'][key]
    #
    cfg = ConfigParser.RawConfigParser()
    cfg.read(common.CONFIG_FILE)
    #
    ## Check if this config file is old and does not have a
    ## "dvb_subtitles" section. Add the default one if it is missing.
    if "dvb_subtitles" not in cfg.sections():
        add_new_cfg_section(configuration,
                    common.INIT_DVB_SUBTITLE_CONFIG_FILE, cfg)
    #
    ## Check if this config file is old and does not have a
    ## "remove_recorded" section. Add the default one if it is missing.
    if "remove_recorded" not in cfg.sections():
        add_new_cfg_section(configuration,
                    common.INIT_REMOVE_RECORDING_CONFIG_FILE, cfg)
    #
    ## Check if this config file is old and does not have a
    ## "mkvmerge_user_settings" section. Add the default one if
    ## it is missing.
    if "mkvmerge_user_settings" not in cfg.sections():
        add_new_cfg_section(configuration,
                    common.INIT_MKVMERGE_USER_SETTINGS_CONFIG_FILE, cfg)
    #
    ## Check if this config file is old and does not have a
    ## "error_detection" section. Add the default one if
    ## it is missing.
    if "error_detection" not in cfg.sections():
        add_new_cfg_section(configuration,
                    common.INIT_ERROR_DETECTION_CONFIG_FILE, cfg)
    #
    for section in cfg.sections():
        if section[:5] == 'File ':
            configuration['config_file'] = section[5:]
            continue
        if section == 'defaults':
            for option in cfg.options(section):
                if option == 'add_metadata':
                    try:
                        configuration[option] = cfg.getboolean(
                                                    section, option)
                    except ValueError:
                        raise Exception(err_true_false % option)
                    continue
                if option == 'ccextractor_args':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    continue
                if option == 'delete_old':
                    try:
                        configuration[option] = cfg.getboolean(
                                                    section, option)
                    except ValueError:
                        raise Exception(err_true_false % option)
                    continue
                if option == 'movepath':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                            option)
                    continue
                if option == 'keep_log':
                    try:
                        configuration[option] = cfg.getboolean(
                                            section, option)
                    except ValueError:
                        raise Exception(err_true_false % option)
                    continue
                if option == 'logpath':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                            option)
                    continue
                if option == 'movie_format':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    for content in ["%(title)s", "%(releasedate)s", ]:
                        index = configuration[option].find(content)
                        if index == -1:
                            raise Exception(err_invalid_variable %
                                            option)
                if option == 'tvseries_format':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                            option)
                    for content in ["%(series)s", "%(season_num)02d",
                                     "%(episode_num)02d", "%(episode)s", ]:
                        index = configuration[option].find(content)
                        if index == -1:
                            raise Exception(err_invalid_variable %
                                                        option)
                if option == 'strip':
                    try:
                        configuration[option] = cfg.getboolean(
                                                        section, option)
                    except ValueError:
                        raise Exception(err_true_false % option)
                    continue
                if option == 'workpath':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
        if section == 'mythvidexport':
            for option in cfg.options(section):
                if option == 'television':
                    try:
                        configuration['TVexportfmt'] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'movie':
                    try:
                        configuration['MOVIEexportfmt'] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'generic':
                    try:
                        configuration['GENERICexportfmt'] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
        if section == 'dvb_subtitles':
            for option in cfg.options(section):
                if option == 'include_dvb_subtitles':
                    try:
                        configuration[option] = cfg.getboolean(
                                                    section, option)
                    except ValueError:
                        raise Exception(err_true_false % option)
                    continue
                if option == 'moveposition':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'font_point_size':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'background_alpha':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'yoffset':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'xoffset':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'xwidth':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'h_unused':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'vertical':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'yoffset2':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'maxlines':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'unknown_1':
                    try:
                        configuration['unknown_1'] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'unknown_2':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
                if option == 'vobsub_delay':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable %
                                                    option)
                    continue
        if section == 'remove_recorded':
            for option in cfg.options(section):
                if option == u'delete_rec_all':
                    if unicode(cfg.get(section, option), 'utf8') == 'ALL':
                        configuration['remove_recorded'] = [[True, True]]
                        break
                elif option.startswith('delete_rec_'):
                    try:
                        seg_num = int(option.replace('delete_rec_', u''))
                    except ValueError:
                        raise Exception(err_invalid_sequence_number)
                    #
                    try:
                        temp = unicode(cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    #
                    channel_title = [False, False]
                    if temp.find(';') == -1:
                        channel_title[1] = filter(
                                is_not_punct_char, temp.strip().lower())
                    else:
                        index = temp.find(';')
                        channel_title[0] = temp[:index].strip().lower()
                        if temp[-1:] != ';':
                            channel_title[1] = filter(
                                is_not_punct_char, temp[
                                                index:].strip().lower())
                    #
                    configuration['remove_recorded'].append(channel_title)
                    continue
        if section == 'mkvmerge_user_settings':
            for option in cfg.options(section):
                try:
                    configuration[option] = unicode(
                                        cfg.get(section, option), 'utf8')
                    if configuration[option]:
                        configuration[option] = configuration[option].strip()
                except Exception:
                    raise Exception(err_invalid_variable %
                                                option)
                continue
        if section == 'error_detection':
            keys = ['type', 'threshold', 'bash_command', 'comment_string' ]
            for option in cfg.options(section):
                try:
                    error_args_dict = {}
                    for key in keys:
                        error_args_dict[key] = None
                    #
                    original_args = unicode(cfg.get(section, option),
                                        'utf8')
                    error_args = original_args.replace(
                                            '\\;', u';').strip().split(',')
                    # Clean up and empty args
                    if not error_args[-1]:
                        del(error_args[-1])
                    #
                    if len(error_args) > 4:
                        raise Exception(
_(u'''"%s" has too many arguments "%s" detected, there can only be four.
Arguments: %s
Resulting argument list: %s''') % (option, len(error_args),
                                    original_args, error_args))
                    #
                    for count in range(len(error_args)):
                        error_args_dict[keys[count]] = \
                                                error_args[count].strip()
                    #
                    if not error_args_dict['type'] in ['alert', 'abort']:
                        raise Exception(
_(u' Invalid error type "%s" must be "alert" or "abort"') %
                            error_args_dict['type'])
                    #
                    try:
                        error_args_dict['threshold'] = \
                                        int(error_args_dict['threshold'])
                    except (TypeError, ValueError):
                        raise Exception(
_(u' Threshold value "%s" must be an integer.') %
                                        error_args_dict['threshold'])
                    #
                    if not error_args_dict['bash_command']:
                        raise Exception(
_(u' A bash command must be provided.'))
                    #
                    #
                    ## Verify that each variable has a valid argument
                    for key in keys:
                        if error_args_dict[key] == None:
                            raise Exception(
                                err_invalid_detection_values % (
                                                    option, original_args))
                    #
                    configuration['error_detection'].append(error_args_dict)
                #
                except Exception, errmsg:
                    error_message = err_invalid_variable % option
                    error_message += u'\n\n%s' % errmsg
                    raise Exception(error_message)
                continue
    #
    ## Change any configuration settings as dictated
    ## by the command line options
    if load_db:
        configuration['archivefile'] = unicode(opts.archivefile, 'utf8')
        configuration['recordedfile'] = configuration['archivefile']
    else:
        configuration['recordedfile'] = unicode(opts.recordedfile, 'utf8')
    #
    configuration['tracknumber'] = None
    if not keyframe_adjust and not ll_report and not load_db:
        if opts.tracknumber:
            if not opts.noextratracks:
                raise Exception(err_concert_cuts_0)
            configuration['tracknumber'] = opts.tracknumber
            validate_audio_track_number(configuration)
        #
        configuration['delayvideo'] = False
        if opts.delayvideo:
            configuration['delayvideo'] = common.VIDEO_TRACK_DELAY % \
                opts.delayvideo
        ## Check if the Concert Cut option is being used
        configuration['concertcuts'] = opts.concertcuts
        if opts.concertcuts:
            if not opts.mythvideo_export and not opts.movepath:
                raise Exception(err_concert_cuts_1)
            if opts.replace_recorded:
                raise Exception(_(
'''Concert cuts do not support the "-r" replace option.'''))
            #
            if opts.concertcuts != True:
                if opts.concertcuts[0] == '~':
                    opts.concertcuts = os.path.expanduser(u"~") + \
                                                    opts.concertcuts[1:]
            #
            if opts.concertcuts == True:
                configuration['concertcuts'] = \
                            common.CONCERT_CUT_DEFAULT_FORMAT
                configuration['segment_names'] = {}
            elif not os.path.isfile(opts.concertcuts):
                raise Exception(err_concert_cuts_2 % opts.concertcuts)
            else:
                process_concert_cuts_cfg(opts.concertcuts, configuration)
        #
        if opts.addmetadata:
            configuration['add_metadata'] = False
        configuration['movepath'] = u''
        if opts.movepath:
            configuration['movepath'] = unicode(opts.movepath, 'utf8')
        configuration['strip'] = opts.noextratracks
        if opts.workingpath:
            configuration['workpath'] = unicode(opts.workingpath, 'utf8')
        configuration['mythvideo_export'] = opts.mythvideo_export
        configuration['replace'] = opts.replace_recorded
        configuration['forcemythxxextractor'] = opts.forcemythxxextractor
        if configuration['replace']:
            configuration['delete_old'] = configuration['delete_old']
        else:
            configuration['delete_old'] = False
        #
        configuration['format_sup_values'] = u''
        configuration['projectx_ini'] = u''
        if configuration['include_dvb_subtitles']:
            configuration['format_sup_values'] = common.FORMAT_SUP_VALUES % \
                                                        configuration
            #
            fileh = open(common.INIT_PROJECTX_INI_FILE, 'r')
            configuration['projectx_ini'] = (fileh.read() % configuration)
            fileh.close()
        #
        configuration['jobid'] = opts.jobid
        if configuration['error_detection']:
            if not opts.jobid:
                raise Exception(err_no_jobid %
                            configuration['error_detection'])
            try:
                configuration['jobid'] = long(opts.jobid)
            except (TypeError, ValueError):
                raise Exception(err_invalid_jobid % opts.jobid)
    #
    if not ll_report and not load_db:
        if opts.logpath:
            configuration['logpath'] = opts.logpath
        configuration['summary'] = opts.summary
    if not ll_report:
        if opts.keeplog:
            configuration['keep_log'] = True
    configuration['test'] = opts.test
    #
    ## Check that that these variables are in the config dictionary
    for option in ['logpath', 'workpath']:
        if not option in configuration.keys():
            raise Exception(u'The configuration option "%s" is missing.' % (
                                option))
    #
    ## Expand any "~" paths, verify the directory exist and
    ## that the script has both read and write previledges
    if keyframe_adjust or ll_report or load_db:
        dirs = ['logpath', ]
    else:
        dirs = ['logpath', 'movepath', 'workpath']
    for option in dirs:
        if option == 'movepath':
            if not configuration[option]:
                continue
        if configuration[option][0] == '~':
            configuration[option] = os.path.expanduser(
                                    "~")+configuration[option][1:]
        if option == 'workpath':
            if not os.path.isdir(configuration[option]):
                try:
                    create_cachedir(configuration[option])
                except Exception, errmsg:
                    raise Exception(err_bad_path % (option,
                                        configuration[option],
                                        u"Error: " + errmsg))
        #
        if not configuration[option]:
            continue
        if not os.path.isdir(configuration[option]):
            raise Exception(err_bad_path % (option,
                                configuration[option], ""))
        if not os.access(
                configuration[option], os.F_OK | os.R_OK | os.W_OK):
            raise Exception(err_read_write % (option,
                                configuration[option], ))
    #
    configuration['sourcefile'] = configuration['recordedfile']
    file_parts = get_filename_parts(configuration['recordedfile'])
    configuration['recorded_dir'], configuration['recorded_name'], \
        configuration['recorded_ext'] = get_filename_parts(
            configuration['recordedfile'])
    configuration['base_name'] = u'%s.%s' % (
                configuration['recorded_name'],
                configuration['recorded_ext'])
    if ll_report:
        configuration['logfile'] = os.path.join(configuration['logpath'],
                                   "Lossless_Report_%s.log" %
                                   configuration['recorded_name'])
    elif keyframe_adjust:
        configuration['logfile'] = os.path.join(configuration['logpath'],
                                   "Adjustframes_%s.log" %
                                   configuration['recorded_name'])
    elif load_db:
        configuration['logfile'] = os.path.join(configuration['logpath'],
                                   "Load_DB_%s.log" %
                                   configuration['recorded_name'].replace(
                                                            u'.tar', u''))
    else:
        configuration['logfile'] = os.path.join(configuration['logpath'],
                                   configuration['recorded_name'] + u'.log')
    #
    # Remove any old log file
    try:
        os.remove(configuration['logfile'])
    except OSError:
        pass
    #
    # Verify that there is enough disk space in the working drive
    # to perform the edits
    if not keyframe_adjust and not ll_report and not load_db:
        stats = os.statvfs(configuration['workpath'])
        available = stats.f_bsize * stats.f_bavail
        filesize = os.path.getsize(configuration['recordedfile'])
        if not available > filesize:
            raise Exception(err_working_diskspace % (
                                configuration['workpath'],
                                available, configuration['recordedfile'],
                                filesize))
    #
    ## Add the MythTV v0.25+ built in subtitle extractor for
    configuration['mythccextractor_args'] = common.MYTHCCEXTRACTOR_ARGS
    #
    ## Verify that the subtitle utility arguments were in the config file
    if not 'ccextractor_args' in configuration.keys():
        raise Exception(err_missing_subtitle_args % ('ccextractor_args'))
    #
    configuration['strip_args'] = ''
    #
    if ll_report:
        configuration['bugtext'] = opts.bugtext
        configuration['bugarchive'] = opts.bugarchive
        configuration['wiki'] = opts.wiki
        configuration['all'] = opts.all
        configuration['verbose'] = False
        configuration['sample_starttime'] = 0
        #
        if opts.all and not opts.bugarchive:
            raise Exception(
_(u'''The copy all recorded video option "-A" is only valid when the -B,
bug archive option is also selected'''))
        #
        if opts.starttime and not opts.bugarchive:
            raise Exception(
_(u'''The sample startime option "-s" is only valid when the -B, bug archive
option is also selected'''))
        #
        if opts.starttime:
            time = opts.starttime.split(':')
            error = False
            if len(time) == 0:
                error = True
            elif not len(time) == 1:
                for index in range(len(time)):
                    try:
                        time[index] = int(time[index])
                    except ValueError:
                        error = True
                        break
            if error:
                raise Exception(
_(u'The sample startime "%s" is invalid. It must be in "HH:MM:SS" format.') % (
                               opts.starttime))
            if len(time) == 1:
                configuration['sample_starttime'] = int(time[0])
            else:
                count = 0
                for value in reversed(time):
                    if not count:
                        configuration['sample_starttime'] = value
                    else:
                        configuration['sample_starttime'] += value * \
                                                                60 ** count
                    count += 1
    #
    configuration['system_info'] = exec_commandline(
                                u'lsb_release -a && uname -m')[0]
    configuration['system_info'] = configuration['system_info'].replace(
                                u'No LSB modules are available.\n', u'')
    #
    return configuration
#
def process_concert_cuts_cfg(concertcuts, configuration):
    ''' Input variables from a segment.cfg file used to specify
    "-C" Concert Cut variables
    return nothing
    '''
    err_invalid_variable  = _(
'''The value for the configuration file variable "%%s" is invalid.
Check the "%s" for valid options.''') % concertcuts
    err_invalid_segment_number  = _(
'''The value for the configuration file variable "%%s" must end with
a valid integer in the format "segment_01".
Check the "%s" for valid options.''') % concertcuts
    err_invalid_segment_filename  = _(
'''The value for the configuration file variable "%%s" must be
commented out (a leading "#") or must not be an empty sting.
Check the "%s" for valid options.''') % concertcuts
    err_invalid_format  = _(
'''The Concert Cut segment file name format "%%s"
contains the variable "%%s" and therefore the variable
"%%s" must be assigned in the
"%s" file.''') % concertcuts
    #
    configuration['artist'] = u''
    configuration['album'] = u''
    configuration['concertcuts'] = common.CONCERT_CUT_DEFAULT_FORMAT
    configuration['segment_names'] = {}
    #
    cfg = ConfigParser.RawConfigParser()
    cfg.read(concertcuts)
    for section in cfg.sections():
        if section[:5] == 'File ':
            configuration['segment_file'] = section[5:]
            continue
        if section == 'defaults':
            for option in cfg.options(section):
                if option == 'artist':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    continue
                if option == 'album':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    continue
                if option.startswith('segment_'):
                    try:
                        seg_num = int(option.replace('segment_', u''))
                    except ValueError:
                        raise Exception(
                                    err_invalid_segment_number % option)
                    #
                    try:
                        configuration['segment_names'][seg_num] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    #
                    if not configuration['segment_names'][seg_num]:
                        raise Exception(
                                    err_invalid_segment_filename % option)
                    continue
        if section == 'concertcutformat':
            for option in cfg.options(section):
                if option == 'concertcuts':
                    try:
                        configuration[option] = unicode(
                                            cfg.get(section, option), 'utf8')
                    except Exception:
                        raise Exception(err_invalid_variable % option)
                    continue
    #
    variable = '%ARTIST%'
    if configuration['concertcuts'].find(variable) != -1 and \
            not configuration['artist']:
        raise Exception(err_invalid_format %
            (configuration['concertcuts'],
            variable, 'artist'))
    variable = '%ALBUM%'
    if configuration['concertcuts'].find(variable) != -1 and \
            not configuration['album']:
        raise Exception(err_invalid_format %
            (configuration['concertcuts'],
            variable, 'album'))
    #
    return
#
def validate_audio_track_number(configuration):
    ''' Validate that the audio track number actually exists.
    return nothing
    '''
    err_1 = _(u'''Unknown error when attempting to validate audio tracks.
> %s
%s''')
    err_2 = _(u'''There is no audio track number "%s" in recording file
%s
See the track numbers and types as listed by "mkvmerge --identify":
%s''')
    #
    args = u'-i "%(recordedfile)s"' % configuration
    results = commandline_call(common.MKVMERGE, args)
    #
    if not results[0]:
        raise Exception(err_1 % (u'%s %s' % (common.MKVMERGE, args),
                            results[1]))
    #
    track_ids = results[1].split('\n')
    for track in track_ids:
        track_id_index = track.find(':')
        index = track.find('audio')
        if not index == -1:
            if str(configuration['tracknumber']) == \
                        track[:track_id_index].replace(
                            common.TRACK_ID, u'').strip():
                return
    #
    raise Exception(err_2 % (configuration['tracknumber'],
                        configuration['recordedfile'],
                        results[1]))
#
def check_dependancies(configuration):
    '''
    Verify that the scripts dependencies can be satisfied. If any
    are missing then raise and exception and pass an appropriate error message.
    return either 'mythutil' or 'mythcommflag'
    '''
    # Error Messages
    utility_not_found = _(
'''The "%s" utility is not installed or cannot be accessed by
this script. Install it or update the environment.
Error: "%s"''')
    ccextractor_not_found = _(
'''The ccextractor utility could not be found at:
"%s". It should have been installed as part of the lossless_cut package.''')
    mkvmerge_err1 = _(
'''The MKVToolNix utility "mkvmerge" is not installed or cannot be accessed by
this script. Check the MKVToolNix Web site for installation information:
Download: %s
Source: %s
Error: "%s"''')
    mkvmerge_err2 = _(
'''The MKVToolNix utility "mkvmerge" must be version %s.x or higher.
Your version is "v%s". Check the MKVToolNix Web site for installation information:
Download: %s
Source: %s''')
    mediainfo_ppa_commands = _('''PPA commands for most Ubuntu based distributions:
> sudo add-apt-repository ppa:shiki/mediainfo
> sudo apt-get update
> sudo apt-get install mediainfo
''')
    mediainfo_err1 = _(
'''The utility "mediainfo" is not installed or cannot be accessed by
this script. Check the MediaInfo Web site for installation information:
PPA: %%s
%s
Downloads: %%s
Error: "%%s"
''') % mediainfo_ppa_commands
    mediainfo_err2 = _(
'''The utility "mediainfo" must be version %%s or higher.
Your version is "v%%s". Check the MKVToolNix Web site for installation information:
PPA: %%s
%s
Downloads: %%s
''') % mediainfo_ppa_commands
    mythvidexport_err = _(
'''On of the following mythvidexport format settings are missing from the
lossless_cut.cfg file and from the MythTV database settings:
  television:   %(TVexportfmt)s
  movie:        %(MOVIEexportfmt)s
  generic:      %(GENERICexportfmt)s
''')
    no_java_installed_err = _(
'''The "~/.mythtv/lossless_cut.cfg" variable "include_dvb_subtitles" is
set as "true" but there is no java installed or cannot be accessed
by this script. Java must be installed.
For Debian distros use one of the following commands:

> sudo apt-get install libcommons-net-java default-jre
OR for the Sun Java runtime:
> sudo apt-get install java2-runtime
''')
    #
    ## Check for ccextractor
    results = commandline_call('which', configuration['ccextractor'])
    if not results[0]:
        raise Exception(ccextractor_not_found %
            configuration['ccextractor'])
    if not results[1]:
        raise Exception(ccextractor_not_found %
            configuration['ccextractor'])
    #
    ## Check for mkvmerge
    results = commandline_call('which', common.MKVMERGE)
    if not results[0]:
        raise Exception(mkvmerge_err1 % (common.MKVTOOLNIX_DOWNLOADS_URL,
                                    common.MKVTOOLNIX_SOURCE_URL,
                                    results[1]))
    if not results[1]:
        raise Exception(mkvmerge_err1 % (common.MKVTOOLNIX_DOWNLOADS_URL,
                                   common.MKVTOOLNIX_SOURCE_URL,
                                    results[1]))
    results = commandline_call(common.MKVMERGE, '--version')
    if not results[0]:
        raise Exception(mkvmerge_err1 % (common.MKVTOOLNIX_DOWNLOADS_URL,
                                    common.MKVTOOLNIX_SOURCE_URL,
                                    results[1]))
    #
    configuration['mkvmerge_version'] = \
                results[1].replace(u'\n', u'').strip()
    #
    index = results[1].find(' v')
    if index == -1:
        raise Exception(mkvmerge_err2 %
            ("unknown", common.MKVTOOLNIX_DOWNLOADS_URL,
                                    common.MKVTOOLNIX_SOURCE_URL))
    if not results[1][index+2:index+5] >= common.MKVMERGE_MIN_VERSION:
        raise Exception(mkvmerge_err2 %
            (common.MKVMERGE_MIN_VERSION,
            results[1][index+2:index+5], common.MKVTOOLNIX_DOWNLOADS_URL,
                                    common.MKVTOOLNIX_SOURCE_URL))
    #
    ## Check for mediainfo
    results = commandline_call('which', common.MEDIAINFO)
    if not results[0]:
        raise Exception(mediainfo_err1 % (
                common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL,
                                    results[1]))
    if not results[1]:
        raise Exception(mediainfo_err1 % (
                common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL,
                                    results[1]))
    results = commandline_call(common.MEDIAINFO, '--version')
    if not results[0]:
        raise Exception(mediainfo_err1 % (
                common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL,
                                    results[1]))
    #
    configuration['mediainfo_version'] = \
                results[1].replace(u'\n', u'').strip()
    #
    mkvinfo_version = 'MediaInfoLib - '
    add_index = len(mkvinfo_version)
    index = results[1].find(mkvinfo_version)
    if index == -1:
        raise Exception(mediainfo_err2 % (
            "unknown", results[1][index+add_index:index+add_index+6],
                common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL))
    if not results[1][
            index+add_index:index+add_index+6] >= \
                                common.MEDIAINFO_MIN_VERSION:
        raise Exception(mediainfo_err2 % (
            common.MEDIAINFO_MIN_VERSION,
            results[1][index+add_index:index+add_index+6],
                common.MEDIAINFO_PPA_URL, common.MEDIAINFO_URL))
    #
    ## Check for either mythutil or mythcommflag
    mythutil = 'mythutil'
    mythcommflag = 'mythcommflag'
    #
    results = commandline_call('which', mythutil)
    if not results[1]:
        results = commandline_call('which', mythcommflag)
        if not results[0]:
            raise Exception(utility_not_found % ('neither %s or %s' %
                                            (mythutil, mythcommflag),
                                                results[1]))
        mythutil = mythcommflag
    #
    ## Check if a Java runtime is installed
    if configuration['include_dvb_subtitles']:
        results = commandline_call('which', 'java')
        if not results[0]:
            raise Exception(no_java_installed_err)
        configuration['java'] = results[1].replace('\n', u'').strip()
    #
    ## Display that the user is missing their mythvidexport settings
    if configuration.has_key('mythvideo_export'):
        if not configuration['TVexportfmt'] or \
                not configuration['MOVIEexportfmt'] or \
                not configuration['GENERICexportfmt']:
            raise Exception(mythvidexport_err % configuration)
    #
    return mythutil
#
def read_iso_language_codes(logger=False):
    ''' Read in a text file of ISO639-2 language codes and convert into
    a dictionary.
    Source: http://loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    return dictionary of ISO639-2 language codes
    '''
    lang_codes = {}
    if not os.path.isfile(common.ISO639_2_LANG_CODE_FILE):
        return lang_codes
    #
    fileh = open(common.ISO639_2_LANG_CODE_FILE, 'r')
    lang_text_list = unicode(fileh.read(), 'utf8').split(u'\n')
    fileh.close()
    #
    for count in range(len(lang_text_list[:-1])):
        if lang_text_list[count].find(u'|') == -1:
            if logger:
                # Show count one less as the first line should be the download
                # date time text e.g. "Downloaded on Thursday Sept, 13th 2012"
                logger.info(_(
u''''ISO639-2 language code file was last updated on %s contains %d language codes''') %
                    (lang_text_list[count].strip('\n'),
                        len(lang_text_list) - 1))
            continue
        #
        one_line = lang_text_list[count].replace(u'\n', u'').strip().split(u'|')
        # Clean and lowrcase each value
        for index in range(len(one_line)):
            one_line[index] = one_line[index].strip().lower()
        # Extract each item:
        isocode = one_line[0]
        match_text = u''
        for text_count in range(3, 5):
            if one_line[text_count]:
                match_text += u' ' + one_line[text_count]
        match_text = match_text.strip()
        if not match_text:
            continue
        lang_codes[isocode] = match_text
    #
    return lang_codes
#
def get_iso_language_code(lang_codes, sublanguage, logger=False):
    ''' Read in a text file of ISO639-2 language codes and convert into
    a dictionary.
    Source: http://loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    return an ISO639-2 language code if one matches subtitle language
    return empty string if no match found
    '''
    #
    # Find a language match
    lower_sublanguage = sublanguage.lower()
    for key in lang_codes.keys():
        if not lang_codes[key].find(lower_sublanguage) == -1:
            if logger:
                logger.info(_(
u''''ISO639-2 language code match found for "%s" language codes "%s" will be used.''') %
                (sublanguage, key))
            return key
    else:
        if logger:
            logger.info(_(
u''''No matching ISO639-2 language code was found for "%s" subtitle will default to "unknown".''') %
                (sublanguage))
        return u''
#
def make_timestamp(secs):
    '''Take a floating point number of fractional seconds and
    convert into a cut point timestamp.
    return a timestamp in the format "00:00:00.123456789"
    '''
    timestamp = unicode((datetime.min +
                        timedelta(0,int(secs))).time().strftime(
                        '%H:%M:%S') + (u'%0.09f' % (
                        secs - int(secs)))[1:])
    #
    return timestamp
#
def display_recorded_info(configuration, logger=False):
    ''' Display information about the recorded video.
    return verbage if there is no logger specified
    '''
    # TRANSLATORS: Please leave %s as it is,
    # because it is needed by the program.
    # Thank you for contributing to this project.
    verbage = \
            _(u'''
Recorded video file information:
    Frames per second (FPS):      %(fps).03f
    WidthxHeight in pixels:       %(width)sx%(height)s

Cut list:
    Original:           (%(rawcutlist)s)
    Inclusive:          (%(pre_massage_cutlist)s)
    Keyframe adjusted:  (%(keyframe_cuts)s)

Recording device:
    Name:                   "%(recorder_displayname)s"
    Card type:              "%(recorders_cardtype)s"
    Default Input:          "%(recorders_defaultinput)s"
    Video Device:           "%(recorders_videodevice)s"
    Audio Device:           "%(recorders_audiodevice)s"
    Host name:              "%(recorders_hostname)s"
''') % configuration
    #
    # TRANSLATORS: Please leave %s as it is,
    # because it is needed by the program.
    # Thank you for contributing to this project.
    verbage += \
            _(u'''
Track totals:
    %(total_video)d Video track(s)
    %(total_audio)d Audio track(s)
    %(total_subtitle)d Subtitle track(s)

''') % configuration['trackinfo']
    #
    ## Build track by track detail lines
    ## Track # then valuable details per type
    #
    for track_type in common.TRACK_DISPLAY_ORDER:
        if configuration['trackinfo']['total_%s' % track_type] == 0:
            continue
        #
        verbage += _(
u'''%s track details:
''') % (track_type.title())
        for detail_dict in configuration['trackinfo'][
                                        '%s_details' % track_type]:
            track_details = u''
            for key in common.TRACK_ELEM_DICT[track_type]:
                if not detail_dict[key]:
                    continue
                track_details += _(
u'''    %s %s
''') % ((key.replace(u'_', u' ').strip() + u':').ljust(24), detail_dict[key])
            ##
            verbage += track_details + u'\n'
    #
    if logger:
        logger.info(verbage)
    else:
        return verbage
    #
    return
#
def get_mediainfo(video_file, element_filter, tracks_filter,
                    etree, logger, sys):
    ''' Use the utility mediainfo to collect detailed track
    information about a video file.
    return dictionary containing an etree of info and track stats
    '''
    tracks = {}
    #
    # Get XML from mediainfo
    result = commandline_call(u'mediainfo',
                common.MEDIAINFO_XML %  video_file)
    stdout = result[1]
    logger.info(
_(u'''mediainfo get video file details in XML format command:
> mediainfo %s

%s
''') % (common.MEDIAINFO_XML %  video_file, stdout))
    if not result[0]:
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        verbage = _(
u'''Mediainfo failed to get track information for
video file "%s", aborting script.
Error: %s
''') % (video_file, result[1])
        logger.critical(verbage)
        sys.stderr.write(verbage)
        exit(int(common.JOBSTATUS().ABORTED))
    #
    # Create an etree structure from the mediainfo XML
    tracks['etree'] = etree.fromstring(str(result[1]))
    #
    # Extract some statistics etree
    tracks['general'] = tracks_filter(tracks['etree'],
                                track_type = "General")[0]
    tracks['video'] = tracks_filter(tracks['etree'],
                                track_type = "Video")
    tracks['audio'] = tracks_filter(tracks['etree'],
                                track_type = "Audio")
    tracks['subtitle'] = tracks_filter(tracks['etree'],
                                track_type = "Text")
    tracks['total_video'] = len(tracks['video'])
    tracks['total_audio'] = len(tracks['audio'])
    tracks['total_subtitle'] = len(tracks['subtitle'])
    tracks['total_tracks'] = tracks['total_video'] + \
                                tracks['total_audio'] + \
                                tracks['total_subtitle']
    #
    ## Extract video duration
    tracks['video_duration'] = 0.0
    if element_filter(tracks['general'], element = u'Duration'):
        duration_element = u' ' + element_filter(tracks['general'],
                                          element = u'Duration')[0]
        for key in common.DURATION_REGEX.keys():
            match = common.DURATION_REGEX[key].match(duration_element)
            if match:
                if len(match.groups()) > 1:
                    number = float(match.groups()[1])
                else:
                    number = float(match.groups()[0])
                if key.startswith('millsecs'):
                    tracks['video_duration'] += number / 1000.0
                elif key.startswith('secs'):
                    tracks['video_duration'] += number
                elif key.startswith('mins'):
                    tracks['video_duration'] += number * 60
                elif key.startswith('hrs'):
                    tracks['video_duration'] += number * 60 * 60
    #
    ## Extract track detils:
    for track_type in common.TRACK_ELEM_DICT.keys():
        if tracks['total_%s' % track_type]:
            tracks['%s_details' % track_type] = []
            for track in tracks[track_type]:
                one_track = {}
                for element in common.TRACK_ELEM_DICT[track_type]:
                    for text in element_filter(track,
                                                element = element):
                        one_track[element] = text
                        break
                    else:
                        one_track[element] = None
                tracks['%s_details' % track_type].append(one_track)
    #
    ## Video FPS, Height, Width and scan type (p or i)
    tracks['video_track_details'] = {}
    if len(tracks['video']):
        for key in ['Width', 'Height', 'Original_frame_rate', 'Scan_type',]:
            tracks['video_track_details'][key] = None
            data = element_filter(tracks['video'][0], element = key)
            if data:
                if data[0].endswith('pixels'):
                    data[0] = data[0].replace('pixels',
                                    u'').replace(' ', u'').strip()
                if data[0].find(' ') != -1:
                    tracks['vide_tracko_details'][key] = \
                                data[0][:data[0].find(' ')].strip()
                else:
                    tracks['video_track_details'][key] = data[0]
            elif key == 'Original_frame_rate':
                #
                ## Special processing for frame rate
                try:
                    tracks['video_track_details']['Original_frame_rate'] = \
                        element_filter(tracks['video'][0],
                                            element = u'Frame_rate')[0]
                except IndexError:
                    # TRANSLATORS: Please leave %s as it is,
                    # because it is needed by the program.
                    # Thank you for contributing to this project.
                    verbage = _(
u'''Mediainfo failed to find FPS video track information for
video file "%s". It is likely that something
is wrong with the video file. The script will attempt to see
if MythTV has the FPS values.
''') % (video_file)
                    logger.critical(verbage)
                    sys.stderr.write(verbage)
                #
                if not tracks['video_track_details'][
                                    'Original_frame_rate'] == None:
                    tracks['video_track_details']['Original_frame_rate'] = \
                        tracks['video_track_details'][
                                'Original_frame_rate'].replace(
                                 'fps', u'').replace('.', u'').strip()
    #
    ## Check for SRT tracks and gather info about those tracks
    ## Also check for DVB Subtitle tracks and calculate a usable ms delay
    ## value from the "Delay_relative_to_video" element string
    count = 0
    tracks['srt_format'] = []
    for subetree in tracks['subtitle']:
        code_id_elem = subetree.xpath('./Codec_ID')
        if code_id_elem:
            if code_id_elem[0].text.startswith('S_TEXT'):
                tracks['srt_format'].append({
                    'id': element_filter(subetree,
                                                element = 'Codec_ID')[0],
                    'format': element_filter(subetree,
                                                element = 'Format')[0],
                    'default': element_filter(subetree,
                                                element = 'Default')[0],
                    'forced': element_filter(subetree,
                                                element = 'Forced')[0],
                    })
        #
        ## Subtitle track delay
        if tracks['subtitle_details'][count][
                                    'Delay_relative_to_video'] != None:
            duration_element = tracks['subtitle_details'][count][
                                    'Delay_relative_to_video']
            delay_time = 0
            pos_neg = 1
            for key in common.DURATION_REGEX.keys():
                match = common.DURATION_REGEX[key].match(duration_element)
                if match:
                    if len(match.groups()) > 1:
                        number = int(match.groups()[1])
                    else:
                        number = int(match.groups()[0])
                    # Deal with negative delays
                    if number < 0:
                        pos_neg = -1
                        number = number * pos_neg
                    if key.startswith('millsecs'):
                        delay_time += number
                    elif key.startswith('secs'):
                        delay_time += number * 1000
                    elif key.startswith('mins'):
                        delay_time += number * 60 * 1000
                    elif key.startswith('hrs'):
                        delay_time += number * 60 * 60 * 1000
            tracks['subtitle_details'][count]['Delay_relative_to_video'] = \
                delay_time * pos_neg
        #
        count += 1
    #
    return tracks
#
def locate_matching_file(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    import fnmatch
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            return os.path.join(path, filename)
#
def cleanup_working_dir(workingpath, recorded_name):
    ''' Remove any recording related files from the working directory.
    return nothing
    '''
    #
    for filename in glob(u'%s/%s*' % (workingpath, recorded_name, )):
        os.remove(filename)
    #
    return
#
def create_config_file():
    ''' Create the inital "~/.mythtv/lossless_cut.cfg" configuration file.
    return nothing
    '''
    #
    # Initialize the new configuration with default values file
    fileh = open(common.INIT_CONFIG_FILE, 'r')
    init_config = fileh.read()
    fileh.close()
    # Add the DVB Subtitle configuration section
    fileh = open(common.INIT_DVB_SUBTITLE_CONFIG_FILE, 'r')
    init_config += u'\n' + (fileh.read() % \
                common.DEFAULT_CONFIG_SETTINGS['dvb_subtitle_defaults'])
    fileh.close()
    # Add the Remove Recoding configuration section
    fileh = open(common.INIT_REMOVE_RECORDING_CONFIG_FILE, 'r')
    init_config += u'\n' + fileh.read()
    fileh.close()
    # Add the Mkvmerge User Settings configuration section
    fileh = open(common.INIT_MKVMERGE_USER_SETTINGS_CONFIG_FILE, 'r')
    init_config += u'\n' + fileh.read()
    fileh.close()
    # Add the error detection User Settings configuration section
    fileh = open(common.INIT_ERROR_DETECTION_CONFIG_FILE, 'r')
    init_config += u'\n' + fileh.read()
    fileh.close()
    #
    # Add the default configuration settings
    init_config = init_config % common.DEFAULT_CONFIG_SETTINGS
    # Save the new configuration file
    try:
        fileh = open(common.CONFIG_FILE, 'w')
    except IOError, errmsg:
        # TRANSLATORS: Please leave %s as it is,
        # because it is needed by the program.
        # Thank you for contributing to this project.
        directory, basefilename = os.path.split(common.CONFIG_FILE)
        verbage = _(
u'''Could not create the "%s" file in directory "%s". This is likely a
directory Read/Write permission issue but check the error message
below to confirm, aborting script.
Error: %s''') % (basefilename, directory, errmsg)
        raise IOError(verbage)
    fileh.write(init_config)
    fileh.close()
    #
    return
#
def add_new_cfg_section(configuration, section, cfg):
    ''' Concatinate a new configuration section.
    return nothing
    '''
    err_cannot_create_cfg_file = _(
u'''Could not create the "%s" file in directory "%s". This is likely a
directory Read/Write permission issue but check the error message
below to confirm, aborting script.
Error: %s''')
    #
    fileh = open(common.CONFIG_FILE, 'r')
    init_config = fileh.read()
    fileh.close()
    #
    fileh = open(section, 'r')
    new_line = u''
    if init_config[-1:] != u'\n':
        new_line = u'\n'
    init_config += new_line + (fileh.read() % configuration)
    fileh.close()
    #
    # Save the new configuration file
    try:
        fileh = open(common.CONFIG_FILE, 'w')
    except IOError, errmsg:
        directory, basefilename = os.path.split(common.CONFIG_FILE)
        verbage = err_cannot_create_cfg_file % \
                (basefilename, directory, errmsg)
        raise Exception(verbage)
    #
    fileh.write(init_config)
    fileh.close()
    #
    ## Reinitialize the config file structure
    cfg.read(common.CONFIG_FILE)
    #
    return
