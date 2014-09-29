Purpose of files
---

This directory contains several binary SPE files for testing and illustration
purposes. All the files were taken with the same settings at the same day.

The program should be tested on files, whose filename starts with
"`data-sample`".

The files, whose names start with "`calibration-`", can be used for wavenumber
calibration with package `xcal_raman` (e.g. "`calibration-polystyrene.SPE`"
together with "`calibration-dark.SPE`"). "`calibration-dark.SPE`" is used
for dark current correction during the wavenumber calibration. You should not
open these files directly, instead mention two of them in your configuration
file "`.speview.conf`".

The same applies for "`data-dark.SPE`", which is used for the dark current
correction of other "`data-sample`" files. If you use background subtraction,
mention it in your config.

Directory structure
---
The names are self-explanatory

```
testdata
├── calibration-cyclohexane.SPE
├── calibration-dark.SPE
├── calibration-polystyrene.SPE
├── data-dark.SPE
├── data-sample_1-plastic.SPE
├── data-sample_2-polystyrene_plate.SPE
├── data-sample_3-paracetamol.SPE
├── data-sample_4-plastic.SPE
└── data-sample_5-paper.SPE
```

