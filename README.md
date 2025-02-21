# APE.KritaTools

ZT1 graphics parser for Krita. An extension for Krita to read Zoo Tycoon 1 graphics files.

## Download Krita (it's free):

https://krita.org/en/

## Download

Clone this repository:

```bash
git clone https://github.com/openztcc/APE.KritaTools.git
```

## To install:

### Easy way:

Download the latest release from the releases page:
https://github.com/openztcc/APE.KritaTools/releases/

Open Krita and go to `Tools > Scripts > Import Python Plugin...` and select the downloaded zip file. It will install the plugin for you.

### Manual way:

**Windows:**

Drop contents directly into `%APPDATA%\krita\pykrita\`

**Linux:**

Drop contents directly into `~/.local/share/krita/pykrita/`

**Enable the plugin:**

Open Krita and go to `Settings > Configure Krita > Python Plugin Manager` - Enable APE.KritaTools.

## Usage

- Open Krita
- Go to the "Tools" menu
- Click on "Scripts" and then "Load APE Image into Krita"
- Choose the ZT1 image you want to import
- Accept default palette or uncheck "Use Embedded Palette" to select a new one.
- Import

## Known issues as of v1.1.0

- No save function yet

## Credits

- Much of the basis of this project could not be done without Jeff Bostoen's detailed specification of the ZT1 graphics format here: https://github.com/jbostoen/ZTStudio/wiki/ZT1-Graphics-Explained
- A lot of of structure names are inspired by Mad Scientist's original Zoot documentation on the file format which was also used as reference.
- Big thanks to Jay for answering my questions about the ZT1 format! Helped me solve a lot of headaches with frame alignments.