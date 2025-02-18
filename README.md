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

Drop contents directly into `%APPDATA%\krita\pykrita\`

Open Krita and go to `Settings > Configure Krita > Python Plugin Manager` - Enable APE.KritaTools.

Go to `Tools > Load APE image into Krita`. It will ask you to find the extensionless graphic first (i.e. SE, NE, N,  etc), and then again will ask you to open the pal file associated with it. There won't be a prompt for the second one, it will just open another dialog window to search for the file.

Current issues as of v0.4.0:

- Not very intuitive to use yet
- No save function yet
- Possible issues with memory management. Might need to restart app if new graphic need loaded.

Much thanks to Jeff Bostoen's detailed specification of the ZT1 graphics format here: https://github.com/jbostoen/ZTStudio/wiki/ZT1-Graphics-Explained
