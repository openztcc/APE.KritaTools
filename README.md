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

**Windows:**

Drop contents directly into `%APPDATA%\krita\pykrita\`

**Linux:**

Drop contents directly into `~/.local/share/krita/pykrita/`

**Enable the plugin:**

Open Krita and go to `Settings > Configure Krita > Python Plugin Manager` - Enable APE.KritaTools.

Go to `Tools > Load APE image into Krita`. It will ask you to find the extensionless graphic first (i.e. SE, NE, N,  etc), and then again will ask you to open the pal file associated with it. There won't be a prompt for the second one, it will just open another dialog window to search for the file.

Current issues as of v1.0.0

- No save function yet

Much thanks to Jeff Bostoen's detailed specification of the ZT1 graphics format here: https://github.com/jbostoen/ZTStudio/wiki/ZT1-Graphics-Explained
