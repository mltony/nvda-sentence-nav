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
* SentenceNav doesn't work in Microsoft Word, WordPad as well as any applications that use Microsoft Word editable controls internally, such as Microsoft Outlook. Sentence navigation in these programs is provided by NVDA, rather than SentenceNav. Phrase navigation is not available.
* Sentence navigation keystrokes Alt+Up/Down might conflict with built-in keystrokes in applications. SentenceNav developers strive to resolve these conflicts whenever possible. However, if you encounter such a situation, a simple workaround is to press NVDA+F2 (Pass next key through), followed by the conflicting keystroke Alt+Up/Down to make sure that this keystroke would be processed by the application and not by SentenceNav.
* SentenceNav doesn't work in some applications, such as LibreOffice and edit control in Mozilla Thunderbird. This is caused by [NVDA issue](https://github.com/nvaccess/nvda/issues/9005).

## Algorithm
SentenceNav uses a regular expression to find sentence boundaries. The regular expression is looking for:
* One or more "Sentence breaker" punctuation marks, such as period, exclamation sign or question sign, followed immediately by one or more spaces.
* Sentence breakers can optionally be followed by one or more "Skippable" punctuation signs, such as closing parenthesis, or a quote.
* Sentence breakers can optionally be followed by a Wikipedia-style reference, e.g. [4], or [citation needed].
* Sentence breakers must not be preceded by any of the exceptional abbreviations, such as Dr., Mr., Prof., etc. Exceptional abbreviations are language-dependent. Exceptional abbreviations are defined as abreviations spelled with a period, which in most cases does not indicate the end of the sentence.
* Sentence breakers must not be preceded by a single capital letter. This is to prevent sentences being broken at people's initials, such as George R. R. Martin. The list of capital letters is language-dependent.
* Alternatively, the regular expression can match one of the full-width sentence breakers. Full-width punctuation is used in some languages, like Chinese and Japanese and there is no requirement to be followed or preceded by anything to be counted as the boundary of sentences.

Phrase detection is performed by another regular expression, that matches:
* One or more "phrase breakers" punctuation marks followed immediately by one or more spaces.
* Or alternatively, one or more "fixed-width" phrase brakers, with no requirement of being followed by spaces.

## Other settings
* Reconstruct sentences across multiple paragraphs: sentences can span across multiple paragraphs. This often happnes in malformed PDF documents, or in email messages written as plain text. With this combo box you can tell SentenceNav to try to identify those sentences and speak them correctly. Sometimes however, it would speak paragraphs together that are not meant to be sentences. In this case you can disable that feature.
* Disable SentenceNav in applications: You can disable SentenceNav in certain applications. For example, some applications use Alt+Down keystroke to perform other functions. This is a comma-separated blacklist of applications where sentence navigation will be disabled. If you are not sure what should be the name of your application, switch to that application, Press NVDA+Control+Z to open up NVDA console and type: "focus.appModule.appName" without quotes to obtain the name of current application.

## Source code
Source code is available at <http://github.com/mltony/nvda-sentence-nav>.

## Release history and downloads
* Current stable release: [v2.2](https://github.com/mltony/nvda-sentence-nav/releases/download/v2.2/SentenceNav-2.2.nvda-addon) - 01/20/2019
  * Better paragraph compatibility logic for reconstructing sentences across paragraphs.
  * Translations.
* [v2.1](https://github.com/mltony/nvda-sentence-nav/releases/download/v2.1/SentenceNav-2.1.nvda-addon) - 12/25/2018
  * Added support for skim reading.
  * Added support for LibreOffice.
  * Improved initials detection.
  * Sentence and phrase breakers can now contain hyphens.
  * Exceptional abbreviations can now contain special characters, such as periods.
  * Added compatibility flags.
  * Translations: bg, de, es, fi, fr, gl, he, it, pt_PT, sk, tr, zh_CN.
* [v2.0](https://github.com/mltony/nvda-sentence-nav/releases/download/v2.0/SentenceNav-2.0.nvda-addon) - 11/08/2018
  * Complete rewrite of SentenceNav.
  * Added ability to reconstruct sentences spanning across multiple paragraphs.
  * Added configuration dialog.
  * Added language-specific abbreviations.
  * Now sentences are spoken as formatted text instead of plain text preserving links and other formatting elements.
  * Added a keystroke to speak current sentence.
  * Added phrase navigation.
  * "Jump to next paragraph with text" functionality has been moved to a separate [TextNav](http://github.com/mltony/nvda-text-nav/) add-on.
  * Added support to disable SentenceNav for a blacklist of applications.
  * Bugfixes.
* [v1.1](https://github.com/mltony/nvda-sentence-nav/releases/download/v1.1/SentenceNav-1.1.nvda-addon) - 03/23/2018
  * Added move to text keystrokes.
  * Bug fixes:
      * Sentence navigation now works in WordPad and other rich text edit fields.
      * Works better with Chinese language.
* [v1.0](https://github.com/mltony/nvda-sentence-nav/releases/download/v1.0/SentenceNav-1.0.nvda-addon)
  * Initial release.



## Feedback
If you have any questions or comments, or if you find this addon useful, please don't hesitate to contact me at anton.malykh *at* gmail.com.
