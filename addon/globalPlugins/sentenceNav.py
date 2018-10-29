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
import speech
import struct
import textInfos
import tones
import ui
import wx


f = open("C:\\users\\tony\\dropbox\\work\\1.txt", "w")
def log(s):
    ss = s
    try:
        ss = ss.encode("UTF-8")
    except:
        pass
    print >>f, ss
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
    "en": "Mr Ms Mrs Dr St",
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
        "breakOnWikiReferences" : "boolean( default=True)",
        "sentenceBreakers" : "string( default='.!?')",
        "fullWidthSentenceBreakers" : "string( default='。！？')",
        "skippable" : "string( default='\"”’»)')",
        "exceptionalAbbreviations" : "string( default='%s')" % exceptionalAbbreviations,
        "capitalLetters" : "string( default='%s')" % capitalLetters,
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

        

    def onOk(self, evt):
        config.conf["sentencenav"]["paragraphChimeVolume"] = self.paragraphChimeVolumeSlider.Value
        config.conf["sentencenav"]["noNextSentenceChimeVolume"] = self.noNextSentenceChimeVolumeSlider.Value
        config.conf["sentencenav"]["noNextSentenceMessage"] = self.noNextSentenceMessageCheckbox.Value
        config.conf["sentencenav"]["sentenceBreakers"] = self.sentenceBreakersEdit.Value
        config.conf["sentencenav"]["skippable"] = self.skippableEdit.Value
        config.conf["sentencenav"]["fullWidthSentenceBreakers"] = self.fullWidthSentenceBreakersEdit.Value
        setConfig("exceptionalAbbreviations", self.exceptionalAbbreviationsEdit.Value, self.lang)
        setConfig("capitalLetters", self.capitalLettersEdit.Value, self.lang)
        
        regexCache.clear()
        super(SettingsDialog, self).onOk(evt)

class Context:
    def __init__(self, textInfo):
        self.texts = [textInfo.text]
        self.textInfos = [textInfo]

def re_grp(s):
    """Wraps a string with a non-capturing group for use in regular expressions."""
    return "(?:%s)" % s        

def re_set(s):
    """Creates a regex set of characters from a plain string."""
    # Step 1: escape special characters
    for c in "\\[]":
        s = s.replace(c, "\\" + c)
    return "[" + s + "]"
    
def nlb(s):
    """Forms a negative look-behind regexp clause to prevent certain expressions like "Mr." from ending the sentence.
    It also adds a positive look-ahead to make sure that such an expression is followed by a period, as opposed to
    other sentence breakers, such as question or exclamation mark."""
    return u"(?<!" + s + u"(?=[.]))"

regexCache = {}

def getRegex(lang):
    try:
        return regexCache[lang]
    except KeyError:
        pass
    regex = u""
    regex += nlb(re_set(getConfig("capitalLetters", lang)))
    for abbr in getConfig("exceptionalAbbreviations", lang).strip().split():
        regex += nlb(abbr)
    regex += re_set(getConfig("sentenceBreakers")) + "+"
    regex += re_set(getConfig("skippable")) + "*"
    if getConfig("breakOnWikiReferences"):
        wikiReference = re_grp("\\[[\\w\\s]+\\]")
        regex += wikiReference + "*"
    regex += "\\s+"
    fullWidth = re_set(getConfig("fullWidthSentenceBreakers"))
    regex = u"^|{regex}|{fullWidth}+|\\s*$".format(
        regex=regex,
        fullWidth=fullWidth)
    log(regex.encode("UTF-8"))
    result = re.compile(regex , re.UNICODE)
    regexCache[lang] = result
    return result

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    
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
    SENTENCE_BREAKERS = ".?!"
    CHINESE_SENTENCE_BREAKERS = ("["
        + u"\u3002" # Chinese full stop
        + u"\uFF01" # Chinese exclamation mark
        + u"\uFF1F" # Chinese question mark
        + "]+") 

    SKIPPABLE_PUNCTUATION = (
        u'")'
        + u"\u201D" # Right double quotation mark
        )  
    WIKIPEDIA_REFERENCE = re_grp("\\[[\\w\\s]+\\]")
    SENTENCE_END_REGEX = u"[{br}]+[{skip}]*{wiki}*\\s+".format(
        br=SENTENCE_BREAKERS ,
        wiki=WIKIPEDIA_REFERENCE,
        skip = SKIPPABLE_PUNCTUATION)
    CAPITAL_LETTERS = (
        "[A-Z"
        # Cyrillic capital letters:
        + u"".join(
            map(unichr,
                xrange(0x0410, 0x0430) 
            ))
        + "]")
    ABBREVIATIONS = "Mr|Ms|Mrs|Dr|St".split("|")
    LOOK_BEHIND = nlb("\\s" + CAPITAL_LETTERS)
    LOOK_BEHIND += "".join([nlb(u"\\s" + abbr) for abbr in ABBREVIATIONS])
    SENTENCE_END_REGEX = LOOK_BEHIND + SENTENCE_END_REGEX
    SENTENCE_END_REGEX = re_grp("^|" + SENTENCE_END_REGEX + "|" + CHINESE_SENTENCE_BREAKERS + "|\\s*$")
    SENTENCE_END_REGEX  = re.compile(SENTENCE_END_REGEX , re.UNICODE)
    
    def splitParagraphIntoSentences(self, text, regex=None):
        if regex is None:
            regex = self.SENTENCE_END_REGEX
        result = [m.end() for m in regex.finditer(text)]
        # Sometimes the last position in the text will be matched twice, so filter duplicates.
        result = sorted(list(set(result)))
        return result
        
    def findCurrentSentence(self, context, offset, regex):
        texts = context.texts
        tis = context.textInfos
        n = len(texts)
        myAssert(n == len(tis))
        
        # Checking that the state is valid
        for i in xrange(n):
            l1 = len(texts[i])
            l2 = tis[i]._endOffset - tis[i]._startOffset
            # Most of the times l1 == l2, however, sometimes l2 is greater by one.
            # Check that no other condition is possible.
            if l1 == l2:
                continue
            if l1 + 1 == l2:
                continue
            raise RuntimeError("Invalid state: l1=%d l2=%d" % (l1, l2))
            
        # Checking that textInfos in the context are adjacent
        for i in xrange(1, n):
            myAssert(tis[i-1]._endOffset == tis[i]._startOffset)
        
        #Step 1. Identify which paragraph offset belongs to.
        curParIndex = -1
        for i in xrange(n):
            textInfo = tis[i]
            if textInfo._startOffset <= offset < textInfo._endOffset:
                curParIndex = i
                break
        if curParIndex == -1:
            raise RuntimeError("Offset is not within this paragraph.")
        joinString = " "
        s = joinString.join(texts)
        index = offset - tis[0]._startOffset + len(joinString) * curParIndex
        parStartIndices = [] # Denotes indices in s where new paragraphs start
        for i in xrange(n):
            parStartIndices.append(tis[i]._startOffset - tis[0]._startOffset + len(joinString) * i)
        boundaries = self.splitParagraphIntoSentences(s, regex=regex)
        # Find the first index in boundaries that is strictly greater than index
        j = bisect.bisect_right(boundaries, index)
        i = j - 1            
        # At this point boundaries[i] and boundaries[j] represent
        # the boundaries of the current sentence.
        if len(boundaries) == 1:
            # This must be an empty context/paragraph
            # j points to out of boundaries
            log("empty paragraph")
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
        ti.collapse()
        result = ti.move(textInfos.UNIT_PARAGRAPH, direction)
        if result == 0:
            return None
        ti.expand(textInfos.UNIT_PARAGRAPH)
        return ti
        
    def getBoundaryOffset(self, textInfo, direction):
        myAssert(direction != 0)
        if direction > 0:
            return textInfo._endOffset
        else:
            return textInfo._startOffset
        
    def expandSentence(self, context, offset, regex, direction, compatibilityFunc=None):
        if direction == 0:
            # Expand both forward and backward
            self.expandSentence(context, offset, regex, -1)
            return self.expandSentence(context, offset, regex, 1)
        elif direction > 0:
            cindex = -1
        else:
            cindex = 0
            
        while True:
            sentenceStr, ti = self.findCurrentSentence(context, offset, regex)
            if self.getBoundaryOffset(ti, direction) != self.getBoundaryOffset(context.textInfos[cindex], direction):
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
    
    def moveSimple(self, paragraph, offset, direction, regex):
        context = Context(paragraph)
        sentenceStr, ti = self.findCurrentSentence(context, offset, regex)
        if direction == 0:
            return sentenceStr, ti
        if self.getBoundaryOffset(ti, direction) != self.getBoundaryOffset(paragraph, direction):
            # Next sentence can be found within the same paragraph
            if direction > 0:
                offset = ti._endOffset
            else:
                offset = ti._startOffset - 1
            return self.findCurrentSentence(context, offset, regex)
        # We need to move to previous/next paragraphs
        self.chimeCrossParagraphBorder()
        while True:
            paragraph = self.nextParagraph(paragraph, direction)
            if paragraph is None:
                self.chimeNoNextSentence(direction)
                return (None, None)
            if not speech.isBlank(paragraph.text):
                break
        context = Context(paragraph)
        if direction > 0:
            offset  = paragraph._startOffset
        else:
            offset = paragraph._endOffset - 1
        return self.findCurrentSentence(context, offset, regex)
        
    def moveExtended(self, paragraph, offset, direction, regex, reconstructMode="sameIndent"):
        chimeIfAcrossParagraphs = False
        if reconstructMode == "always":
            compatibilityFunc = lambda x,y: True
        elif reconstructMode == "sameIndent":
            compatibilityFunc = lambda ti1, ti2: ti1.NVDAObjectAtStart.location[0] == ti2.NVDAObjectAtStart.location[0]
        elif reconstructMode == "never":
            compatibilityFunc = lambda x,y: False
        else:
            raise ValueError()
        context = Context(paragraph)
        sentenceStr, ti = self.expandSentence( context, offset, regex, direction, compatibilityFunc=compatibilityFunc)
        if direction == 0:
            return sentenceStr, ti
        elif direction > 0:
            cindex = -1
        else:
            cindex = 0
        if self.getBoundaryOffset(ti, direction) == self.getBoundaryOffset(context.textInfos[cindex], direction):
            # We need to look for the next sentence in the next paragraph.
            paragraph = context.textInfos[cindex]
            while True:
                paragraph = self.nextParagraph(paragraph, direction)
                if paragraph is None:
                    self.chimeNoNextSentence(direction)
                    return (None, None)
                if not speech.isBlank(paragraph.text):
                    break
            self.chimeCrossParagraphBorder()
            context = Context(paragraph)
            if direction > 0:
                offset = paragraph._startOffset
            else:
                offset = paragraph._endOffset - 1
        else:
            # Next sentence can be found in the same context
            # At least its beginning or ending - that sentence will be expanded.
            if direction > 0:
                offset = ti._endOffset
            else:
                offset = ti._startOffset - 1
            chimeIfAcrossParagraphs = True
        resultSentenceStr, resultTi = self.expandSentence( context, offset, regex, direction, compatibilityFunc=compatibilityFunc)
        if chimeIfAcrossParagraphs:
            paragraphOffsets = [p._startOffset for p in context.textInfos]
            index1 = bisect.bisect_right(paragraphOffsets, ti._startOffset)
            index2 = bisect.bisect_right(paragraphOffsets, resultTi._startOffset)
            if index1 != index2:
                self.chimeCrossParagraphBorder()
        return resultSentenceStr, resultTi
        
    def chimeNoNextSentence(self, direction):
        volume = config.conf["sentencenav"]["noNextSentenceChimeVolume"]
        self.fancyBeep("HF", 100, volume, volume)
        if getConfig("noNextSentenceMessage"):
            if direction > 0:
                # Translators: Spoken message when no next sentence is available in the document
                ui.message(_("No next sentence"))
            else:
                # Translators: Spoken message when no previous sentence is available in the document
                ui.message(_("No previous sentence"))
        
    def chimeCrossParagraphBorder(self):
        volume = config.conf["sentencenav"]["paragraphChimeVolume"]
        self.fancyBeep("AC#EG#", 30, volume, volume)
        
    def script_nextSentence(self, gesture):
        """Move to next sentence."""
        self.move(gesture, 1)
        
    def script_previousSentence(self, gesture):
        """Move to previous sentence."""
        self.move(gesture, -1)

    def script_currentSentence(self, gesture):
        """Speak current  sentence."""
        self.move(gesture, 0)

    def script_nextExtendedSentence(self, gesture):
        """Move to next extended sentence."""
        self.move(gesture, 1, extended=True)
        
    def script_previousExtendedSentence(self, gesture):
        """Move to previous extended sentence."""
        self.move(gesture, -1, extended=True)

    def script_nextText(self, gesture):
        """Move to next paragraph that contains text."""
        self.moveToText(gesture, 1)

    def script_previousText(self, gesture):
        """Move to previous paragraph that contains text."""
        self.moveToText(gesture, -1)

    def move(self, gesture, increment, extended=False):
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
        if focus.role  in [controlTypes.ROLE_COMBOBOX, controlTypes.ROLE_LISTITEM]:
            try:
                # The following line will only succeed in BrowserMode.
                focus.treeInterceptor.script_collapseOrExpandControl(gesture)
            except AttributeError:
                gesture.send()
            return
        if hasattr(focus, "treeInterceptor") and hasattr(focus.treeInterceptor, "makeTextInfo"):
            focus = focus.treeInterceptor
        textInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        caretOffset = textInfo._getCaretOffset() 
        textInfo.expand(textInfos.UNIT_PARAGRAPH)
        caretIndex = caretOffset - textInfo._startOffset
        regex = getRegex(getCurrentLanguage())
        if extended:
            sentenceStr, ti = self.moveExtended(textInfo, caretOffset, increment, regex=regex)
        else:
            sentenceStr, ti = self.moveSimple(textInfo, caretOffset, increment, regex=regex)
        if ti is None:
            return
        ti.collapse()
        if increment != 0:
            ti.updateCaret()
        speech.speakText(sentenceStr)
        return
        
        while True:
            text = textInfo.text
            boundaries = self.splitParagraphIntoSentences(text)
            # Find the first index in boundaries that is strictly greater than caretIndex
            j = bisect.bisect_right(boundaries, caretIndex)
            i = j - 1            
            # At this point boundaries[i] and boundaries[j] represent
            # the boundaries of the current sentence.
            
            # Testing if we can move to previous/next sentence and still remain within the same paragraph.
            n = len(boundaries)
            if (0 <= i + increment < n) and (0 <= j + increment < n):
                # Next sentence can be found within the same paragraph
                i += increment
                j += increment
                textInfo.collapse()
                textInfo2 = textInfo.copy()
                result = textInfo.move(textInfos.UNIT_CHARACTER, boundaries[i])
                myAssert((result != 0) or (boundaries[i] == 0))
                # If we are moving to the very last sentence of the very last paragraph,
                # then we cannot move textInfo2 to the end of the paragraph.
                # Move to just one character before that, and then try to move one more character.
                myAssert(boundaries[j] > 1)
                result2 = textInfo2.move(textInfos.UNIT_CHARACTER, boundaries[j] - 1)
                myAssert(result2 != 0)
                textInfo2.move(textInfos.UNIT_CHARACTER, 1)
                textInfo.setEndPoint(textInfo2, "endToStart")
                textInfo.updateCaret()
                ui.message(textInfo.text)
                return
            else:  
                # We need to move to previous/next paragraph to find previous/next sentence.
                self.fancyBeep("AC#EG#", 30, 5, 5)
                while True:
                    result = textInfo.move(textInfos.UNIT_PARAGRAPH, increment)
                    if result == 0:
                        self.fancyBeep("HF", 100, 50, 50)
                        return
                    textInfo.expand(textInfos.UNIT_PARAGRAPH)
                    if not speech.isBlank(textInfo.text):
                        break
                textInfo.expand(textInfos.UNIT_PARAGRAPH)
                # Imaginary caret just before (if moving forward) or just after (if moving backward) this paragraph,
                # so that the next iteration will pick the very first or the very last sentence of this paragraph.
                if increment > 0:
                    caretIndex = -1
                else:
                    caretIndex = len(textInfo.text) 
                # Now control flow will takes us to another iteration of the outer while loop. 

    def moveToText(self, gesture, increment):
        focus = api.getFocusObject()
        if hasattr(focus, "treeInterceptor") and hasattr(focus.treeInterceptor, "makeTextInfo"):
            focus = focus.treeInterceptor
        textInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        distance = 0
        while True:
            result =textInfo.move(textInfos.UNIT_PARAGRAPH, increment)
            if result == 0:
                self.fancyBeep("HF", 100, 50, 50)
                return
            distance += 1
            textInfo.expand(textInfos.UNIT_PARAGRAPH)
            text = textInfo.text
            
            # Small hack: our regex always matches the end of the string, since any sentence must end at the end of the paragraph.
            # In this case, however, we need to figure out if the sentence really ends with a full stop or other sentence breaker at the end.
            # So we add a random word in the end of the string and see if there is any other sentence boundaries besides the beginning and the end of the string.
            text2 = text + " FinalWord"
            boundaries = self.splitParagraphIntoSentences(text2)
            if len(boundaries) >= 3:
                textInfo.collapse()
                textInfo.updateCaret()
                self.simpleCrackle(distance)
                ui.message(text)
                break

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

    __gestures = {
        "kb:alt+DownArrow": "nextSentence",
        "kb:alt+UpArrow": "previousSentence",
        "kb:NVDA+Alt+S": "currentSentence",
        "kb:alt+Windows+DownArrow": "nextExtendedSentence",
        "kb:alt+Windows+UpArrow": "previousExtendedSentence",
        "kb:alt+shift+DownArrow": "nextText",
        "kb:alt+shift+UpArrow": "previousText",
    }
