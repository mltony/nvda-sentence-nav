import api
import bisect
import controlTypes
import config
import ctypes
import globalPluginHandler
import NVDAHelper
import operator
import re 
import speech
import textInfos
import tones
import ui
import unicodedata


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    MY_LOG_NAME = "C:\\Users\\tony\\1.txt" 
    open(MY_LOG_NAME, "w").close()
    
    def mylog(self, s):
        f = open(self.MY_LOG_NAME, "a")
        f.write(unicode(s).encode('utf8'))
        f.write("\n")        
        f.close()
    
    def describe(self, obj):
        self.mylog(str(obj))
        self.mylog(str(type(obj)))
        for s in dir(obj):
            self.mylog(str(s))

    SENTENCE_BREAKERS = set(list(".!?"))
    EMPTY_CHARACTERS = set(list(" \t\r\n"))
    
    def re_grp(s):
        return "(?:%s)" % s        
    
    SENTENCE_BREAKERS =( ".?!"
                         + u"\u3002" # Chinese full stop
                         + u"\uFF01" # Chinese exclamation mark
                         + u"\uFF1F" # Chinese question mark 
                         ) 
    WIKIPEDIA_REFERENCE = re_grp("\\[[\\w\\s]+\\]")
    SENTENCE_END_REGEX = u"[{br}]+{wiki}*\\s+".format(br=SENTENCE_BREAKERS ,
                                                 wiki=WIKIPEDIA_REFERENCE)
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
        #self.mylog(self.LOOK_BEHIND) 
        result = [m.end() for m in self.SENTENCE_END_REGEX  .finditer(text)]
        # Sometimes the last position in the text will be matched twice, so filter duplicates.
        result = sorted(list(set(result)))
        #ui.message(str(result))
        self.mylog(result)
        self.mylog("'%s'" % text)
        s = "\r\n"
        r = re.compile("$")
        rr = [m.end() for m in r.finditer(s)]
        self.mylog("rr=%s" % str(rr))
        for i in xrange(1, len(result)):
            s = text[result[i-1]:result[i]]
            #self.mylog(s)
        return result
    
    def ifSentenceBreak(selfself, s, index):
        if s[index] not in self.SENTENCE_BREAKERS:
            return False
        try:
            nextChar = s[index+1]
        except IndexError:
            return True
        return nextChar in EMPTY_CHARACTERS

    def isSkippable(self, c):
        return unicodedata.category(c)[0] in "CPZ"
    
    def skipClass(self, s, i, unicodeClass):
        while (i < len(s)) and (unicodedata.category(s[i])[0] in unicodeClass):
            i += 1
        return i 
    
    """
    def splitParagraphIntoSentences(self, text):
        #begin = textInfo._startOffset
        #end = textInfo._endOffset
        #text = textInfo.text
        boundaries = [0]
        for i in xrange(len(text)):
            if text[i] not in self.SENTENCE_BREAKERS:
                continue
            # We just found the end of one sentence.
            # Lets move a little forward to find the beginning of the next one.
            i = self.skipClass(text, i, "P") # Skip all punctuation
            i2 = self.skipClass(text, i, "CZ") # Skip all whitespaces
            whitespaces = i2 - i
            i = i2
            if whitespaces > 0:
                boundaries.append(i)
        if boundaries[-1] !=len(text):
            boundaries.append(len(text))  
        return boundaries
    """
    
    def findEndOfSentence(self, textInfo, offset):
        text = textInfo.text 
        index = offset - textInfo._startOffset
        assert(index >= 0)
        #sentenceRe = re.compile("([.?!]\\B|$)")
        #if sentenceRe.search(text, ):
        

    def find_gt(a, x):
        'Find leftmost value greater than x'
        i = bisect_right(a, x)
        if i != len(a):
            return a[i]
        raise ValueError

    def script_nextSentence(self, gesture):
        """Move to next sentence."""
        self.move(1)
        
    def script_previousSentence(self, gesture):
        """Move to previous sentence."""
        self.move(-1)
        
    def move(self, increment):
        focus = api.getFocusObject()
        if hasattr(focus, "treeInterceptor") and hasattr(focus.treeInterceptor, "makeTextInfo"):
            focus = focus.treeInterceptor
        textInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
        #self.describe(textInfo)
        caretOffset = textInfo._getCaretOffset() 
        textInfo.expand(textInfos.UNIT_PARAGRAPH)
        caretIndex = caretOffset - textInfo._startOffset
        #ui.message(str(caretIndex))
        while True:
            text = textInfo.text
            boundaries = self.splitParagraphIntoSentences(text)
            #self.mylog(boundaries)
            #ui.message("Len=%d" % len(text))
            #ui.message(str(boundaries))
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
                tones.beep(440, 100)
                while True:
                    result = textInfo.move(textInfos.UNIT_PARAGRAPH, increment)
                    if result == 0:
                        ui.message("No next sentence")
                        return
                    textInfo.expand(textInfos.UNIT_PARAGRAPH)
                    if not speech.isBlank(textInfo.text):
                        break
                textInfo.expand(textInfos.UNIT_PARAGRAPH)
                # Imaginary caret just before this paragraph,
                # so that the next iteration will pick the very first sentence of this paragraph.
                if increment > 0:
                    caretIndex = -1
                else:
                    caretIndex = len(textInfo.text) 
                # Now control flow will takes us to another iteration of the outer while loop. 
        
    __gestures = {
        "kb:alt+DownArrow": "nextSentence",
        "kb:alt+UpArrow": "previousSentence",
    }
