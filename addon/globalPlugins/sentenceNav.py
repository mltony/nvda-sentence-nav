import api
import bisect
import browseMode
import controlTypes
import config
import ctypes
import globalPluginHandler
import NVDAHelper
from NVDAObjects.IAccessible import IAccessible 
from NVDAObjects.IAccessible import mozilla
from NVDAObjects.window import winword

from NVDAObjects.UIA.wordDocument import WordDocument
import operator
import re 
import speech
import struct
import textInfos
import tones
import ui
import unicodedata

MY_LOG_NAME = "C:\\Users\\tony\\1.txt" 
open(MY_LOG_NAME, "w").close()

def mylog(s):
    f = open(MY_LOG_NAME, "a")
    f.write(unicode(s).encode('utf8'))
    f.write("\n")        
    f.close()

def describe(obj):
    mylog(str(obj))
    mylog(str(type(obj)))
    import inspect
    mylog(inspect.getmro(type(obj)))
    for s in dir(obj):
        try:
            value = eval("obj.%s" % s)
            value = str(value)
        except:
            value = "."
        mylog("%s = %s" % (str(s), value))



ctr = 0

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    browserNames = set("firefox,chrome,iexplore,microsoftedge".split(","))
    cc = set()
    appNames = set()
    def chooseNVDAObjectOverlayClasses (self, obj, clsList):
        """
        for c in clsList:
            if issubclass(c, browseMode.BrowseModeDocumentTreeInterceptor):
                tones.beep(200, 50)
        
        if isinstance(obj, browseMode.BrowseModeDocumentTreeInterceptor):
            tones.beep(200, 50)
        try:
            if obj.treeInterceptor is not None:
                if isinstance(obj.treeInterceptor, browseMode.BrowseModeDocumentTreeInterceptor):
                    tones.beep(200, 50)
        except:
            pass
"""  
        if obj.appModule.appName in self.browserNames:
            #tones.beep(200, 50)
            clsList.insert (0, SentenceNavigator)
            return
        
        
        self.appName = str(obj.appModule.appName)
        self.appNames.add(obj.appModule.appName) 
        if mozilla.Mozilla in clsList: 
            #tones.beep(200, 50)
            pass
        if WordDocument in clsList:
            tones.beep(200, 100)
        if winword.WordDocument in clsList:
            for c in clsList:
                #describe(c)
                pass
            tones.beep(800, 100)
            return
        try:
            self.obj = obj
            self.appName = obj.IA2Attributes
            #tones.beep(200, 10)
        except:
            self.appName = None
            
        #focus = api.getFocusObject()
        if obj.windowClassName == "NetUIHWND":
            #tones.beep(1000, 50)
            pass
        #if isinstance(focus, winword.WordDocument):
            #return

        if obj.role == controlTypes.ROLE_EDITABLETEXT or mozilla.BrokenFocusedState in clsList:
            #mozilla.Mozilla
            #            mozilla.BrokenFocusedState
            #mozilla.Document
            clsList.insert (0, SentenceNavigator)
            
    def script_status(self, gesture):
        ui.message(self.appName)
        for appName in self.appNames:
            mylog(appName)
            
    __gestures = {
        "kb:NVDA+Control+X": "status",
        }

            
class SentenceNavigator(IAccessible): 
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
        self.mylog(str(type(obj).__bases__))
        for s in dir(obj):
            self.mylog(str(s))

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
                focus.treeInterceptor.script_collapseOrExpandControl(gesture)
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
                self.fancyBeep()
                while True:
                    result = textInfo.move(textInfos.UNIT_PARAGRAPH, increment)
                    if result == 0:
                        ui.message("No next sentence")
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
        
    def fancyBeep(self):
        beepLen = 100 
        freqs = [400,500, 600]
        intSize = 8 # bytes
        bufSize = max([NVDAHelper.generateBeep(None,freq, beepLen, 50, 50) for freq in freqs])
        if bufSize % intSize != 0:
            bufSie +=intSize
            bufSize -= (bufSize % intSize)
        tones.player.stop()
        bbs = []
        result = [0] * (bufSize/intSize)
        for freq in freqs:
            buf = ctypes.create_string_buffer(bufSize)
            NVDAHelper.generateBeep(buf, freq, beepLen, 50, 50)
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
    
    def initOverlayClass (self): 
        for key, value in self.__gestures.iteritems():
            self.bindGesture (key, value) 
