#!/usr/bin/python -B
# -*- coding: utf-8 -*-

# Converts an AEL ROM Collection into EmulationStation databases.
# It copies the collection ROMs to a new location.
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
import shutil
import sys
import xml.etree.ElementTree

# --- Configuration ------------------------------------------------------------------------------
AEL_COLLECTION_NAME = 'EmulationStation'
AEL_ROM_ARTWORK_FIELD = 's_3dbox'
RETROARCH_PATH = '/home/kodi/bin/retroarch'
LIBRETRO_PATH = '/home/kodi/bin/libretro/'
KODI_USERDATA_DIR = '/home/kodi/.kodi/userdata/'
AEL_DATA_DIR = '/home/kodi/.kodi/userdata/addon_data/plugin.program.advanced.emulator.launcher/'
ES_ROMS_DIR = '/home/kodi/EmulationStation-ROMs/'
ES_CONFIG_DIR = '/home/kodi/.emulationstation/'

# Aborts program if platform cannot be converted, for example, the Unknown platform.
# ES platform names https://github.com/RetroPie/es-theme-carbon
def AEL_to_ES_platform(platform):
    AEL_to_ES_platform = {
        'NEC PC Engine' : ('pcengine', 'PC Engine', 'mednafen_pce_fast_libretro.so'),

        'Nintendo NES' : ('nes', 'Nintendo Entertainment System', 'mesen_libretro.so'),
        'Nintendo SNES' : ('snes', 'Super Nintendo', 'snes9x_libretro.so'),

        'Sega 32X' : ('sega32x', 'Sega 32X', 'picodrive_libretro.so'),
        'Sega Mega Drive' : ('megadrive', 'Mega Drive', 'genesis_plus_gx_libretro.so'),
        'Sega Master System' : ('mastersystem', 'Master System', 'genesis_plus_gx_libretro.so'),

        'Sony PlayStation' :  ('psx', 'PlayStation', 'mednafen_psx_libretro.so'),
    }

    return AEL_to_ES_platform[platform]

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

# --- Main ---------------------------------------------------------------------------------------
print('Converting AEL Collection {} to ES database'.format(AEL_COLLECTION_NAME))

# Open AEL collection index.
collection_fname = os.path.join(AEL_DATA_DIR, 'collections.xml')
collections, collections_idx = read_Collection_XML(collection_fname)
if AEL_COLLECTION_NAME not in collections_idx:
    print('Collection {} not found. Exiting.'.format(AEL_COLLECTION_NAME))
    sys.exit(1)
collection_dic = collections[collections_idx[AEL_COLLECTION_NAME]]

# Open collection ROMs DB.
roms_base_noext = collection_dic['roms_base_noext']
collection_ROMs_fname = os.path.join(AEL_DATA_DIR, 'db_Collections' + '/' + roms_base_noext + '.json')
roms = read_Collection_ROMs_JSON(collection_ROMs_fname)

# Traverse ROMs, copy ROM files and artwork.
es_systems_list = [] # List of new_system_dic() dictionaries.
es_systems_idx = {} # Key platform, value index in es_systems_list
es_gamelist_dic = {} # Key system name, value list of dictionaries new_game_dic().
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
        'releasedate' : '',
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
    rom_fname = rom['filename']
    rom_basename = os.path.basename(rom_fname)
    new_rom_fname = os.path.join(ES_ROMS_DIR, es_platform, rom_basename)
    new_rom_dir = os.path.dirname(new_rom_fname)
    es_rom['path'] = new_rom_fname
    print('\n ROM {}'.format(rom_basename))
    print('Copy {}'.format(rom_fname))
    print('  to {}'.format(new_rom_fname))
    if not os.path.exists(new_rom_dir): os.makedirs(new_rom_dir)
    shutil.copy(rom_fname, new_rom_fname)

    # Copy ROM artwork file. Artwork must have same name as ROM (but different extension).
    art_fname = rom[AEL_ROM_ARTWORK_FIELD]
    art_basename = os.path.basename(art_fname)
    art_ext = os.path.splitext(art_fname)[1]
    rom_basename_noext = os.path.splitext(rom_basename)[0]
    new_art_fname = os.path.join(ES_ROMS_DIR, es_platform, rom_basename_noext + art_ext)
    es_rom['image'] = new_art_fname
    if art_fname.startswith('special://profile/'):
        art_fname = art_fname.replace('special://profile/', KODI_USERDATA_DIR)
    print(' Art {}'.format(art_basename))
    print('Copy {}'.format(art_fname))
    print('  to {}'.format(new_art_fname))
    shutil.copy(art_fname, new_art_fname)

# Generate es_systems.cfg.
print('\nGenerating es_systems.cfg')
o_sl = []
o_sl.append('<!-- Generated automatically, do not edit! -->')
o_sl.append('<systemList>')
for system in es_systems_list:
    print('Processing system {}'.format(system['name']))
    print('Extension list {}'.format(unicode(system['extension_list'])))
    o_sl.append('<system>')
    o_sl.append(XML_text('name', system['name']))
    o_sl.append(XML_text('fullname', system['fullname']))
    o_sl.append(XML_text('path', system['path']))
    o_sl.append(XML_text('extension', ' '.join(system['extension_list'])))
    o_sl.append(XML_text('command', system['command']))
    o_sl.append(XML_text('platform', system['platform']))
    o_sl.append(XML_text('theme', system['theme']))
    o_sl.append('</system>')
o_sl.append('</systemList>')
es_systems_fname = os.path.join(ES_CONFIG_DIR, 'es_systems.cfg')
print('Writing file {}'.format(es_systems_fname))
with open(es_systems_fname, 'w') as file_obj:
    file_obj.write('\n'.join(o_sl).encode('utf-8'))

# Generate gamelist.xml, one per platform.
for es_platform, gamelist in es_gamelist_dic.iteritems():
    print('\nGenerating gamelist.xml for system {}'.format(es_platform))
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
    print('Gamelist dir {}'.format(es_gamelist_dir))
    print('Writing file {}'.format(es_gamelist_fname))
    if not os.path.exists(es_gamelist_dir): os.makedirs(es_gamelist_dir)
    with open(es_gamelist_fname, 'w') as file_obj:
        file_obj.write('\n'.join(o_sl).encode('utf-8'))
print('Finished.')
