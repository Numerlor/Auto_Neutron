# Contributing translations

Translations can be contributed as PRs containing the .po files to this repository.

To create translations, you can use tools like [POEdit](https://poedit.net/), or manually translate in the files.

Each directory under this directory represents a single language code, where the LC_MESSAGES sub dir contains the translations of the messages.

So for example to create a de_DE translation you'd create a de_DE directory and put your translations in there.

As the release distributions don't contain locale data for locales which are not contained in them, to see your translations you either have to run the application from source, or download the data online and paste it into the directory release of Auto_Neutron.

To download the data online, go to https://pypi.org/project/Babel/#files, download tarball, extract it and merge the babel/locale-data directory from the main directory in the tarball with Auto_neutron's babel/locale-data irectory.

After you do this, copy your compiled translations into Auto_Neutron's locale directory as specified above, and you should be able to choose the language in the settings.


With a poetry environment initialized, Auto_Neutron defines a few utility task that are runnable with `poetry run task`\
`i18n-init` initializes a directory containing a .po file to translate, takes the language code as the argument\
`i18n-compile` compiles all the .po files in the locale directory\
`i18n-update` updates the all the .po files after a new .pot file is extracted\
`i18n-extract` extracts the .pot file from the project source
