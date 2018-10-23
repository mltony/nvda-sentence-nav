#A part of the SentenceNav addon for NVDA
#Copyright (C) 2018 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

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

class Context:
    def __init__(self, textInfo):
        self.texts = [textInfo.text]
        self.textInfos = [textInfo]

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def re_grp(s):
        """Wraps a string with a non-capturing group for use in regular expressions."""
        return "(?:%s)" % s        
    
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
    def nlb(s):
        """Forms a negative look-behind regexp clause to prevent certain expressions like "Mr." from ending the sentence.
        It also adds a positive look-ahead to make sure that such an expression is followed by a period, as opposed to
        other sentence breakers, such as question or exclamation mark."""
        return u"(?<!" + s + u"(?=[.]))"
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
        assert(n == len(tis))
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
            j = i
        sentenceStr = s[boundaries[i]:boundaries[j]]
        
        t1i = bisect.bisect_right(parStartIndices, boundaries[i]) - 1
        t1 = tis[t1i].copy()
        t1.collapse()
        t1.move(textInfos.UNIT_CHARACTER, boundaries[i] - parStartIndices[t1i])
        t2i = bisect.bisect_right(parStartIndices, boundaries[j]) - 1
        t2 = tis[t2i].copy()
        t2.collapse()
        t2.move(textInfos.UNIT_CHARACTER, boundaries[j] - parStartIndices[t2i])
        t1.setEndPoint(t2, "endToEnd")
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
        assert(direction != 0)
        if direction > 0:
            return textInfo._endOffset
        else:
            return textInfo._startOffset
        
    def expandSentence(self, context, offset, regex, direction):
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
                self.chimeNoNextSentence()
                return (None, None)
            if not speech.isBlank(paragraph.text):
                break
        context = Context(paragraph)
        if direction > 0:
            offset  = paragraph._startOffset
        else:
            offset = paragraph._endOffset - 1
        return self.findCurrentSentence(context, offset, regex)
        
    def chimeNoNextSentence(self):
        self.fancyBeep("HF", 100, 50, 50)
        
    def chimeCrossParagraphBorder(self):
        self.fancyBeep("AC#EG#", 30, 5, 5)
        
    def script_nextSentence(self, gesture):
        """Move to next sentence."""
        self.move(gesture, 1)
        
    def script_previousSentence(self, gesture):
        """Move to previous sentence."""
        self.move(gesture, -1)

    def script_currentSentence(self, gesture):
        """Speak current  sentence."""
        self.move(gesture, 0)

        
    def script_nextText(self, gesture):
        """Move to next paragraph that contains text."""
        self.moveToText(gesture, 1)

    def script_previousText(self, gesture):
        """Move to previous paragraph that contains text."""
        self.moveToText(gesture, -1)

    def move(self, gesture, increment):
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
        sentenceStr, ti = self.moveSimple(textInfo, caretOffset, increment, regex=self.SENTENCE_END_REGEX)
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
        "kb:alt+shift+DownArrow": "nextText",
        "kb:alt+shift+UpArrow": "previousText",
    }
