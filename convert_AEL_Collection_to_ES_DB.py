#!/usr/bin/python -B
# -*- coding: utf-8 -*-

# Converts an AEL ROM Collection into EmulationStation databases.
# Also converts AML Favourites.
# It copies all ROMs to a new location.
# It generates es_systems.cfg and the necessary gamelist.xml.
# Note that this overwrites the EmulationStation databases.
# ES does not support rendering Unicode characters, plots are converted to ASCII.
# The script exits if any problem is found.

# Copyright (c) 2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree

# --- Configuration ------------------------------------------------------------------------------
AEL_COLLECTION_NAME = 'EmulationStation'
AEL_ROM_ARTWORK_FIELD = 's_3dbox'
AML_ROM_ARTWORK_FIELD = 'snap' # 3dbox, cabinet, snap, title
ES_MAME_PLATFORM = 'mame'
RETROARCH_PATH = '/home/kodi/bin/retroarch'
LIBRETRO_PATH = '/home/kodi/bin/libretro/'
MAME_PATH = '/home/kodi/bin/mame64'
KODI_USERDATA_DIR = '/home/kodi/.kodi/userdata/'
AEL_CODE_DIR = '/home/kodi/.kodi/addons/plugin.program.advanced.emulator.launcher/'
AEL_DATA_DIR = '/home/kodi/.kodi/userdata/addon_data/plugin.program.advanced.emulator.launcher/'
AML_DATA_DIR = '/home/kodi/.kodi/userdata/addon_data/plugin.program.AML/'
AML_MAME_ROMS_DIR = '/home/kodi/MAME-ROMs/'
ES_ROMS_DIR = '/home/kodi/EmulationStation-ROMs/'
ES_ROMS_MAME_EXTRA_DIR = '/home/kodi/EmulationStation-ROMs/mame-extra/'
ES_CONFIG_DIR = '/home/kodi/.emulationstation/'

# Aborts program if platform cannot be converted, for example, the Unknown platform.
# ES platform names https://github.com/RetroPie/es-theme-carbon
# BIOSes required:
# xxxxx - corename
# ...
def AEL_to_ES_platform(platform):
    AEL_to_ES_platform = {
        'Atari 2600' : ('atari2600', 'Atari 2600', 'stella_libretro.so'),

        'NEC PC Engine' : ('pcengine', 'PC Engine', 'mednafen_pce_fast_libretro.so'),
        'NEC PC Engine CDROM2' : ('pcenginecd', 'PC Engine CDROM2', 'mednafen_pce_fast_libretro.so'),

        'Nintendo GameBoy' : ('gb', 'Nintendo GameBoy', 'sameboy_libretro.so'),
        'Nintendo GameBoy Color' : ('gbc', 'Nintendo GameBoy Color', 'sameboy_libretro.so'),
        'Nintendo GameBoy Advance' : ('gba', 'Nintendo GameBoy Advance', 'mgba_libretro.so'),
        'Nintendo DS' : ('nds', 'Nintendo DS', 'desmume_libretro.so'),
        'Nintendo Famicon Disk System' : ('fds', 'Nintendo Famicon Disk System', 'mesen_libretro.so'),
        'Nintendo NES' : ('nes', 'Nintendo Entertainment System', 'mesen_libretro.so'),
        'Nintendo SNES' : ('snes', 'Super Nintendo', 'snes9x_libretro.so'),
        'Nintendo 64' : ('n64', 'Nintendo 64', 'mupen64plus_next_libretro.so'),
        'Nintendo GameCube' : ('gc', 'Nintendo GameCube', 'dolphin_libretro.so'),

        'Sega Game Gear' : ('gamegear', 'Sega Game Gear', 'genesis_plus_gx_libretro.so'),
        'Sega Master System' : ('mastersystem', 'Master System', 'genesis_plus_gx_libretro.so'),
        'Sega Mega Drive' : ('megadrive', 'Mega Drive', 'genesis_plus_gx_libretro.so'),
        'Sega MegaCD' : ('segacd', 'Sega MegaCD', 'genesis_plus_gx_libretro.so'),
        'Sega 32X' : ('sega32x', 'Sega 32X', 'picodrive_libretro.so'),
        'Sega Saturn' : ('saturn', 'Sega Saturn', 'mednafen_saturn_libretro.so'),
        'Sega Dreamcast' : ('dreamcast', 'Sega Dreamcast', 'flycast_libretro.so'),

        'Sony PlayStation' :  ('psx', 'PlayStation', 'mednafen_psx_libretro.so'),
        'Sony PlayStation Portable' :  ('psp', 'PlayStation', 'mednafen_psx_libretro.so'),
    }

    return AEL_to_ES_platform[platform]

C_RED   = "\033[1;31m"
C_BLUE  = "\033[1;34m"
C_CYAN  = "\033[1;36m"
C_GREEN = "\033[0;32m"
C_END   = "\033[0;0m"

# --- Functions ----------------------------------------------------------------------------------
# Returns a list of dictionaries and a dictionary index { m_name : index, ... }
def read_Collection_XML(fname):
    collections = []
    collections_idx = {}
    print('read_Collection_XML() Loading {}'.format(fname))
    try:
        xml_tree = xml.etree.ElementTree.parse(fname)
    except xml.etree.ElementTree.ParseError as ex:
        log_error('(ParseError) Exception parsing XML categories.xml')
        log_error('(ParseError) {}'.format(str(ex)))
        raise ex
    xml_root = xml_tree.getroot()
    for root_element in xml_root:
        if root_element.tag == 'Collection':
            collection = {}
            for rom_child in root_element:
                xml_tag  = rom_child.tag
                xml_text = rom_child.text if rom_child.text is not None else ''
                xml_text = text_unescape_XML(xml_text)
                collection[xml_tag] = xml_text
            collections.append(collection)
            if collection['m_name'] in collections_idx:
                raise TypeError('Repeated collection {}'.format(collection['m_name']))
            collections_idx[collection['m_name']] = len(collections) - 1

    return (collections, collections_idx)

# Returns a list of dictionaries.
def read_Collection_ROMs_JSON(fname):
    print('read_Collection_ROMs_JSON() Loding {}'.format(fname))
    with open(fname) as file:
        try:
            raw_data = json.load(file)
        except ValueError as ex:
            statinfo = roms_json_file.stat()
            log_error('ValueError exception in json.load() function')
            log_error('File {}'.format(roms_json_file.getOriginalPath()))
            log_error('Size {}'.format(statinfo.st_size))
            raise ex
    roms = raw_data[1]

    return roms

def fs_load_JSON_file_dic(json_filename, verbose = True):
    # --- If file does not exist return empty dictionary ---
    data_dic = {}
    if not os.path.isfile(json_filename):
        print('fs_load_JSON_file_dic() File not found "{}"'.format(json_filename))
        return data_dic
    if verbose:
        print('fs_load_JSON_file_dic() "{}"'.format(json_filename))
    with open(json_filename) as file:
        data_dic = json.load(file)

    return data_dic

def XML_text(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{}<{}>{}</{}>'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        line = '{}<{} />'.format(' ' * num_spaces, tag_name)
    return line

def text_escape_XML(data_str):
    # Ampersand MUST BE replaced FIRST
    data_str = data_str.replace('&', '&amp;')
    data_str = data_str.replace('>', '&gt;')
    data_str = data_str.replace('<', '&lt;')
    data_str = data_str.replace("'", '&apos;')
    data_str = data_str.replace('"', '&quot;')
    data_str = data_str.replace('\n', '&#10;')
    data_str = data_str.replace('\r', '&#13;')
    data_str = data_str.replace('\t', '&#9;')

    return data_str

def text_unescape_XML(data_str):
    data_str = data_str.replace('&quot;', '"')
    data_str = data_str.replace('&apos;', "'")
    data_str = data_str.replace('&lt;', '<')
    data_str = data_str.replace('&gt;', '>')
    data_str = data_str.replace('&#10;', '\n')
    data_str = data_str.replace('&#13;', '\r')
    data_str = data_str.replace('&#9;', '\t')
    # Ampersand MUST BE replaced LAST
    data_str = data_str.replace('&amp;', '&')

    return data_str

def copy_file_if_new(src_fname, dest_fname):
    # If source files does not exists return.
    if not os.path.isfile(src_fname):
        print('Source file does not exist.')
        return
    # If destination file does not exists copy automatically.
    if os.path.isfile(dest_fname):
        # File exists. Check if sizes are different.
        # Check if source is newer than dest. st_mtime is seconds since the epoch.
        src_stat = os.stat(src_fname)
        dest_stat = os.stat(dest_fname)
        if src_stat.st_size == dest_stat.st_size and src_stat.st_mtime < dest_stat.st_mtime:
            # Not necessary to copy file.
            return
    # If we reach this point copy file.
    print('Copy {}'.format(src_fname))
    print('  to {}'.format(dest_fname))
    dest_fname_dir = os.path.dirname(dest_fname)
    if not os.path.exists(dest_fname_dir): os.makedirs(dest_fname_dir)
    shutil.copy(src_fname, dest_fname)

# files_set is a fully qualified file names.
# Also cleans empty subdirectories.
def clean_unknown_files(dir_name, files_set):
    # Root is a string with a directory. dirs and files are lists.
    # The loops produces an interation for every subdirectory in dir_name,
    # including dir_name itself.
    for root, dirs, files in os.walk(dir_name):
        # Clean files not in list.
        for file in files:
            file_name = os.path.join(root, file)
            if file_name in files_set: continue
            print('RM file "{}"'.format(file_name))
            os.unlink(file_name)

    # Clean empty subdirectories.
    for root, dirs, files in os.walk(dir_name):
        if dirs or files: continue
        print('RM empty dir "{}"'.format(root))
        os.rmdir(file_name)

# Converts a year string into ES date format, example: 19950311T000000.
# Currently AEL only uses year so only the year needs to be converted.
# If conversion not possible it returns ''
def get_release_date(year):
    if re.match('^\d\d\d\d$', year):
        return '{}0101T000000'.format(year)
    else:
        return ''

# --- Main ---------------------------------------------------------------------------------------
print(C_RED + 'Converting AEL Collection {} to ES database'.format(AEL_COLLECTION_NAME) + C_END)

# Open AEL collection index.
collection_fname = os.path.join(AEL_DATA_DIR, 'collections.xml')
collections, collections_idx = read_Collection_XML(collection_fname)
if AEL_COLLECTION_NAME not in collections_idx:
    print('Collection {} not found. Exiting.'.format(AEL_COLLECTION_NAME))
    sys.exit(1)
print('Loaded {} collections'.format(len(collections)))
collection_dic = collections[collections_idx[AEL_COLLECTION_NAME]]

# Open collection ROMs DB.
roms_base_noext = collection_dic['roms_base_noext']
collection_ROMs_fname = os.path.join(AEL_DATA_DIR, 'db_Collections' + '/' + roms_base_noext + '.json')
roms = read_Collection_ROMs_JSON(collection_ROMs_fname)
print('Loaded {} ROMs'.format(len(roms)))

# Read AML Favourites.
AML_favs_fname = os.path.join(AML_DATA_DIR, 'Favourite_Machines.json')
aml_favs = fs_load_JSON_file_dic(AML_favs_fname)
print('Loaded {} machines'.format(len(aml_favs)))

# Read ROM_Set_machine_files.json to know the dependencies (ZIP, CHD, Sample) of each machine.
RSMF_fname = os.path.join(AML_DATA_DIR, 'ROM_Set_machine_files.json')
RSMF_dic = fs_load_JSON_file_dic(RSMF_fname)
print('Loaded {} machines'.format(len(RSMF_dic)))

# Traverse ROMs, copy ROM files and artwork.
es_systems_list = [] # List of new_system_dic() dictionaries.
es_systems_idx = {} # Key platform, value index in es_systems_list
es_gamelist_dic = {} # Key system name, value list of dictionaries new_game_dic().
Files_set = set()
print(C_RED + 'Synchronizing AEL Collection ROMs...' + C_END)
for rom in roms:
    # Check if ES system exists for this ROM. If not create it.
    platform_tuple = AEL_to_ES_platform(rom['platform'])
    es_platform = platform_tuple[0]
    long_platform = platform_tuple[1]
    corename = platform_tuple[2]
    if es_platform not in es_systems_idx:
        core_path = os.path.join(LIBRETRO_PATH, corename)
        command = '{} -L {} %ROM%'.format(RETROARCH_PATH, core_path)
        system = {
            'name' : es_platform,
            'fullname' : long_platform,
            'path' : os.path.join(ES_ROMS_DIR, es_platform),
            'command' : command,
            'platform' : es_platform,
            'theme' : es_platform,
            'extension_list' : [],
        }
        es_systems_list.append(system)
        es_systems_idx[es_platform] = len(es_systems_list) - 1
        es_gamelist_dic[es_platform] = []

    # Add ROM to ES database.
    # See https://github.com/Aloshi/EmulationStation/blob/master/GAMELISTS.md
    es_rom = {
        'name' : rom['m_name'],
        'desc' : rom['m_plot'],
        'releasedate' : get_release_date(rom['m_year']),
        'developer' : rom['m_developer'],
        'publisher' : '',
        'genre' : rom['m_genre'],
        'players' : rom['m_nplayers'],
    }
    es_gamelist_dic[es_platform].append(es_rom)

    # Add ROM extension to the list of extensions for this system.
    rom_ext = os.path.splitext(rom['filename'])[1]
    system = es_systems_list[es_systems_idx[es_platform]]
    if rom_ext not in system['extension_list']: system['extension_list'].append(rom_ext)

    # Copy ROM ZIP file.
    # TODO Only copy file is src is newer than dest.
    rom_basename = os.path.basename(rom['filename'])
    new_rom_fname = os.path.join(ES_ROMS_DIR, es_platform, rom_basename)
    es_rom['path'] = new_rom_fname
    print(C_GREEN + 'ROM {}'.format(rom_basename) + C_END)
    copy_file_if_new(rom['filename'], new_rom_fname)
    Files_set.add(new_rom_fname)

    # Copy ROM artwork file. Artwork must have same name as ROM (but different extension).
    if rom[AEL_ROM_ARTWORK_FIELD]:
        art_fname = rom[AEL_ROM_ARTWORK_FIELD]
        art_ext = os.path.splitext(art_fname)[1]
        rom_basename_noext = os.path.splitext(rom_basename)[0]
        new_art_fname = os.path.join(ES_ROMS_DIR, es_platform, rom_basename_noext + art_ext)
        es_rom['image'] = new_art_fname
        if art_fname.startswith('special://profile/'):
            art_fname = art_fname.replace('special://profile/', KODI_USERDATA_DIR)
        print('Art {}'.format(os.path.basename(art_fname)))
        copy_file_if_new(art_fname, new_art_fname)
        Files_set.add(new_art_fname)
    else:
        print('No artwork available.')
        es_rom['image'] = ''

# Now synchronize arcade ROMs.
system = {
    'name' : ES_MAME_PLATFORM,
    'fullname' : 'MAME',
    'path' : os.path.join(ES_ROMS_DIR, ES_MAME_PLATFORM),
    'command' : '{} %BASENAME%'.format(MAME_PATH),
    'platform' : ES_MAME_PLATFORM,
    'theme' : ES_MAME_PLATFORM,
    'extension_list' : ['.zip'],
}
if ES_MAME_PLATFORM in es_systems_idx:
    raise RuntimeError('Platform {} already in es_systems_idx'.format(ES_MAME_PLATFORM))
es_systems_list.append(system)
es_systems_idx[ES_MAME_PLATFORM] = len(es_systems_list) - 1
es_gamelist_dic[ES_MAME_PLATFORM] = []
print(C_RED + 'Synchronizing AML Favourite ROMs...' + C_END)
for mname in sorted(aml_favs, key = lambda x: x.lower()):
    machine = aml_favs[mname]
    asset_dic = aml_favs[mname]['assets']
    es_rom = {
        'name' : machine['description'],
        'desc' : '',
        'releasedate' : get_release_date(machine['year']),
        'developer' : machine['manufacturer'],
        'publisher' : '',
        'genre' : machine['genre'],
        'players' : machine['nplayers'],
    }

    # Copy ROM ZIP file and dependencies.
    print(C_GREEN + 'Machine {}'.format(mname) + C_END)
    machine_files = RSMF_dic[mname]
    for mindex, rom_basename_noext in enumerate(machine_files['ROMs']):
        rom_basename = rom_basename_noext + '.zip'
        print('ROM {}'.format(rom_basename))
        rom_fname = os.path.join(AML_MAME_ROMS_DIR, rom_basename)
        # Copy machine main ROMs to MAME directory. Copy dependencies to an
        # alternative directory so don't show in EmulationStation.
        if rom_basename_noext == mname:
            new_rom_fname = os.path.join(ES_ROMS_DIR, ES_MAME_PLATFORM, rom_basename)
        else:
            new_rom_fname = os.path.join(ES_ROMS_MAME_EXTRA_DIR, rom_basename)
        copy_file_if_new(rom_fname, new_rom_fname)
        Files_set.add(new_rom_fname)
    new_rom_fname = os.path.join(ES_ROMS_DIR, ES_MAME_PLATFORM, mname + '.zip')
    es_rom['path'] = new_rom_fname
    rom_basename = mname + '.zip'
    # print('Added to ES database "{}"'.format(new_rom_fname))
    # print('Machine basename "{}"'.format(rom_basename))

    # Copy ROM artwork file. Artwork must have same name as ROM (but different extension).
    if not asset_dic[AML_ROM_ARTWORK_FIELD]:
        print('Empty artwork {}. Skipping.'.format(AML_ROM_ARTWORK_FIELD))
        es_rom['image'] = ''
        continue
    art_fname = asset_dic[AML_ROM_ARTWORK_FIELD]
    art_basename = os.path.basename(art_fname)
    art_ext = os.path.splitext(art_fname)[1]
    rom_basename_noext = os.path.splitext(rom_basename)[0]
    new_art_fname = os.path.join(ES_ROMS_DIR, ES_MAME_PLATFORM, rom_basename_noext + art_ext)
    es_rom['image'] = new_art_fname
    if art_fname.startswith('special://profile/'):
        art_fname = art_fname.replace('special://profile/', KODI_USERDATA_DIR)
    print('Art {}'.format(art_basename))
    copy_file_if_new(art_fname, new_art_fname)
    Files_set.add(new_art_fname)

    # Only add ROM if not a BIOS, etc.
    # Not need for a machine filter, the filter is done manually in AML.
    es_gamelist_dic[ES_MAME_PLATFORM].append(es_rom)

# Clean unknown files in destination directories.
print(C_RED + 'Cleaning files and empty dirs in "{}"'.format(ES_ROMS_DIR) + C_END)
clean_unknown_files(ES_ROMS_DIR, Files_set)

# Generate es_systems.cfg.
print(C_RED + 'Generating es_systems.cfg' + C_END)
o_sl = []
o_sl.append('<!-- Generated automatically, do not edit! -->')
o_sl.append('<systemList>')
for system in es_systems_list:
    # print('Processing system {}'.format(system['name']))
    # print('Extension list {}'.format(unicode(system['extension_list'])))
    o_sl.append('<system>')
    o_sl.append(XML_text('name', system['name']))
    o_sl.append(XML_text('fullname', system['fullname']))
    o_sl.append(XML_text('path', system['path']))
    o_sl.append(XML_text('extension', ' '.join(system['extension_list'])))
    o_sl.append(XML_text('command', system['command']))
    o_sl.append(XML_text('platform', system['platform']))
    o_sl.append(XML_text('theme', system['theme']))
    o_sl.append('</system>')
o_sl.append('</systemList>\n')
es_systems_fname = os.path.join(ES_CONFIG_DIR, 'es_systems.cfg')
print('Writing file {}'.format(es_systems_fname))
with open(es_systems_fname, 'w') as file_obj:
    file_obj.write('\n'.join(o_sl).encode('utf-8'))

# Generate gamelist.xml, one per platform.
for es_platform, gamelist in es_gamelist_dic.iteritems():
    print(C_RED + 'Generating gamelist.xml for system {}'.format(es_platform) + C_END)
    o_sl = []
    o_sl.append('<!-- Generated automatically, do not edit! -->')
    o_sl.append('<gameList>')
    for es_rom in es_gamelist_dic[es_platform]:
        o_sl.append('<game>')
        o_sl.append(XML_text('name', es_rom['name']))
        o_sl.append(XML_text('desc', es_rom['desc']))
        o_sl.append(XML_text('releasedate', es_rom['releasedate']))
        o_sl.append(XML_text('developer', es_rom['developer']))
        o_sl.append(XML_text('publisher', es_rom['publisher']))
        o_sl.append(XML_text('genre', es_rom['genre']))
        o_sl.append(XML_text('players', es_rom['players']))
        o_sl.append(XML_text('path', es_rom['path']))
        o_sl.append(XML_text('image', es_rom['image']))
        o_sl.append('</game>')
    o_sl.append('</gameList>')
    es_gamelist_dir = os.path.join(ES_CONFIG_DIR, 'gamelists', es_platform)
    es_gamelist_fname = os.path.join(es_gamelist_dir, 'gamelist.xml')
    # print('Gamelist dir {}'.format(es_gamelist_dir))
    # print('Writing file {}'.format(es_gamelist_fname))
    if not os.path.exists(es_gamelist_dir): os.makedirs(es_gamelist_dir)
    with open(es_gamelist_fname, 'w') as file_obj:
        file_obj.write('\n'.join(o_sl).encode('utf-8'))
print(C_RED + 'Finished.' + C_END)
