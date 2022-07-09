# nvda-sentence-nav
SentenceNav 是一个 NVDA 的插件，可以让您以句子为单位阅读文本，而不是按段落或单词。


注意，“跳转到下一段文本”的功能已移至 [TextNav](http://github.com/mltony/nvda-text-nav/) 插件，需要单独安装。

## 按键
* Alt+Down：跳转到下一个句子。
* Alt+Up：跳转到上一个句子。
* NVDA+Alt+S：读出当前句子。
* Alt+Windows+Down：跳转到下一个短语。
* Alt+Windows+Up：跳转到上一个短语。


## 注释和已知问题
* 句子标记由启发式算法完成，并非 100% 准确。在个别情况下 SentenceNav 可能会出错，例如，对不应该被拆分成两个句子的文本进行了拆分，或者相反而一次性读出了两个句子。
* 自 2.8 版起添加了对 Microsoft Word 和 WordPad 的实验性支持。
* 句子导航的快捷键 Alt+Up/Down 可能与某些应用程序中的快捷键冲突。 SentenceNav 开发者尽可能解决这些冲突。但是，如果您遇到这种情况，一个简单的解决方法是按 NVDA+F2（忽略下一次 NVDA 按键），然后按 Alt+Up/Down 以确保把该按键传递给应用程序本身。

## 算法

SentenceNav 使用正则表达式来查找句子边界。正则表达式可以查找以下位置：

* 一个或多个“断句”标点符号，例如句号、感叹号或问号，后面紧跟一个或多个空格。
* 断句后可以选择性跟随一个或多个“可跳过”标点符号，例如右括号或引用。
* 断句后可以选择性跟随一个维基百科风格的参考，例如[4] 或 [citation needed]。
* 断句前不得有任何特殊缩写，例如 Dr.、Mr.、Prof. 等。往往特殊缩写取决于特定语言，多数情况下特殊缩写包含句号，但其并不表示句子的结束。
* 断句前不得包含一个大写字母。这是为了防止因人名的首字母大写而错误的将其拆分为单独的句子，例如 George R. R. Martin。大写字母列表取决于特定语言。
* 或者，正则表达式可以匹配全角断句。中文、日文等语言使用全角标点符号，无需句号前后包含特定字符来作为句子的边界。
* 双换行也算作断句符。

## 短语检测由另一个匹配的正则表达式完成：
* 一个或多个“短语断句”符号后紧跟一个或多个空格。
* 一个或多个“短语断句”符号后无需跟随空格。
* 两个换行。

## 其他设置
* 跨段落重建句子：一个句子可以跨多个段落。这种情况常见于格式错误的 PDF 文档或以纯文本形式编写的电子邮件中。使用此组合框，您可以告诉 SentenceNav 尝试识别这些句子并正确读出。然而，有时它会错误的将不应该是同一个句子的段落识别为一个句子。在这种情况下，您可以禁用该功能。
* 在应用程序中禁用句子导航：您可以在某些应用程序中禁用 SentenceNav。例如，某些应用程序使用 Alt+Down 按键来执行其他功能。这是一个逗号分隔的应用程序黑名单，表示句子导航在这些应用程序中将被禁用。如果您不确定应用程序的名称，请切换到该应用程序，按 NVDA+Control+Z 打开 NVDA 控制台并键入：“focus.appModule.appName”（不带引号）以查看当前应用程序的名称。

## 源代码

源代码可在 <http://github.com/mltony/nvda-sentence-nav> 获取。

## 下载
* 当前稳定版本：[SentenceNav](https://github.com/mltony/nvda-sentence-nav/releases/latest/download/SentenceNav.nvda-addon)
* 最后一个 Python 2 版本（与 NVDA 2019.2 及之前版本兼容）：[SentenceNav v2.5](https://github.com/mltony/nvda-sentence-nav/releases/download/v2.5/SentenceNav-2.5.nvda-addon)
