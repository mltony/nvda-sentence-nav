# nvda-sentence-nav
SentenceNav is an NVDA add-on that allows you to read text by sentences, as opposed to by paragraphs or words.

Please note that "Jump to next  paragraph with text" feature has been move to [TextNav](http://github.com/mltony/nvda-text-nav/) add-on that needs to be installed separately.
## Download
Current stable release: [SentenceNav v1.1](https://github.com/mltony/nvda-sentence-nav/releases/download/v1.1/SentenceNav-1.1.nvda-addon).

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
## Source code
Source code is available at <http://github.com/mltony/nvda-sentence-nav>.

## Release history
* v2.0 - TBD
  * Complete rewrite of SentenceNav.
  * Added ability to reconstruct sentences spanning across multiple paragraphs.
  * Added configuration dialog.
  * Added language-specific abbreviations.
  * Now sentences are spoken as formatted text instead of plain text preserving links and other formatting elements.
  * Added a keystroke to speak current sentence.
  * Added phrase navigation.
  * "Jump to next paragraph with text" functionality has been moved to a separate [TextNav](http://github.com/mltony/nvda-text-nav/) add-on.
  * Added support to disable SentenceNav for some applications.
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
