# nvda-sentence-nav
SentenceNav is an NVDA add-on that allows you to read text by sentences, as opposed to by paragraphs or words.

Please note that "Jump to next  paragraph with text" feature has been move to [TextNav](http://github.com/mltony/nvda-text-nav/) add-on that needs to be installed separately.
## Keystrokes
* Alt+Down: Go to next sentence.
* Alt+Up: Go to previous sentence.
* NVDA+Alt+S: Speak current sentence.
* Alt+Windows+Down: Go to next phrase.
* Alt+Windows+Up: Go to previous phrase.

Please note that "Jump to next  paragraph with text" feature has been move to [TextNav](http://github.com/mltony/nvda-text-nav/) add-on that needs to be installed separately.

## Notes and known issues
* Sentence markup is done by heuristic algorithms and is not 100% accurate. Expect SentenceNav to occasionally make mistakes, such as breaking a sentence where it's not supposed to be broken or the other way around - missing a border between two sentences and speaking them together.
* Experimental support for Microsoft Word and WordPad has been added as of version 2.8.
* Sentence navigation keystrokes Alt+Up/Down might conflict with built-in keystrokes in applications. SentenceNav developers strive to resolve these conflicts whenever possible. However, if you encounter such a situation, a simple workaround is to press NVDA+F2 (Pass next key through), followed by the conflicting keystroke Alt+Up/Down to make sure that this keystroke would be processed by the application and not by SentenceNav.

## Algorithm
SentenceNav uses a regular expression to find sentence boundaries. The regular expression is looking for:
* One or more "Sentence breaker" punctuation marks, such as period, exclamation sign or question sign, followed immediately by one or more spaces.
* Sentence breakers can optionally be followed by one or more "Skippable" punctuation signs, such as closing parenthesis, or a quote.
* Sentence breakers can optionally be followed by a Wikipedia-style reference, e.g. [4], or [citation needed].
* Sentence breakers must not be preceded by any of the exceptional abbreviations, such as Dr., Mr., Prof., etc. Exceptional abbreviations are language-dependent. Exceptional abbreviations are defined as abreviations spelled with a period, which in most cases does not indicate the end of the sentence.
* Sentence breakers must not be preceded by a single capital letter. This is to prevent sentences being broken at people's initials, such as George R. R. Martin. The list of capital letters is language-dependent.
* Alternatively, the regular expression can match one of the full-width sentence breakers. Full-width punctuation is used in some languages, like Chinese and Japanese and there is no requirement to be followed or preceded by anything to be counted as the boundary of sentences.
* Alternatively, double new line counts as a sentence breaker.

Phrase detection is performed by another regular expression, that matches:
* One or more "phrase breakers" punctuation marks followed immediately by one or more spaces.
* Or alternatively, one or more "fixed-width" phrase brakers, with no requirement of being followed by spaces.
* Or alternatively, double new line.

## Other settings
* Reconstruct sentences across multiple paragraphs: sentences can span across multiple paragraphs. This often happnes in malformed PDF documents, or in email messages written as plain text. With this combo box you can tell SentenceNav to try to identify those sentences and speak them correctly. Sometimes however, it would speak paragraphs together that are not meant to be sentences. In this case you can disable that feature.
* Disable SentenceNav in applications: You can disable SentenceNav in certain applications. For example, some applications use Alt+Down keystroke to perform other functions. This is a comma-separated blacklist of applications where sentence navigation will be disabled. If you are not sure what should be the name of your application, switch to that application, Press NVDA+Control+Z to open up NVDA console and type: "focus.appModule.appName" without quotes to obtain the name of current application.

## Source code
Source code is available at <http://github.com/mltony/nvda-sentence-nav>.

## Downloads
* Current stable version: [SentenceNav](https://github.com/mltony/nvda-sentence-nav/releases/latest/download/SentenceNav.nvda-addon)
* Last Python 2 version (compatible with NVDA 2019.2 and prior): [SentenceNav v2.5](https://github.com/mltony/nvda-sentence-nav/releases/download/v2.5/SentenceNav-2.5.nvda-addon)

