# -*- coding: UTF-8 -*-
#A part of the SentenceNav addon for NVDA
#Copyright (C) 2018-2019 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import bisect
import braille
import config
import controlTypes
import ctypes
import globalPluginHandler
import gui
import json
import NVDAHelper
from NVDAObjects.window import winword
import operator
import re
import review
import sayAllHandler
import vision
from scriptHandler import script, willSayAllResume
import speech
import struct
import textInfos
import tones
import ui
import wx

debug = False
if debug:
    f = open("C:\\Users\\tony\\Dropbox\\1.txt", "w", encoding="utf-8")
def mylog(s):
    if debug:
        print(str(s), file=f)
        f.flush()

def myAssert(condition):
    if not condition:
        raise RuntimeError("Assertion failed")

def initConfiguration():
    exceptionalAbbreviations = """
{
    "en": "Mr Ms Mrs Dr St e.g",
    "ru": "Тов тов"
}
""".replace("\n", " ")
    capitalLetters = """
{
    "en": "A-Z",
    "ru": "А-Я"
}
""".replace("\n", " ")
    lowerCaseLetters = """
{
    "en": "a-z",
    "ru": "а-я"
}
""".replace("\n", " ")
    confspec = {
        "paragraphChimeVolume" : "integer( default=5, min=0, max=100)",
        "noNextSentenceChimeVolume" : "integer( default=50, min=0, max=100)",
        "noNextSentenceMessage" : "boolean( default=False)",
        "speakFormatted" : "boolean( default=True)",
        "reconstructMode" : "string( default='sameIndent')",
        "breakOnWikiReferences" : "boolean( default=True)",
        "sentenceBreakers" : "string( default='.!?')",
        "fullWidthSentenceBreakers" : "string( default='。！？')",
        "skippable" : "string( default='\"”’»)')",
        "exceptionalAbbreviations" : "string( default='%s')" % exceptionalAbbreviations,
        "capitalLetters" : "string( default='%s')" % capitalLetters,
        "lowerCaseLetters" : "string( default='%s')" % lowerCaseLetters,
        "phraseBreakers" : "string( default='.!?,;:-–()')",
        "fullWidthPhraseBreakers" : "string( default='。！？，；：（）')",
        "applicationsBlacklist" : "string( default='audacity,excel')",
        "enableInWord" : "boolean( default=False)",
    }
    config.conf.spec["sentencenav"] = confspec

def getConfig(key, lang=None):
    value = config.conf["sentencenav"][key]
    if lang is None:
        return value
    dictionary = json.loads(value)
    try:
        return dictionary[lang]
    except KeyError:
        return dictionary["en"]

def setConfig(key, value, lang):
    fullValue = config.conf["sentencenav"][key]
    dictionary = json.loads(fullValue)
    dictionary[lang] = value
    config.conf["sentencenav"][key] = json.dumps(dictionary)

def getCurrentLanguage():
    s = speech.getCurrentLanguage()
    return s[:2]

addonHandler.initTranslation()
initConfiguration()

class SettingsDialog(gui.SettingsDialog):
    # Translators: Title for the settings dialog
    title = _("SentenceNav settings")

    reconstructOptions = ["always", "sameIndent", "never"]
    # Translators: choices inside reconstruct mode combo box
    reconstructOptionsText = [_("Always"), _("Only across paragraphs with same indentation and same style level"), _("Never")]

    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
      # paragraphChimeVolumeSlider
        sizer=wx.BoxSizer(wx.HORIZONTAL)
        # Translators: Paragraph crossing chime volume
        label=wx.StaticText(self,wx.ID_ANY,label=_("Volume of chime when crossing paragraph border"))
        slider=wx.Slider(self, wx.NewId(), minValue=0,maxValue=100)
        slider.SetValue(config.conf["sentencenav"]["paragraphChimeVolume"])
        sizer.Add(label)
        sizer.Add(slider)
        settingsSizer.Add(sizer)
        self.paragraphChimeVolumeSlider = slider

      # noNextSentenceChimeVolumeSlider
        sizer=wx.BoxSizer(wx.HORIZONTAL)
        # Translators: End of document chime volume
        label=wx.StaticText(self,wx.ID_ANY,label=_("Volume of chime when no more sentences available"))
        slider=wx.Slider(self, wx.NewId(), minValue=0,maxValue=100)
        slider.SetValue(config.conf["sentencenav"]["noNextSentenceChimeVolume"])
        sizer.Add(label)
        sizer.Add(slider)
        settingsSizer.Add(sizer)
        self.noNextSentenceChimeVolumeSlider = slider

      # Checkboxes
        # Translators: Checkbox that controls spoken message when no next or previous sentence is available in the document
        label = _("Speak message when no next sentence available in the document")
        self.noNextSentenceMessageCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.noNextSentenceMessageCheckbox.Value = getConfig("noNextSentenceMessage")
        # Translators: speak formatted text checkbox
        label = _("Speak formatted text")
        self.speakFormattedCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.speakFormattedCheckbox.Value = getConfig("speakFormatted")

      # Reconstruct mode Combo box
        # Translators: Label for reconstruct mode combo box
        label = _("Reconstruct sentences across multiple paragraphs when")
        self.reconstructModeCombobox = sHelper.addLabeledControl(label, wx.Choice, choices=self.reconstructOptionsText)
        index = self.reconstructOptions.index(str(getConfig("reconstructMode")))
        self.reconstructModeCombobox.Selection = index

      # Regex-related checkbox
        # Translators: Checkbox that controls whether we should take wiki references into account when parsing sentences
        label = _("Take Wikipedia-style references into account")
        self.breakOnWikiReferencesCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.breakOnWikiReferencesCheckbox.Value = getConfig("breakOnWikiReferences")

      # Regex-related edit boxes
        # Translators: Label for sentence breakers edit box
        self.sentenceBreakersEdit = gui.guiHelper.LabeledControlHelper(self, _("Sentence breakers"), wx.TextCtrl).control
        self.sentenceBreakersEdit.Value = getConfig("sentenceBreakers")
        # Translators: Label for skippable punctuation marks edit box
        self.skippableEdit = gui.guiHelper.LabeledControlHelper(self, _("Skippable punctuation marks"), wx.TextCtrl).control
        self.skippableEdit.Value = getConfig("skippable")
        # Translators: Label for full width sentence breakers edit box
        self.fullWidthSentenceBreakersEdit = gui.guiHelper.LabeledControlHelper(self, _("Full width sentence breakers"), wx.TextCtrl).control
        self.fullWidthSentenceBreakersEdit.Value = getConfig("fullWidthSentenceBreakers")

      # Regex-related language-specific edit boxes
        lang = self.lang = getCurrentLanguage()
      # Translators: Label for exceptional abbreviations edit box
        label = _("Exceptional abbreviations, space separated, in language %s") % lang
        self.exceptionalAbbreviationsEdit = gui.guiHelper.LabeledControlHelper(self, label, wx.TextCtrl).control
        self.exceptionalAbbreviationsEdit.Value = getConfig("exceptionalAbbreviations", lang)
      # Translators: Label for capital letters edit box
        label = _("Capital letters with no spaces in language %s") % lang
        self.capitalLettersEdit = gui.guiHelper.LabeledControlHelper(self, label, wx.TextCtrl).control
        self.capitalLettersEdit.Value = getConfig("capitalLetters", lang)
      # Translators: Label for lower case letters edit box
        label = _("Lower case letters with no spaces in language %s") % lang
        self.lowerCaseLettersEdit = gui.guiHelper.LabeledControlHelper(self, label, wx.TextCtrl).control
        self.lowerCaseLettersEdit.Value = getConfig("lowerCaseLetters", lang)

      # Phrase regex-related edit boxes
        # Translators: Label for phrase breakers edit box
        self.phraseBreakersEdit = gui.guiHelper.LabeledControlHelper(self, _("Phrase breakers"), wx.TextCtrl).control
        self.phraseBreakersEdit.Value = getConfig("phraseBreakers")
        # Translators: Label for full width phrase breakers edit box
        self.fullWidthPhraseBreakersEdit = gui.guiHelper.LabeledControlHelper(self, _("Full width phrase breakers"), wx.TextCtrl).control
        self.fullWidthPhraseBreakersEdit.Value = getConfig("fullWidthPhraseBreakers")
      # applicationsBlacklist edit
        # Translators: Label for blacklisted applications edit box
        self.applicationsBlacklistEdit = gui.guiHelper.LabeledControlHelper(self, _("Disable SentenceNav in applications (comma-separated list)"), wx.TextCtrl).control
        self.applicationsBlacklistEdit.Value = getConfig("applicationsBlacklist")
      # Enable in MS Word
        # Translators: Checkbox that enables support for MS Word
        label = _("Enable experimental support for Microsoft Word and WordPad (overrides default NVDA functionality)")
        self.enableInWordCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.enableInWordCheckbox.Value = getConfig("enableInWord")



    def onOk(self, evt):
        config.conf["sentencenav"]["paragraphChimeVolume"] = self.paragraphChimeVolumeSlider.Value
        config.conf["sentencenav"]["noNextSentenceChimeVolume"] = self.noNextSentenceChimeVolumeSlider.Value
        config.conf["sentencenav"]["noNextSentenceMessage"] = self.noNextSentenceMessageCheckbox.Value
        config.conf["sentencenav"]["speakFormatted"] = self.speakFormattedCheckbox.Value
        config.conf["sentencenav"]["reconstructMode"] = self.reconstructOptions[self.reconstructModeCombobox.Selection]
        config.conf["sentencenav"]["breakOnWikiReferences"] = self.breakOnWikiReferencesCheckbox.Value
        config.conf["sentencenav"]["sentenceBreakers"] = self.sentenceBreakersEdit.Value
        config.conf["sentencenav"]["skippable"] = self.skippableEdit.Value
        config.conf["sentencenav"]["fullWidthSentenceBreakers"] = self.fullWidthSentenceBreakersEdit.Value
        setConfig("exceptionalAbbreviations", self.exceptionalAbbreviationsEdit.Value, self.lang)
        setConfig("capitalLetters", self.capitalLettersEdit.Value, self.lang)
        setConfig("lowerCaseLetters", self.lowerCaseLettersEdit.Value, self.lang)
        config.conf["sentencenav"]["phraseBreakers"] = self.phraseBreakersEdit.Value
        config.conf["sentencenav"]["fullWidthPhraseBreakers"] = self.fullWidthPhraseBreakersEdit.Value
        config.conf["sentencenav"]["applicationsBlacklist"] = self.applicationsBlacklistEdit.Value
        config.conf["sentencenav"]["enableInWord"] = self.enableInWordCheckbox.Value

        regexCache.clear()
        phraseRegex = None
        super(SettingsDialog, self).onOk(evt)


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
def countCharacters(textInfo):
    '''Counts the number of characters in this TextInfo.
    There is no good unified way to do so in NVDA,
    so try every possible trick in the book.
    This function is only guaranteed to work if textInfo is contained within a single paragraph.'''
    try:
        # This used to work for offset-based TextInfos
        # Probably migration to Python 3 broke the way it works with unicode characters, since now it looks at byte offsets, and every unicode character increases the offset by 2.
        #return textInfo._endOffset - textInfo._startOffset
        # Well, let's try an alternative:
        return len(textInfo.text)
    except AttributeError:
        pass
    try:
        # This works for some CompoundTextInfos, like in LibreOffice Writer
        myAssert(len(list(textInfo._getTextInfos())) == 1)
        return countCharacters(list(textInfo._getTextInfos())[0])
    except AttributeError:
        pass
    try:
        # This works in edit control in Mozilla Thunderbird
        myAssert(textInfo._start == textInfo._end)
        return countCharacters(textInfo._start)
    except AttributeError:
        pass
    raise RuntimeError("Unable to count characters for %s" % str(textInfo))

def getCaretIndexWithinParagraph(caretTextInfo):
    paragraphTextInfo = caretTextInfo.copy()
    paragraphTextInfo.expand(textInfos.UNIT_PARAGRAPH)
    preInfo = paragraphTextInfo.copy()
    preInfo.setEndPoint(caretTextInfo, "endToStart")
    # For optimization return paragraphTextInfo, since it will be needed later
    return (countCharacters(preInfo), paragraphTextInfo)

def preprocessNewLines(s):
    s = s.replace("\r\n", "\n") # Fix for Notepad++
    s = s.replace("\r", "\n") # Fix for AkelPad
    return s.replace("\n", " ")

class Context:
    def __init__(self, textInfo, caretIndex, caretInfo=None):
        self.texts = [preprocessNewLines(textInfo.text)]
        self.textInfos = [textInfo]
        self.caretIndex = caretIndex # Caret index within current paragraph, zero-based
        self.caretInfo = caretInfo # collapsed textInfo representing caret
        self.current = 0 # Index of current paragraph
    def addParagraph(self, index, textInfo):
        mylog(f"Inserting new para at index={index}")
        mylog(f"Before texts={self.texts}")
        if index >= 0:
            self.textInfos.insert(index, textInfo)
            self.texts.insert(index, preprocessNewLines(textInfo.text))
        else:
            self.textInfos.append(textInfo)
            self.texts.append(preprocessNewLines(textInfo.text))
        mylog(f"texts={self.texts}")
        if (index >= 0) and (self.current >= index):
            self.current += 1

    def makeTextInfo(self, paragraphInfo, offset):
        index = self.textInfos.index(paragraphInfo)
        if index != self.current or self.caretInfo is None:
            mylog(f"Plain MakeTextInfo: moving by {offset}")
            info = paragraphInfo.copy()
            text = self.texts[index]
            if len(text) == offset:
                # We need to move to the very end. However some textInfos won't allow us
                # to do so, e.g. Thunderbird. Besides it would be slow anyway.
                # So try to collapse to the end instead.
                info.collapse(end=True)
                mylog("Collapsed to the end since offset={offset} = len(text)!")
                return info
            mylog(f"{info._startOffset}")
            info.collapse()
            mylog(f"{info._startOffset}")
            result = info.move(textInfos.UNIT_CHARACTER, offset)
            if (offset > 0) and (result == 0):
                raise Exception("Unexpected! Failed to move!")
            mylog(f"{info._startOffset}")
            return info
        # optimization: if we are in our current paragraph, compute off of caret textInfo
        mylog(f"Optimized MakeTextInfo: moving by {offset} - {self.caretIndex}")
        info = self.caretInfo.copy()
        info.move(textInfos.UNIT_CHARACTER, offset - self.caretIndex)
        return info

    def makeSentenceInfo(self, startTi, startOffset, endTi, endOffset):
        start = self.makeTextInfo(startTi, startOffset)
        mylog(f"start._startOffset={start._startOffset}")
        end = self.makeTextInfo(endTi, endOffset)
        mylog(f"end._startOffset={end._startOffset}")
        start.setEndPoint(end, "endToEnd")
        mylog(f"start._startOffset={start._startOffset} start._endOffset={start._endOffset}")
        return start

    def isTouchingBoundary(self,direction, startTi, startOffset, endTi, endOffset):
        # When moving forward we need to compare if the end of the sentence coincides with the end of the context.
        # If this is the case, we might want to expand context, just to check whetehr the sentence might continue in the next paragraph.
        # Or similarly, when moving backward, comparing to the beginning of the context.
        if debug:
            mylog(f"isTouchingBoundary({startOffset}, {endOffset})")
            mylog(f"startTi: {startTi.text}")
            mylog(f"endTi: {endTi.text}")
            c1 = endTi == self.textInfos[-1]
            c2 =  endOffset == len(self.texts[-1])
            c3 = startTi == self.textInfos[0]
            c4 =  startOffset == 0
            mylog(f"{c1} {c2} {c3} {c4}")
        if (
            (
                direction > 0
                and  (
                    endTi == self.textInfos[-1]
                    and endOffset == len(self.texts[-1])
                )
            ) or (
                direction < 0
                and  (
                    startTi == self.textInfos[0]
                    and startOffset == 0
                )
            )
        ):
            mylog(f"isTouchingBoundary=True!")
            return True
        else:
            mylog(f"isTouchingBoundary=False!")
            return False
            
    def findByOffset(self, paragraphInfo, offset):
        # Sets caret position according to paragraph and offset within paragraph
        index = self.textInfos.index(paragraphInfo)
        if offset < 0:
            # Special case, we would like to move back one character and so we need to jump to the previous paragraph
            if index == 0:
                raise Exception("Impossible!")
            self.current = index - 1
            self.caretIndex = len(self.texts[index-1]) - 1
            self.caretInfo = None
        else:
            self.current = index
            self.caretIndex = offset
            self.caretInfo = None

    def find(self, textInfo):
        # Finds textInfo and sets it as current caret, updating internal variables accordingly
        # textInfo must be a collapsed info!
        which="start"
        for i in range(len(self.textInfos)):
            if textInfo.compareEndPoints(self.textInfos[i], which + "ToStart") >= 0:
                if textInfo.compareEndPoints(self.textInfos[i], which + "ToEnd") < 0:
                    self.current = i
                    indexTextInfo = self.textInfos[i].copy()
                    indexTextInfo.setEndPoint(textInfo, "endTo" + which.capitalize())
                    self.caretIndex = countCharacters(indexTextInfo)
                    self.caretInfo = textInfo
                    return
        raise RuntimeError("Could not find textInfo in this context.")

    def __str__(self):
        result = ""
        for i in range(len(self.texts)):
            text = self.texts[i]
            if i == self.current:
                prefix = "@%d" % self.caretIndex
            else:
                prefix = "."
            result += "%s %s\n" % (prefix, text)
        return result

def re_grp(s):
    """Wraps a string with a non-capturing group for use in regular expressions."""
    return "(?:%s)" % s

def re_set(s, allowRanges=False):
    """Creates a regex set of characters from a plain string."""
    # Step 1: escape special characters
    for c in "\\[]":
        s = s.replace(c, "\\" + c)
    if not allowRanges:
        # Step 2. If hyphen is in the set, we need to move it to position 1.
        if "-" in s:
            s = "-" + s.replace("-", "")
    return "[" + s + "]"

def re_escape(s):
    for c in "\\.?*()[]{}$^":
        s = s.replace(c, "\\" + c)
    return s


def nlb(s):
    """Forms a negative look-behind regexp clause to prevent certain expressions like "Mr." from ending the sentence.
    It also adds a positive look-ahead to make sure that such an expression is followed by a period, as opposed to
    other sentence breakers, such as question or exclamation mark."""
    return u"(?<!" + s + u"(?=[.]))"
def nla(s):
    """Forms a negative look-ahead regexp clause to prevent for example lower-case letters."""
    return f"(?!{s})"

regexCache = {}

def getRegex(lang):
    # Description of end of sentence regular expression in human language:
    # End of sentence regular expression SENTENCE_END_REGEX  matches either:
    # 1. Beginning or end of the string.
    # 2.Sentence breaker punctuation marks (such as period, question or exclamation mark) SENTENCE_BREAKERS  (one or more), that is both:
    # 2.1. Followed by all of:
    # 2.1.1. Optionally skippable punctuation marks (such as closing right bracket or right double quote mark) SKIPPABLE_PUNCTUATION (zero or more)
    # 2.1.2.Optionally Wikipedia-style reference (such as [1], or [Citation Needed]) WIKIPEDIA_REFERENCE  (zero or more)
    # 2.1.3. One or more whitespaces or whitespace-like characters \\s
    # 2.2. And (defined in LOOK_BEHIND ) not preceded by:
    # 2.2.1. Common abbreviations (defined in ABBREVIATIONS ), such as Mr., Ms., Dr., etc, followed by period.
    # 2.2.2. Single letter abbreviations (defined in CAPITAL_LETTERS ), such as initials, followed by a period.
    # 3. Wide character punctuation marks (defined in CHINESE_SENTENCE_BREAKERS)
    # 4. Two or more newline characters in a row, optionally followed by any amount of whitespaces.
    # One additional condition is that if the separator is period, then
    # we check that it is not followed by a few spaces and then a lower case letter.

    try:
        return regexCache[lang]
    except KeyError:
        pass
    regex = u""
    regex += nlb("\\b" + re_set(getConfig("capitalLetters", lang), allowRanges=True))
    for abbr in getConfig("exceptionalAbbreviations", lang).strip().split():
        regex += nlb(re_escape(abbr))        
    breakers = getConfig("sentenceBreakers")
    if "." in breakers:
        breakers = [
            breakers.replace(".", ""),
            "."
        ]
    else:
        breakers = [breakers]
    rrr = []
    for bi in range(len(breakers)):
        rr = re_set(breakers[bi]) + "+"
        rr += re_set(getConfig("skippable")) + "*"
        if getConfig("breakOnWikiReferences"):
            wikiReference = re_grp("\\[[\\w\\s]+\\]")
            rr += wikiReference + "*"
        rr += "\\s+"
        if bi == 1:
            # Here we handle lower case letters only after period as breaker
            rr += nla(re_set(getConfig("lowerCaseLetters", lang), allowRanges=True))
        rrr.append(rr)
    regex +=re_grp("|".join(rrr))
    fullWidth = re_set(getConfig("fullWidthSentenceBreakers"))
    doubleNewLine = re_grp("\n\\s*")
    doubleNewLine = "%s{2,}" % doubleNewLine
    regex = u"^|{regex}|{fullWidth}+\\s*|{doubleNewLine}|\\s*$".format(
        regex=regex,
        fullWidth=re_grp(fullWidth),
        doubleNewLine=re_grp(doubleNewLine))
    mylog("Compiling regex: " + regex)
    try:
        result = re.compile(regex , re.UNICODE)
    except:
        # Translators: message when regex compilation failed
        ui.message("Couldn't compile regular expression for sentences")
        raise
    regexCache[lang] = result
    return result


phraseRegex = None

def getPhraseRegex():
    global phraseRegex
    if phraseRegex is not None:
        return phraseRegex
    regex = u""
    regex += re_set(getConfig("phraseBreakers")) + "+"
    regex += "\\s+"
    fullWidth = re_set(getConfig("fullWidthPhraseBreakers"))
    doubleNewLine = re_grp("\n\\s*")
    doubleNewLine = "%s{2,}" % doubleNewLine
    regex = u"^|{regex}|{fullWidth}+\\s*|{doubleNewLine}|\\s*$".format(
        regex=regex,
        fullWidth=re_grp(fullWidth),
        doubleNewLine=re_grp(doubleNewLine))
    try:
        result = re.compile(regex , re.UNICODE)
    except:
        # Translators: message when regex compilation failed
        ui.message("Couldn't compile regular expression for phrases")
        raise
    phraseRegex = result
    return result

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("SentenceNav")

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.createMenu()

    def createMenu(self):
        def _popupMenu(evt):
            gui.mainFrame._popupSettingsDialog(SettingsDialog)
        self.prefsMenuItem = gui.mainFrame.sysTrayIcon.preferencesMenu.Append(wx.ID_ANY, _("SentenceNav..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, _popupMenu, self.prefsMenuItem)

    def terminate(self):
        prefMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
        try:
            if wx.version().startswith("4"):
                prefMenu.Remove(self.prefsMenuItem)
            else:
                prefMenu.RemoveItem(self.prefsMenuItem)
        except:
            pass

    def splitParagraphIntoSentences(self, text, regex=None):
        if regex is None:
            regex = self.SENTENCE_END_REGEX
        result = [m.end() for m in regex.finditer(text)]
        # Sometimes the last position in the text will be matched twice, so filter duplicates.
        result = sorted(list(set(result)))
        return result

    def findCurrentSentence(self, context, regex):
        if debug:
            mylog("findCurrentSentence\n %s" % context)
        texts = context.texts
        tis = context.textInfos
        n = len(texts)
        myAssert(n == len(tis))

        joinString = "\n"
        s = joinString.join(texts)
        mylog(f"s='{s}'")
        index = sum([len(texts[t]) for t in range(context.current)]) + len(joinString) * context.current + context.caretIndex
        parStartIndices = [0] # Denotes indices in s where new paragraphs start
        for i in range(1, n):
            parStartIndices.append(parStartIndices[i-1] + len(texts[i-1]) + len(joinString))
        boundaries = self.splitParagraphIntoSentences(s, regex=regex)
        if debug:
            mylog(f"n={n}, parStartIndices={parStartIndices}")
            mylog(f"Index={index} Boundaries: {boundaries}")
            mylog(f"[s]=[{s}]")
            mylog(f"texts={texts}")
        # Find the first index in boundaries that is strictly greater than index
        j = bisect.bisect_right(boundaries, index)
        i = j - 1
        # At this point boundaries[i] and boundaries[j] represent
        # the boundaries of the current sentence.

        if len(boundaries) == 1:
            # This must be an empty context/paragraph
            # j points to out of boundaries
            if debug:
                mylog(f"len(boundaries) == 1, therefore, must be empty context and j={j} points out of boundaries")
            t1i = bisect.bisect_right(parStartIndices, boundaries[i]) - 1
            t1 = tis[t1i]
            return (texts[t1i], t1, 0, t1, len(texts[t1i]))
        if j == len(boundaries):
            # This can happen if the cursor is at the very last position in the document
            if debug:
                mylog(f"j == len(boundaries) - This can happen if the cursor is at the very last position in the document")
            ti = tis[-1]
            #ti.collapse()
            moveDistance = boundaries[i] - parStartIndices[-1]
            #ti.move(textInfos.UNIT_CHARACTER, moveDistance)
            #ti.setEndPoint(tis[-1], "endToEnd")
            #return ("", ti)
            return ("", tis[-1], moveDistance, tis[-1], len(texts[-1]))
        sentenceStr = s[boundaries[i]:boundaries[j]]
        if debug:
            mylog(f"Current sentence: '{sentenceStr}'")

        t1i = bisect.bisect_right(parStartIndices, boundaries[i]) - 1
        t1 = tis[t1i]
        t1offset = boundaries[i] - parStartIndices[t1i]
        #t1.collapse()
        #t1.move(textInfos.UNIT_CHARACTER, boundaries[i] - parStartIndices[t1i])
        t2i = bisect.bisect_right(parStartIndices, boundaries[j]) - 1
        t2 = tis[t2i]
        t2offset = boundaries[j] - parStartIndices[t2i]
        #moveDistance = boundaries[j] - parStartIndices[t2i]
        if False:
            if moveDistance < len(texts[t2i]):
                t2.collapse()
                result = t2.move(textInfos.UNIT_CHARACTER, moveDistance)
                myAssert(result == moveDistance)
                t1.setEndPoint(t2, "endToEnd")
            elif moveDistance == len(texts[t2i]):
                # Sometimes paragraphs contain an extra invisible character.
                # We need to include it in the result textInfo, so handle this case in a special way.
                t1.setEndPoint(t2, "endToEnd")
            else:
                raise RuntimeError("Unexpected condition.")
        # Now we rturn:
        # 1. String of the sentence that we identified.
        # 2. TextInfo of the paragraph where start of the sentence happens to be
        # 3. Offset within that textInfo, pointing at the start
        # 4. TextInfo of the paragraph where end of the sentence happens to be.
        # 5. offset in that textInfo pointing at the end.
        return (sentenceStr, t1, t1offset, t2, t2offset)

    def nextParagraph(self, textInfo, direction):
        mylog(f"nextParagraph direction={direction}")
        ti = textInfo.copy()
        # For some TextInfo implementations, such as edit control in Thunderbird we need to try twice:
        for i in [1,2]:
            mylog(f"nextParagraph i={i}")
            ti.collapse()
            result = ti.move(textInfos.UNIT_PARAGRAPH, direction)
            if result == 0:
                mylog(f"nextParagraph result == 0")
                return None
            ti.expand(textInfos.UNIT_PARAGRAPH)
            if sign(ti.compareEndPoints(textInfo, "startToStart")) == sign(direction):
                mylog(f"NextPara compare end points successful!")
                return ti
        mylog(f"nextParagraph failed after two loops.")
        return None

    def expandSentence(self, context, regex, direction, compatibilityFunc=None):
        if direction == 0:
            # Expand both forward and backward
            self.expandSentence(context, regex, -1, compatibilityFunc=compatibilityFunc)
            return self.expandSentence(context, regex, 1, compatibilityFunc=compatibilityFunc)
        elif direction > 0:
            cindex = -1
            method = "endToEnd"
        else:
            cindex = 0
            method = "startToStart"
        counter = 0
        while True:
            counter += 1
            if counter > 1000:
                raise RuntimeError("Infinite loop detected.")
            sentenceStr, startTi, startOffset, endTi, endOffset = self.findCurrentSentence(context, regex)

            #if ti.compareEndPoints(context.textInfos[cindex], method) != 0:
            if not context.isTouchingBoundary(direction, startTi, startOffset, endTi, endOffset):
                return (sentenceStr, startTi, startOffset, endTi, endOffset)
            nextTextInfo = self.nextParagraph(context.textInfos[cindex], direction)
            if nextTextInfo is None:
                return (sentenceStr, startTi, startOffset, endTi, endOffset)
            if compatibilityFunc is not None:
                if not compatibilityFunc(nextTextInfo, context.textInfos[cindex]):
                    return (sentenceStr, startTi, startOffset, endTi, endOffset)
            context.addParagraph(cindex, nextTextInfo)

    def moveExtended(self, context, direction, regex, errorMsg="Error", reconstructMode="sameIndent"):
        chimeIfAcrossParagraphs = False
        if reconstructMode == "always":
            compatibilityFunc = lambda x,y: True
        elif reconstructMode == "sameIndent":
            compatibilityFunc = lambda ti1, ti2: (ti1.NVDAObjectAtStart.location[0] == ti2.NVDAObjectAtStart.location[0]) and (self.getParagraphStyle(ti1) == self.getParagraphStyle(ti2))
        elif reconstructMode == "never":
            compatibilityFunc = lambda x,y: False
        else:
            raise ValueError()

        sentenceStr, startTi, startOffset, endTi, endOffset = self.expandSentence( context, regex, direction, compatibilityFunc=compatibilityFunc)
        if direction == 0:
            return sentenceStr, context.makeSentenceInfo(startTi, startOffset, endTi, endOffset)
        elif direction > 0:
            cindex = -1
            method = "endToEnd"
        else:
            cindex = 0
            method = "startToStart"
        if context.isTouchingBoundary(direction, startTi, startOffset, endTi, endOffset):
            # We need to look for the next sentence in the next paragraph.
            mylog("Looking in the next paragraph.")
            paragraph = context.textInfos[cindex]
            counter = 0
            while True:
                counter += 1
                if counter > 1000:
                    raise RuntimeError("Infinite loop detected.")
                paragraph = self.nextParagraph(paragraph, direction)
                if paragraph is None:
                    self.chimeNoNextSentence(errorMsg)
                    return (None, None)
                if not speech.isBlank(paragraph.text):
                    break
            self.chimeCrossParagraphBorder()
            context = Context(paragraph, 0)
            if direction < 0:
                #lastPosition = paragraph.copy()
                #lastPosition.collapse(True) # collapse to the end
                #result = lastPosition.move(textInfos.UNIT_CHARACTER, -1)
                #myAssert(result != 0)
                #context.find(lastPosition)
                context.findByOffset(paragraph, len(paragraph.text) - 1)
        else:
            # Next sentence can be found in the same context
            # At least its beginning or ending - that sentence will be expanded.
            mylog("Looking in the same paragraph.")
            if direction > 0:
                #ti2 = ti.copy()
                #ti2.collapse(True) # Collapse to the end
                #context.find(ti2)
                context.findByOffset(endTi, endOffset)
            else:
                #ti2 = ti.copy()
                #ti2.collapse(False) # to the beginning
                #result = ti2.move(textInfos.UNIT_CHARACTER, -1)
                #myAssert(result != 0)
                #context.find(ti2)
                context.findByOffset(startTi, startOffset - 1)
            chimeIfAcrossParagraphs = True
        sentenceStr2, startTi2, startOffset2, endTi2, endOffset2 = self.expandSentence( context, regex, direction, compatibilityFunc=compatibilityFunc)
        if debug:
            mylog(f"result2: {sentenceStr2}")
            mylog(f"start: {startOffset2} @ {startTi2.text}")
            mylog(f"end: {endOffset2} @ {endTi2.text}")
        if  chimeIfAcrossParagraphs:
            mylog(f"Chime? direction={direction} startOffset{startOffset} startOffset2={startOffset2}")
            if (
                (direction > 0 and startOffset2 == 0)
                or (direction < 0 and startOffset == 0)
            ):
                mylog(f"Chime!")
                self.chimeCrossParagraphBorder()
            #if ti.compareEndPoints(resultTi, "startToStart") > 0:
            #    trailing = ti
            #else:
            #    trailing = resultTi
            #for paragraph in context.textInfos:
            #    if paragraph.compareEndPoints(trailing, "startToStart") == 0:
            #        self.chimeCrossParagraphBorder()
            #        break
        info = context.makeSentenceInfo(startTi2, startOffset2, endTi2, endOffset2)
        if debug:
            mylog(f"MoveExtended result string: {sentenceStr2}")
            mylog(f"MoveExtended result: {info.text}")
        return sentenceStr2, info

    def chimeNoNextSentence(self, errorMsg="Error"):
        volume = config.conf["sentencenav"]["noNextSentenceChimeVolume"]
        self.fancyBeep("HF", 100, volume, volume)
        if getConfig("noNextSentenceMessage"):
            ui.message(errorMsg)

    def chimeCrossParagraphBorder(self):
        volume = config.conf["sentencenav"]["paragraphChimeVolume"]
        self.fancyBeep("AC#EG#", 30, volume, volume)

    @script(description='Move to next sentence.', gestures=['kb:Alt+DownArrow'],
        resumeSayAllMode=sayAllHandler.CURSOR_CARET)
    def script_nextSentence(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getRegex(getCurrentLanguage())
        # Translators: message when no next sentence available in the document
        errorMsg = _("No next sentence")
        self.move(gesture, regex, 1, errorMsg)

    @script(description='Move to previous sentence.', gestures=['kb:Alt+UpArrow'],
        resumeSayAllMode=sayAllHandler.CURSOR_CARET)
    def script_previousSentence(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getRegex(getCurrentLanguage())
        # Translators: message when no previous sentence available in the document
        errorMsg = _("No previous sentence")
        self.move(gesture, regex, -1, errorMsg)

    @script(description='Speak current sentence.', gestures=['kb:NVDA+Alt+S'])
    def script_currentSentence(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getRegex(getCurrentLanguage())
        self.move(gesture, regex, 0, "")

    @script(description='Move to next phrase.', gestures=['kb:Alt+Windows+DownArrow'],
        resumeSayAllMode=sayAllHandler.CURSOR_CARET)
    def script_nextPhrase(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getPhraseRegex()
        # Translators: message when no next phrase available in the document
        errorMsg = _("No next phrase")
        self.move(gesture, regex, 1, errorMsg)

    @script(description='Move to previous phrase.', gestures=['kb:Alt+Windows+UpArrow'],
        resumeSayAllMode=sayAllHandler.CURSOR_CARET)
    def script_previousPhrase(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getPhraseRegex()
        # Translators: message when no previous phrase available in the document
        errorMsg = _("No previous phrase")
        self.move(gesture, regex, -1, errorMsg)

    @script(description='Speak current phrase.', gestures=[])
    def script_currentPhrase(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getPhraseRegex()
        self.move(gesture, regex, 0, "")

    def maybePassThrough(self, gesture):
        focus = api.getFocusObject()
        appName = focus.appModule.appName
        if appName.lower() in getConfig("applicationsBlacklist").lower().strip().split(","):
            gesture.send()
            return True
        return False

    styleFields = [
        "level",
        "font-family",
        "font-size",
        "color",
        "background-color",
        "bold",
        "italic",
    ]

    def getParagraphStyle(self, info):
        formatField=textInfos.FormatField()
        formatConfig=config.conf['documentFormatting']
        for field in info.getTextWithFields(formatConfig):
            #if isinstance(field,textInfos.FieldCommand): and isinstance(field.field,textInfos.FormatField):
            try:
                formatField.update(field.field)
            except:
                pass
        result = [formatField.get(fieldName, None) for fieldName in self.styleFields]
        return tuple(result)

    def move(self, gesture, regex, increment, errorMsg):
        focus = api.getFocusObject()
        if not getConfig("enableInWord") and  (
            isinstance(focus, winword.WordDocument)
            or (
                "Dynamic_IAccessibleRichEdit" in str(type(focus))
                and  hasattr(focus, "script_caret_nextSentence")
                and hasattr(focus, "script_caret_previousSentence")
            )
        ):
            if increment > 0:
                focus.script_caret_nextSentence(gesture)
            elif increment < 0:
                focus.script_caret_previousSentence(gesture)
            else:
                # increment == 0
                pass
            return
        if focus.role  in [controlTypes.ROLE_COMBOBOX, controlTypes.ROLE_LISTITEM, controlTypes.ROLE_BUTTON]:
            try:
                # The following line will only succeed in BrowserMode.
                focus.treeInterceptor.script_collapseOrExpandControl(gesture)
            except AttributeError:
                gesture.send()
            return
        if hasattr(focus, "treeInterceptor") and hasattr(focus.treeInterceptor, "makeTextInfo"):
            focus = focus.treeInterceptor
        try:
            caretInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        except NotImplementedError:
            gesture.send()
            return
        caretIndex, paragraphInfo = getCaretIndexWithinParagraph(caretInfo)
        context = Context(paragraphInfo, caretIndex, caretInfo)
        reconstructMode = getConfig("reconstructMode")
        sentenceStr, ti = self.moveExtended(context, increment, regex=regex, errorMsg=errorMsg, reconstructMode=reconstructMode)
        if ti is None:
            return
        if increment != 0:
            newCaret = ti.copy()
            newCaret.collapse()
            newCaret.updateCaret()
            review.handleCaretMove(newCaret)
            braille.handler.handleCaretMove(focus)
            vision.handler.handleCaretMove(focus)
            
        if willSayAllResume(gesture):
            return
        if getConfig("speakFormatted"):
            speech.speakTextInfo(ti, reason=controlTypes.REASON_CARET)
        else:
            speech.speakText(sentenceStr)

    NOTES = "A,B,H,C,C#,D,D#,E,F,F#,G,G#".split(",")
    NOTE_RE = re.compile("[A-H][#]?")
    BASE_FREQ = 220
    def getChordFrequencies(self, chord):
        myAssert(len(self.NOTES) == 12)
        prev = -1
        result = []
        for m in self.NOTE_RE.finditer(chord):
            s = m.group()
            i =self.NOTES.index(s)
            while i < prev:
                i += 12
            result.append(int(self.BASE_FREQ * (2 ** (i / 12.0))))
            prev = i
        return result

    def fancyBeep(self, chord, length, left=10, right=10):
        beepLen = length
        freqs = self.getChordFrequencies(chord)
        intSize = 8 # bytes
        bufSize = max([NVDAHelper.generateBeep(None,freq, beepLen, right, left) for freq in freqs])
        if bufSize % intSize != 0:
            bufSize += intSize
            bufSize -= (bufSize % intSize)
        tones.player.stop()
        bbs = []
        result = [0] * (bufSize//intSize)
        for freq in freqs:
            buf = ctypes.create_string_buffer(bufSize)
            NVDAHelper.generateBeep(buf, freq, beepLen, right, left)
            bytes = bytearray(buf)
            unpacked = struct.unpack("<%dQ" % (bufSize // intSize), bytes)
            result = map(operator.add, result, unpacked)
        maxInt = 1 << (8 * intSize)
        result = map(lambda x : x %maxInt, result)
        packed = struct.pack("<%dQ" % (bufSize // intSize), *result)
        tones.player.feed(packed)

    def uniformSample(self, a, m):
        n = len(a)
        if n <= m:
            return a
        # Here assume n > m
        result = []
        for i in range(0, m*n, n):
            result.append(a[i // m])
        return result

    BASE_FREQ = speech.IDT_BASE_FREQUENCY
    def getPitch(self, indent):
        return self.BASE_FREQ*2**(indent/24.0) #24 quarter tones per octave.

    BEEP_LEN = 10 # millis
    PAUSE_LEN = 5 # millis
    MAX_CRACKLE_LEN = 400 # millis
    MAX_BEEP_COUNT = MAX_CRACKLE_LEN // (BEEP_LEN + PAUSE_LEN)

    def fancyCrackle(self, levels):
        levels = self.uniformSample(levels, self.MAX_BEEP_COUNT )
        beepLen = self.BEEP_LEN
        pauseLen = self.PAUSE_LEN
        pauseBufSize = NVDAHelper.generateBeep(None,self.BASE_FREQ,pauseLen,0, 0)
        beepBufSizes = [NVDAHelper.generateBeep(None,self.getPitch(l), beepLen, 50, 50) for l in levels]
        bufSize = sum(beepBufSizes) + len(levels) * pauseBufSize
        buf = ctypes.create_string_buffer(bufSize)
        bufPtr = 0
        for l in levels:
            bufPtr += NVDAHelper.generateBeep(
                ctypes.cast(ctypes.byref(buf, bufPtr), ctypes.POINTER(ctypes.c_char)),
                self.getPitch(l), beepLen, 50, 50)
            bufPtr += pauseBufSize # add a short pause
        tones.player.stop()
        tones.player.feed(buf.raw)

    def simpleCrackle(self, n):
        return self.fancyCrackle([0] * n)
