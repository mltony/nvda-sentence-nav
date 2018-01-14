#A part of the SentenceNav addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file LICENSE  for more details.

import addonHandler
import api
import bisect
import controlTypes
import ctypes
import globalPluginHandler
import NVDAHelper
from NVDAObjects.window import winword
import operator
import re 
import speech
import struct
import textInfos
import tones
import ui

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def re_grp(s):
        return "(?:%s)" % s        
    
    SENTENCE_BREAKERS = (
        ".?!"
        + u"\u3002" # Chinese full stop
        + u"\uFF01" # Chinese exclamation mark
        + u"\uFF1F" # Chinese question mark 
        )
    SKIPPABLE_PUNCTUATION = (
        u'")'
        + u"\u201D" # Right double quotation amrk
        )  
    WIKIPEDIA_REFERENCE = re_grp("\\[[\\w\\s]+\\]")
    SENTENCE_END_REGEX = u"[{br}]+[{skip}]*{wiki}*\\s+".format(
        br=SENTENCE_BREAKERS ,
        wiki=WIKIPEDIA_REFERENCE,
        skip = SKIPPABLE_PUNCTUATION)
    CAPITAL_LETTERS = ("[A-Z"
                       + "\u0410-\u042F" # Cyrillic capital letters
                       + "]")
    ABBREVIATIONS = "Mr|Ms|Mrs|Dr|St".split("|")
    def nlb(s):
        """Forms a negative look-behind regexp clause to prevent certain expressions like "Mr." from ending the sentence.
        It also adds a positive look-ahead to make sure that such an expression is followed by a period, as opposed to
        other sentence breakers, such as question or exclamation mark."""
        return u"(?<!" + s + u"(?=[.]))"
    LOOK_BEHIND = nlb("\\s" + CAPITAL_LETTERS)
    LOOK_BEHIND += "".join([nlb(u"\\s" + abbr) for abbr in ABBREVIATIONS])
    SENTENCE_END_REGEX = LOOK_BEHIND + SENTENCE_END_REGEX
    SENTENCE_END_REGEX = re_grp("^|" + SENTENCE_END_REGEX +  "|\\s*$")
    SENTENCE_END_REGEX  = re.compile(SENTENCE_END_REGEX , re.UNICODE)
    
    def splitParagraphIntoSentences(self, text):
        result = [m.end() for m in self.SENTENCE_END_REGEX  .finditer(text)]
        # Sometimes the last position in the text will be matched twice, so filter duplicates.
        result = sorted(list(set(result)))
        return result
    
    def script_nextSentence(self, gesture):
        """Move to next sentence."""
        self.move(gesture, 1)
        
    def script_previousSentence(self, gesture):
        """Move to previous sentence."""
        self.move(gesture, -1)
        
    def move(self, gesture, increment):
        focus = api.getFocusObject()
        if isinstance(focus, winword.WordDocument):
            if increment > 0:
                focus.script_caret_nextSentence(None)
            else:
                focus.script_caret_previousSentence(None)    
            return
        if focus.role  in [controlTypes.ROLE_COMBOBOX, controlTypes.ROLE_LISTITEM]:
            try:
                focus.script_collapseOrExpandControl(gesture)
            except AttributeError:
                errorMsg = _(
                    "This keystroke doesn't work here because of SentenceNav add-on running. "
                    + "You can either disable SentenceNav add-on in NVDA settings, "
                    + "or press Enter Instead to open a combo box."
                    )
                ui.message(errorMsg)
                return
            return
        if hasattr(focus, "treeInterceptor") and hasattr(focus.treeInterceptor, "makeTextInfo"):
            focus = focus.treeInterceptor
        textInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        caretOffset = textInfo._getCaretOffset() 
        textInfo.expand(textInfos.UNIT_PARAGRAPH)
        caretIndex = caretOffset - textInfo._startOffset
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
                assert((result != 0) or (boundaries[i] == 0))
                # If we are moving to the very last sentence of the very last paragraph,
                # then we cannot move textInfo2 to the end of the paragraph.
                # Move to just one character before that, and then try to move one more character.
                assert(boundaries[j] > 1)
                result2 = textInfo2.move(textInfos.UNIT_CHARACTER, boundaries[j] - 1)
                assert(result2 != 0)
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
        
    NOTES = "A,B,H,C,C#,D,D#,E,F,F#,G,G#".split(",")
    NOTE_RE = re.compile("[A-H][#]?")
    BASE_FREQ = 220 
    def getChordFrequencies(self, chord):
        assert(len(self.NOTES) == 12)
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
    __gestures = {
        "kb:alt+DownArrow": "nextSentence",
        "kb:alt+UpArrow": "previousSentence",
    }
