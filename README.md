[![license-shield]][license-url]
[![pylama-failed]][pylama-url]
![project-status-progress]

🔨 **Note**: major refactoring of the code is planned

<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ghrimx/InspectorMate.git">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">InspectorMate</h3>

  <p align="center">
    InspectorMate provides a central place to inspector to gather all the information needed to conduct a successful inspection.
    <br />
    <a href=[documentation-url]><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ghrimx/InspectorMate/issues">Report Bug</a>
    ·
    <a href="https://github.com/ghrimx/InspectorMate/issues">Request Feature</a>
  </p>
</div>

<!-- ABOUT THE PROJECT -->
## About The Project

![main-layout]

InspectorMate is a Windows desktop application designed to streamline the workflow for inspectors. It offers tools for organizing folders, managing document requests, findings, and questions, and includes a rich text editor. The app references documents from monitored folders and supports viewing various file types. With a flexible layout, users can easily view documents while taking notes, ensuring efficient and organized inspections.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Static Badge](https://img.shields.io/badge/Python_3-blue?style=flat-square)][Python-url]
* [![Static Badge](https://img.shields.io/badge/PyQt6-green?style=flat-square)][PyQt-url]
* [![Static Badge](https://img.shields.io/badge/SQLite-blue?style=flat-square)](https://www.sqlite.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- FEATURES -->
## Features

- **View Multiple File Formats**: Safely view various file types, including Microsoft Office formats (requires MS Office suite), with no risk of altering the original files. Convert Office documents and text files to PDF for secure, unchangeable viewing. (Supported formats: .pdf, .txt, .md, .png, .jpeg, .jpg, .docx, .doc, .xlsx, .xls, .ppt, .pptx)  
- **Import Tags from OneNote**: Seamlessly import tags from specific OneNote sections for efficient categorization.
- **Bulk Import of "Signage"**: Import data from multiple Excel files simultaneously, streamlining the signage management process.
- **Export to Excel**: Easily export requests, findings, and questions into structured Excel files for reporting or further analysis.
- **Recursive Zip File Extraction**: Unpack zip files recursively, ensuring that all nested content is extracted.
- **Embedded PDF Extraction**: Automatically unpack embedded PDFs within files for quick access.
- **Excel Sheet Merging**: Merge multiple Excel sheets into a single document, simplifying data consolidation.
- **Create Stylish Notes**: Write detailed, beautifully formatted notes using the rich text editor, and save them as clean HTML files for easy sharing and access.
- **Automatic Reference Key Detection**: Effortlessly detect reference keys from filenames or folder names to streamline document organization.
- **Smart Reference Key Increment**: Automatically increment signage reference key, with or without a prefix, ensuring consistency in document tracking.
- **File Access Flexibility**: Open files seamlessly, even if they've been renamed or moved, maintaining a smooth workflow without manual re-linking.

*to come* : visualize and annotate database extract from Excel or csv

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

*"Signage"* refers to key elements like document requests, findings, and questions. Unlike simple tags or labels, signage items have a defined lifecycle (e.g., Open, Closed, On Hold), allowing for more dynamic tracking and management. 

Document requests, referred to as "requests," are organized within a dedicated tab for streamlined access and handling.

A *"workspace"* is a dedicated folder where all files and folders related to an inspection are systematically organized. When setting up a workspace, two primary folders are created: “Evidence” and “Notebook.” The “Evidence” folder serves as the repository for documents received in response to requests, from which the app will generate references. The “Notebook” folder is designated for note files, which have the “.phv” extension. Additionally, the “Notebook” folder contains a “.image” subfolder that stores all images copy-pasted into note files.

### Create Workspace
![create-workspace]

### Drag and Drop frames to organize the layout
![flexible-layout]

### Create a request from anywhere in the app

The popup dialog (shortcut *"ctrl + R"* or via *File menu*) provides an interface for selecting the signage type, with "request" set as the default option. The reference key (refkey) is automatically incremented based on the chosen signage type and any specified prefix, ensuring consistent and organized tracking.

![create-request]

### Capture the screen and keep the document reference with it

The built-in screen capture tool enables users to capture and paste images along with citations directly into internal notes. The citation, automatically placed below the image, includes essential details such as the reference key, title, subtitle, reference, and current page number. When the capture is pasted into other applications the image is transferred without the accompanying citation.

![screen-capture]

### Annotate table item (use shortcuts for quick formatting)

You can create a note for any item organized in a table by using the Note tab in the right pane. An icon will appear in the first column of the item to indicate that a note is associated with it.

![annotate-table-item]

### Explore the content of the workspace folder and open any file in the default app

Effortlessly navigate your workspace files and folder structure with the intuitive popup panel located on the left side of the interface. This panel provides a view of your directories within your workspace, making it easy to find what you need without hassle. The "Explorer" panel allows you to open any file with ease, using the default system applications. The "Notebook" tab offers quick access to your notes. To create new notes, right-click within the panel to open the context menu that provides additional options to manage your notes and files.

![explore-workspace]

### Write note

Right-click within the "Explorer" or "Notebook" panel to open the context menu. Use the system file dialog to create folders and files. When you create a note, it is saved by default in the Notebook folder assigned during the workspace setup. Note files have the “.phv” extension, but they are standard HTML files that can be opened with any web browser.

![write-note]

*For more examples, please refer to the [Documentation](wiki)*

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Known issues

### OneNote COM error
If the app failed to connect to OneNote try the following workarounds:

#### Workaround 1: Delete the registry key
run regedit.exe, and navigate to
```HKEY_CLASSES_ROOT\TypeLib\{0EA692EE-BB50-4E3C-AEF0-356D91732725}```

There should only be one subfolder in this class called 1.1.
If you see 1.0 or any other folders, you'll need to delete them.

The final hierarchy should look like this:
```
|- {0EA692EE-BB50-4E3C-AEF0-356D91732725}
|     |- 1.1
|         |-0
|         | |- win32
|         |- FLAGS
|         |- HELPDIR
```

Alternatively use the following powershell script

```
$path 'HKEY_CLASSES_ROOT\TypeLib\{0EA692EE-BB50-4E3C-AEF0-356D91732725}\1.0'

if (Test-Path -Path registry::$path){
  Get-Item registry::$path | Remove-Item -Verbose
}
```

#### Workaround 2: Delete gen_py
Clear the content of ```C:\Users\<username>\AppData\Local\Temp\gen_py```

Type ```%temp%``` in the address bar in FileExplorer and delete the folder ```gen_py```.

### HyperLink warning in OneNote
1. In the Registry Editor, locate the following subkey:

```HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Common```

2. On the menu bar, click Edit > New > Key and type ```Security``` and press Enter.

3. Right click Security, then click New > DWORD (32-bit) Value and type ```DisableHyperlinkWarning``` and press Enter.

4. Double click the above value, select Decimal and change the Value data to ```1```, then click OK.



<!-- CONTRIBUTING -->
## Contributing

Contributions are welcome, and they are **greatly appreciated**! Every little bit helps, and credit will always be given.

You can contribute in many ways:

### Report Bugs

Report bugs at https://github.com/ghrimx/InspectorMate/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Implement Features

If you have a suggestion that would make this better, please fork the repo and create a pull request (see [Get Started](#get-started)). You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/ghrimx/InspectorMate/issues.


### Write Documentation

InspectorMate could always use more documentation, whether as part of the official InspectorMate docs, in docstrings, or even on the web in blog posts, articles, and such.

### Get Started!

Ready to contribute? Here's how to set up `InspectorMate` for local development.

1. Fork the `InspectorMate` repo on GitHub.
2. Clone your fork locally:

    - `git clone git@github.com:your_name_here/InspectorMate.git`

3. Install your local copy into a virtualenv. Assuming you have "venv" installed, this is how you set up your fork for local development:

    - `python -m venv /path/to/new/virtual/environment`
    - `.\venv\Scripts\activate`
    - `cd InspectorMate`
    - `pip install -r .\requirements.txt`

4. Create a branch for local development:

    - `git checkout -b name-of-your-bugfix-or-feature`

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass `pylama` and the tests:

    - `pylama .\src > pylama_outcome.txt`
    - `pytest -rA .\tests`

   To get pylama, just pip install it into your virtualenv. Check `pylama.ini` for linters.

   Tips: to run a subset of tests `pytest -rA .\test\<test-file>.py -k "test_<method-name>"`

6. Commit your changes and push your branch to GitHub::

    - `git add .`
    - `git commit -m "Your detailed description of your changes."`
    - `git push origin name-of-your-bugfix-or-feature`

7. Submit a pull request through the GitHub website.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributors

None yet. Why not be the first?

💖 Help will be greatly appreciated for issue [#01](https://github.com/ghrimx/InspectorMate/issues/1#issue-2524412537)

<!-- LICENSE -->
## License

Distributed under the GPL-3.0 license. See [LICENSE.txt][license-url] for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact
The best way to get in touch is to file an issue at https://github.com/ghrimx/InspectorMate/issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) by Riverbank Computing. License under GPL license.
* [Fugue Icons](http://p.yusukekamiyamane.com/) by Yusuke Kamiyamane. Licensed under a Creative Commons Attribution 3.0 License.
* [Remix Icon](https://remixicon.com/) Licensed under Apache License.
* [Qt Advanced Docking System](https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System/) Licensed under LGPL-2.1 license.
* [PyMuPDF](https://pypi.org/project/PyMuPDF/) by Artiflex. Licensed under GNU AFFERO GPL 3.0.
* [PyQt-Template](https://github.com/gciftci/PyQT-Template.git) Licensed under MIT license. 
* [one-py](https://github.com/varunsrin/one-py/tree/master) Licensed under MIT license.
* [QtWaitingSpinner](https://github.com/fbjorn/QtWaitingSpinner.git) Licensed under MIT license.
* [html2text](https://github.com/Alir3z4/html2text.git) by Aaron Swartz. Licensed under GPL-3.0 license
* [openpyxl](https://openpyxl.readthedocs.io/en/stable/) Licensed under MIT license.
* [pywin32](https://github.com/mhammond/pywin32) by  Mark Hammond (et al). Licensed under Python Software Foundation License (PSF)
* [pandas](https://pandas.pydata.org/) Licensed under BSD License (BSD 3-Clause License Copyright (c) 2008-2011, AQR Capital Management, LLC, Lambda Foundry, Inc. and ...) 

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/ghrimx/InspectorMate.git/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/ghrimx/InspectorMate.git/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/ghrimx/InspectorMate.git/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/ghrimx/InspectorMate.git/issues
[license-shield]: https://img.shields.io/badge/License-GPL--3.0-yellow?style=flat-square
[license-url]: LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Python-url]: https://www.python.org/
[Python-logo]: images/python-logo@2x.png
[PyQt-url]: https://www.riverbankcomputing.com/software/pyqt/
[PyQt-logo]: images/Qt_logo.png
[InspectorMate-logo]: images/logo.png
[Remix-Icon]:https://remixicon.com/
[main-layout]: images/main.PNG
[usage-1]: images/usage-1.PNG
[screen-capture]: images/screen-capture.gif
[create-request]: images/create-request.gif
[flexible-layout]: images/flexible-layout.gif
[annotate-table-item]: images/annotate-table-item.gif
[explore-workspace]: images/explore-workspace.gif
[write-note]: images/write-note.gif
[pylama-failed]: https://img.shields.io/badge/Pylama-failed-red?style=flat-square
[pylama-passed]: https://img.shields.io/badge/Pylama-passed-green?style=flat-square
[pylama-url]: https://pypi.org/project/pylama/
[project-status-progress]: https://img.shields.io/badge/Project--Status-In_Progress-orange?style=flat-square
[project-status-maintanance]: https://img.shields.io/badge/Project--Status-Maintanance-blue?style=flat-square
[create-workspace]: images/create-workspace.gif
[documentation-url]: wiki


