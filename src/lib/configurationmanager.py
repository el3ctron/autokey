
# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

#import os.path, ConfigParser
import os.path, configobj, gtk
import cPickle as pickle

CONFIG_FILE = "../../config/autokey.bin"

DEFAULT_ABBR_FOLDER = "Abbreviations"

def get_config_manager():
    if os.path.exists(CONFIG_FILE):
        pFile = open(CONFIG_FILE, 'r')
        config = pickle.load(pFile)
        pFile.close()
        return config
    else:
        return ConfigurationManager()

class ConfigurationManager:

    # Static members for global application settings ----
    isFirstRun = True
    serviceRunning = False
    menuTakesFocus = True
    showTrayIcon = True
    sortByUsageCount = True
    predictiveLength = 5
    
    def __init__(self):
        """
        Create initial default configuration
        """    
        self.folders = {}
        #self.folders[DEFAULT_ABBR_FOLDER] = PhraseFolder(DEFAULT_ABBR_FOLDER)
                
        # TODO TESTING REMOVE ME LATER
        from iomediator import Key
        myPhrases = PhraseFolder("My Phrases")
        myPhrases.set_hotkey([Key.CONTROL], '<f7>')
        myPhrases.set_modes([PhraseMode.HOTKEY])

        p = Phrase("First phrase", "Test phrase number one!")
        p.set_modes([PhraseMode.PREDICTIVE])
        p.prompt = True
        p.set_window_titles(".* - gedit")
        myPhrases.add_phrase(p)
        
        p1 = Phrase("Positioning Phrase", "[udc]%%[/udc]\nBlah")
        p1.set_modes([PhraseMode.ABBREVIATION, PhraseMode.HOTKEY])
        p1.set_hotkey([Key.CONTROL], 'j')
        p1.set_abbreviation("udc")
        p1.showInTrayMenu = True
        p1.immediate = True
        myPhrases.add_phrase(p1)
        
        myPhrases.add_phrase(Phrase("Second phrase", "Test phrase number two!"))
        myPhrases.add_phrase(Phrase("Third phrase", "Test phrase number three!"))
        self.folders[myPhrases.title] = myPhrases
        
        trayPhrases = PhraseFolder("Tray Phrases", showInTrayMenu=True)
        trayPhrases.add_phrase(Phrase("First phrase", "Test phrase number one!"))
        trayPhrases.add_phrase(Phrase("Second phrase", "Test phrase number two!"))
        trayPhrases.add_phrase(Phrase("Third phrase", "Test phrase number three!"))
        self.folders[trayPhrases.title] = trayPhrases
        
        self.config_altered()
            
    def config_altered(self):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders. 
        """
        self.hotKeyFolders = []
        self.hotKeyPhrases = []
        
        self.abbrPhrases = []
        
        self.allFolders = []
        self.allPhrases = []
        
        for folder in self.folders.values():
            if PhraseMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            self.__processFolder(folder)
                    
    def __processFolder(self, folder):
        for folder in folder.folders.values():
            if PhraseMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            self.__processFolder(folder)
            
        for phrase in folder.phrases.values():
            if PhraseMode.HOTKEY in phrase.modes:
                self.hotKeyPhrases.append(phrase)
            if PhraseMode.ABBREVIATION in phrase.modes:
                self.abbrPhrases.append(phrase)
            self.allPhrases.append(phrase)

        
    def import_legacy_settings(self, configFilePath):
        importer = LegacyImporter()
        importer.load_config(configFilePath)
        newRow = False
        # TODO import exception
        
        # Check that default Abbreviations folder exists
        if not self.folders.has_key(DEFAULT_ABBR_FOLDER):
            self.folders[DEFAULT_ABBR_FOLDER] = PhraseFolder(DEFAULT_ABBR_FOLDER)
            newRow = True
            
        folder = self.folders[DEFAULT_ABBR_FOLDER]
        #for phrase in importer.phrases:
        #    folder.add_phrase(phrase)
        
        return (newRow, folder, importer.phrases)
    
    def check_abbreviation_unique(self, abbr):
        """
        Checks that the given abbreviation is not already in use.
        """
        for item in self.allFolders:
            if PhraseMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbr:
                    return False
            
        for item in self.allPhrases:
            if PhraseMode.ABBREVIATION in item.modes:
                if item.abbrevation == abbr:
                    return False
            
        return True
            
    def check_hotkey_unique(self, modifiers, key):
        """
        Checks that the given hotkey is not already in use.
        """
        modifiers.sort()
        
        for item in self.allFolders:
            if PhraseMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == key:
                    return False
            
        for item in self.allPhrases:
            if PhraseMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == key:
                    return False        

        return True

# Legacy Importer ----

# Legacy configuration sections
CONFIG_SECTION = "config"
DEFAULTS_SECTION = "defaults"
ABBR_SECTION = "abbr"

# Legacy configuration parameters

WORD_CHARS_REGEX_OPTION = "wordchars"
IMMEDIATE_OPTION = "immediate"
IGNORE_CASE_OPTION = "ignorecase"
MATCH_CASE_OPTION = "matchcase"
BACKSPACE_OPTION = "backspace"
OMIT_TRIGGER_OPTION = "omittrigger"
TRIGGER_INSIDE_OPTION = "triggerinside"

ABBREVIATION_OPTIONS = [
                        WORD_CHARS_REGEX_OPTION,
                        IMMEDIATE_OPTION,
                        IGNORE_CASE_OPTION,
                        MATCH_CASE_OPTION,
                        BACKSPACE_OPTION,
                        OMIT_TRIGGER_OPTION,
                        TRIGGER_INSIDE_OPTION
                        ]

class LegacyImporter:
    
    def load_config(self, configFilePath):
        # TODO catch exceptions and throw import exception
        #p = ConfigParser.ConfigParser()
        #p.read([configFilePath])
        #abbrDefinitions = dict(p.items(ABBR_SECTION))
        
        config = configobj.ConfigObj(configFilePath, list_values=False)
        abbrDefinitions = config[ABBR_SECTION]
        
        definitions = abbrDefinitions.keys()
        definitions.sort()        

        # Import default settings
        #defaultSettings = dict(p.items(DEFAULTS_SECTION))
        defaultSettings = config[DEFAULTS_SECTION]
        defaultSettings[WORD_CHARS_REGEX_OPTION] = re.compile(defaultSettings[WORD_CHARS_REGEX_OPTION], re.UNICODE)
        
        self.__applyBooleanOption(IMMEDIATE_OPTION, defaultSettings)        
        self.__applyBooleanOption(IGNORE_CASE_OPTION, defaultSettings)
        self.__applyBooleanOption(MATCH_CASE_OPTION, defaultSettings)   
        self.__applyBooleanOption(BACKSPACE_OPTION, defaultSettings)    
        self.__applyBooleanOption(OMIT_TRIGGER_OPTION, defaultSettings)
        self.__applyBooleanOption(TRIGGER_INSIDE_OPTION, defaultSettings)        
        
        # Import user-defined abbreviations as phrases        
        self.phrases = []
        
        while len(definitions) > 0:

            # Flush any unused options that weren't matched with an abbreviation definition
            while '.' in definitions[0]:
                isOption = False
                for option in ABBREVIATION_OPTIONS:
                    if definitions[0].endswith(option):
                        definitions.pop(0)
                        isOption = True
                        break

                if len(definitions) == 0:
                    break # leave the flushing loop if no definitions remaining
                if len(definitions) == 1 and not isOption:
                    break # leave the flushing loop if the last remaining definition is not an option
                    

            if len(definitions) > 0:
                self.phrases.append(self.__buildPhrase(definitions, abbrDefinitions, defaultSettings))                 

    def __buildPhrase(self, definitions, abbrDefinitions, defaults):
        """
        Create a new Phrase instance for the abbreviation definition at the start of the list
        
        @param definitions: list of definitions yet to be processed, with the abbreviation definition
        to be instantiated at the start of the list
        @param abbrDefinitions: dictionary of all abbreviation and config definitions
        """
        ownSettings = {}
        definition = definitions.pop(0)
        phraseText = abbrDefinitions[definition]
        startString = definition + '.'
        offset = len(startString)

        while len(definitions) > 0:
            key = definitions[0]
            if key.startswith(startString):
                ownSettings[key[offset:]] = abbrDefinitions[key]
                definitions.pop(0)
            else:
                # no more options for me - leave loop
                break
        
        if ownSettings.has_key(WORD_CHARS_REGEX_OPTION):
            ownSettings[WORD_CHARS_REGEX_OPTION] = re.compile(ownSettings[WORD_CHARS_REGEX_OPTION], re.UNICODE)
        
        self.__applyBooleanOption(IMMEDIATE_OPTION, ownSettings)        
        self.__applyBooleanOption(IGNORE_CASE_OPTION, ownSettings)
        self.__applyBooleanOption(MATCH_CASE_OPTION, ownSettings)   
        self.__applyBooleanOption(BACKSPACE_OPTION, ownSettings)    
        self.__applyBooleanOption(OMIT_TRIGGER_OPTION, ownSettings)
        self.__applyBooleanOption(TRIGGER_INSIDE_OPTION, ownSettings)
        
        #if result._getSetting(IGNORE_CASE_OPTION):
        #    result.abbreviation = result.abbreviation.lower()
        
        # Apply options to final phrase
        phraseDescription = phraseText[:20].replace('\n', ' ')
        result = Phrase(phraseDescription, phraseText)
        result.set_abbreviation(definition)
        result.set_modes([PhraseMode.ABBREVIATION])
        result.wordChars = self.__getDefaultOrCustom(defaults, ownSettings, WORD_CHARS_REGEX_OPTION)
        result.immediate = self.__getDefaultOrCustom(defaults, ownSettings, IMMEDIATE_OPTION)
        result.ignoreCase = self.__getDefaultOrCustom(defaults, ownSettings, IGNORE_CASE_OPTION)
        result.matchCase = self.__getDefaultOrCustom(defaults, ownSettings, MATCH_CASE_OPTION)
        result.backspace = self.__getDefaultOrCustom(defaults, ownSettings, BACKSPACE_OPTION)
        result.omitTrigger = self.__getDefaultOrCustom(defaults, ownSettings, OMIT_TRIGGER_OPTION)
        result.triggerInside = self.__getDefaultOrCustom(defaults, ownSettings, TRIGGER_INSIDE_OPTION)
        return result
            
    def __applyBooleanOption(self, optionName, settings):
        if settings.has_key(optionName):
            settings[optionName] = (settings[optionName].lower()[0] == 't')
            
    def __getDefaultOrCustom(self, defaults, ownSettings, optionName):
        if ownSettings.has_key(optionName):
            return ownSettings[optionName]
        else:
            return defaults[optionName]

from phrase import *