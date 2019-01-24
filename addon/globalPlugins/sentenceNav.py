# -*- coding: UTF-8 -*-
#A part of the SentenceNav addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import bisect
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
import sayAllHandler
from scriptHandler import script, willSayAllResume
import speech
import struct
import textInfos
import tones
import ui
import wx

debug = False
if debug:
    f = open("C:\\Users\\tony\\Dropbox\\1.txt", "w")
def mylog(s):
    if debug:
        print >>f, str(s)
        f.flush()

def myAssert(condition):
    if not condition:
        raise RuntimeError("Assertion failed")


def createMenu():
    def _popupMenu(evt):
        gui.mainFrame._popupSettingsDialog(SettingsDialog)
    prefsMenuItem  = gui.mainFrame.sysTrayIcon.preferencesMenu.Append(wx.ID_ANY, _("SentenceNav..."))
    gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, _popupMenu, prefsMenuItem)

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
        "phraseBreakers" : "string( default='.!?,;:-–()')",
        "fullWidthPhraseBreakers" : "string( default='。！？，；：（）')",
        "applicationsBlacklist" : "string( default='audacity,excel')",
    }
    config.conf.spec["sentencenav"] = confspec

def getConfig(key, lang=None):
    value = config.conf["sentencenav"][key]
    if isinstance(value, str):
        value = unicode(value.decode("UTF-8"))
    if lang is None:
        return value
    dictionary = json.loads(value)
    try:
        return dictionary[lang]
    except KeyError:
        return dictionary["en"]

def setConfig(key, value, lang):
    fullValue = config.conf["sentencenav"][key]
    fullValue = unicode(fullValue.decode("UTF-8"))
    dictionary = json.loads(fullValue)
    dictionary[lang] = value
    config.conf["sentencenav"][key] = json.dumps(dictionary).encode("UTF-8")

def getCurrentLanguage():
    s = speech.getCurrentLanguage()
    return s[:2]

addonHandler.initTranslation()
initConfiguration()
createMenu()

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
        config.conf["sentencenav"]["phraseBreakers"] = self.phraseBreakersEdit.Value
        config.conf["sentencenav"]["fullWidthPhraseBreakers"] = self.fullWidthPhraseBreakersEdit.Value
        config.conf["sentencenav"]["applicationsBlacklist"] = self.applicationsBlacklistEdit.Value

        regexCache.clear()
        phraseRegex = None
        super(SettingsDialog, self).onOk(evt)


def countCharacters(textInfo):
    '''Counts the number of characters in this TextInfo.
    There is no good unified way to do so in NVDA, 
    so try every possible trick in the book.'''
    try:
        # This works for offset-based TextInfos
        return textInfo._endOffset - textInfo._startOffset
    except AttributeError:
        pass
    try:
        # This works for some CompoundTextInfos, like in LibreOffice Writer
        return countCharacters(list(textInfo._getTextInfos())[0])
    except AttributeError:
        pass
    try:
        # This works in edit control in Mozilla Thunderbird
        return countCharacters(textInfo._start)
    except AttributeError:
        pass
    raise RuntimeError("Unable to count characters for %s" % str(textInfo))

def getCaretIndexWithinParagraph(caretTextInfo):
    paragraphTextInfo = caretTextInfo.copy()
    paragraphTextInfo.expand(textInfos.UNIT_PARAGRAPH)
    paragraphTextInfo.setEndPoint(caretTextInfo, "endToStart")
    return countCharacters(paragraphTextInfo)

class Context:
    def __init__(self, textInfo, caretIndex):
        self.texts = [textInfo.text]
        self.textInfos = [textInfo]
        self.caretIndex = caretIndex # Caret index within current paragraph, zero-based
        self.current = 0 # Index of current paragraph

    def find(self, textInfo, which="start"):
        for i in xrange(len(self.textInfos)):
            if textInfo.compareEndPoints(self.textInfos[i], which + "ToStart") >= 0:
                if textInfo.compareEndPoints(self.textInfos[i], which + "ToEnd") < 0:
                    self.current = i
                    indexTextInfo = self.textInfos[i].copy()
                    indexTextInfo.setEndPoint(textInfo, "endTo" + which.capitalize())
                    self.caretIndex = countCharacters(indexTextInfo)
                    return
        raise RuntimeError("Could not find textInfo in this context.")

    def __str__(self):
        result = ""
        for i in xrange(len(self.texts)):
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

def re_set(s):
    """Creates a regex set of characters from a plain string."""
    # Step 1: escape special characters
    for c in "\\[]":
        s = s.replace(c, "\\" + c)
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

    try:
        return regexCache[lang]
    except KeyError:
        pass
    regex = u""
    regex += nlb("\\b" + re_set(getConfig("capitalLetters", lang)))
    for abbr in getConfig("exceptionalAbbreviations", lang).strip().split():
        regex += nlb(re_escape(abbr))
    regex += re_set(getConfig("sentenceBreakers")) + "+"
    regex += re_set(getConfig("skippable")) + "*"
    if getConfig("breakOnWikiReferences"):
        wikiReference = re_grp("\\[[\\w\\s]+\\]")
        regex += wikiReference + "*"
    regex += "\\s+"
    fullWidth = re_set(getConfig("fullWidthSentenceBreakers"))
    regex = u"^|{regex}|{fullWidth}+\\s*|\n\n+\\s*|\\s*$".format(
        regex=regex,
        fullWidth=fullWidth)
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
    regex = u"^|{regex}|{fullWidth}+|\\s*$".format(
        regex=regex,
        fullWidth=fullWidth)
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
        index = sum([len(texts[t]) for t in xrange(context.current)]) + len(joinString) * context.current + context.caretIndex
        parStartIndices = [0] # Denotes indices in s where new paragraphs start
        for i in xrange(1, n):
            parStartIndices.append(parStartIndices[i-1] + len(texts[i-1]) + len(joinString))
        boundaries = self.splitParagraphIntoSentences(s, regex=regex)
        # Find the first index in boundaries that is strictly greater than index
        j = bisect.bisect_right(boundaries, index)
        i = j - 1
        # At this point boundaries[i] and boundaries[j] represent
        # the boundaries of the current sentence.
        if len(boundaries) == 1:
            # This must be an empty context/paragraph
            # j points to out of boundaries
            t1i = bisect.bisect_right(parStartIndices, boundaries[i]) - 1
            t1 = tis[t1i].copy()
            t1.expand(textInfos.UNIT_PARAGRAPH)
            return (t1.text, t1)
        if j == len(boundaries):
            # This can happen if the cursor is at the very last position in the document
            ti = tis[-1].copy()
            ti.collapse()
            moveDistance = boundaries[i] - parStartIndices[-1]
            ti.move(textInfos.UNIT_CHARACTER, moveDistance)
            ti.setEndPoint(tis[-1], "endToEnd")
            return ("", ti)
        sentenceStr = s[boundaries[i]:boundaries[j]]

        t1i = bisect.bisect_right(parStartIndices, boundaries[i]) - 1
        t1 = tis[t1i].copy()
        t1.collapse()
        t1.move(textInfos.UNIT_CHARACTER, boundaries[i] - parStartIndices[t1i])
        t2i = bisect.bisect_right(parStartIndices, boundaries[j]) - 1
        t2 = tis[t2i].copy()
        moveDistance = boundaries[j] - parStartIndices[t2i]
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
        return (sentenceStr, t1)

    def nextParagraph(self, textInfo, direction):
        ti = textInfo.copy()
        # For some TextInfo implementations, such as edit control in Thunderbird we need to try twice:
        for i in [1,2]:
            ti.collapse()
            result = ti.move(textInfos.UNIT_PARAGRAPH, direction)
            if result == 0:
                return None
            ti.expand(textInfos.UNIT_PARAGRAPH)
            if ti.compareEndPoints(textInfo, "startToStart") == direction:
                return ti
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
            sentenceStr, ti = self.findCurrentSentence(context, regex)
            if ti.compareEndPoints(context.textInfos[cindex], method) != 0:
                return (sentenceStr, ti)
            nextTextInfo = self.nextParagraph(context.textInfos[cindex], direction)
            if nextTextInfo is None:
                return (sentenceStr, ti)
            if compatibilityFunc is not None:
                if not compatibilityFunc(nextTextInfo, context.textInfos[cindex]):
                    return (sentenceStr, ti)
            nextText = nextTextInfo.text
            if direction > 0:
                context.textInfos.append(nextTextInfo)
                context.texts.append(nextText)
            else:
                context.textInfos.insert(0, nextTextInfo)
                context.texts.insert(0, nextText)
                context.current += 1

    def moveExtended(self, paragraph, caretIndex, direction, regex, errorMsg="Error", reconstructMode="sameIndent"):
        chimeIfAcrossParagraphs = False
        if reconstructMode == "always":
            compatibilityFunc = lambda x,y: True
        elif reconstructMode == "sameIndent":
            compatibilityFunc = lambda ti1, ti2: (ti1.NVDAObjectAtStart.location[0] == ti2.NVDAObjectAtStart.location[0]) and (self.getParagraphStyle(ti1) == self.getParagraphStyle(ti2))
        elif reconstructMode == "never":
            compatibilityFunc = lambda x,y: False
        else:
            raise ValueError()
        context = Context(paragraph, caretIndex)
        sentenceStr, ti = self.expandSentence( context, regex, direction, compatibilityFunc=compatibilityFunc)
        if direction == 0:
            return sentenceStr, ti
        elif direction > 0:
            cindex = -1
            method = "endToEnd"
        else:
            cindex = 0
            method = "startToStart"
        if ti.compareEndPoints(context.textInfos[cindex], method) == 0:
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
                lastPosition = paragraph.copy()
                lastPosition.collapse(True) # collapse to the end
                result = lastPosition.move(textInfos.UNIT_CHARACTER, -1)
                myAssert(result != 0)
                context.find(lastPosition)
        else:
            # Next sentence can be found in the same context
            # At least its beginning or ending - that sentence will be expanded.
            mylog("Looking in the same paragraph.")
            if direction > 0:
                ti2 = ti.copy()
                ti2.collapse(True) # Collapse to the end
                context.find(ti2)
            else:
                ti2 = ti.copy()
                ti2.collapse(False) # to the beginning
                result = ti2.move(textInfos.UNIT_CHARACTER, -1)
                myAssert(result != 0)
                context.find(ti2)
            chimeIfAcrossParagraphs = True
        resultSentenceStr, resultTi = self.expandSentence( context, regex, direction, compatibilityFunc=compatibilityFunc)
        if  chimeIfAcrossParagraphs:
            if ti.compareEndPoints(resultTi, "startToStart") > 0:
                trailing = ti
            else:
                trailing = resultTi
            for paragraph in context.textInfos:
                if paragraph.compareEndPoints(trailing, "startToStart") == 0:
                    self.chimeCrossParagraphBorder()
                    break
        return resultSentenceStr, resultTi

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

    @script(description='Move to next phrase.', gestures=['kb:Alt+Windows+DownArrow'])
    def script_nextPhrase(self, gesture):
        if self.maybePassThrough(gesture):
            return
        regex = getPhraseRegex()
        # Translators: message when no next phrase available in the document
        errorMsg = _("No next phrase")
        self.move(gesture, regex, 1, errorMsg)

    @script(description='Move to previous phrase.', gestures=['kb:Alt+Windows+UpArrow'])
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
        if unicode(appName.lower()) in getConfig("applicationsBlacklist").lower().strip().split(","):
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
        if (
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
        textInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        caretIndex = getCaretIndexWithinParagraph(textInfo)
        textInfo.expand(textInfos.UNIT_PARAGRAPH)
        reconstructMode = getConfig("reconstructMode")
        sentenceStr, ti = self.moveExtended(textInfo, caretIndex, increment, regex=regex, errorMsg=errorMsg, reconstructMode=reconstructMode)
        if ti is None:
            return
        if increment != 0:
            ti.updateCaret()
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
        result = [0] * (bufSize/intSize)
        for freq in freqs:
            buf = ctypes.create_string_buffer(bufSize)
            NVDAHelper.generateBeep(buf, freq, beepLen, right, left)
            bytes = bytearray(buf)
            unpacked = struct.unpack("<%dQ" % (bufSize / intSize), bytes)
            result = map(operator.add, result, unpacked)
        maxInt = 1 << (8 * intSize)
        result = map(lambda x : x %maxInt, result)
        packed = struct.pack("<%dQ" % (bufSize / intSize), *result)
        tones.player.feed(packed)

    def uniformSample(self, a, m):
        n = len(a)
        if n <= m:
            return a
        # Here assume n > m
        result = []
        for i in xrange(0, m*n, n):
            result.append(a[i  / m])
        return result

    BASE_FREQ = speech.IDT_BASE_FREQUENCY
    def getPitch(self, indent):
        return self.BASE_FREQ*2**(indent/24.0) #24 quarter tones per octave.

    BEEP_LEN = 10 # millis
    PAUSE_LEN = 5 # millis
    MAX_CRACKLE_LEN = 400 # millis
    MAX_BEEP_COUNT = MAX_CRACKLE_LEN / (BEEP_LEN + PAUSE_LEN)

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
