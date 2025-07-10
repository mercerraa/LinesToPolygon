---
title: Lines to polygon
author:
- name: Andrew Mercer
  affiliation: Riksantikvarieämbetet
  email: mercerraa@gmail.com
date:  2025.07.10
lang: en-GB
papersize: a4
geometry:
- margin=2cm
- portrait
font: 11
mainfont: "Georgia"
indent: false
linestretch: 1.2
---

# Description

The plugin combines selected lines into one polygon if those lines are correctly snapped to each other.
It begins by checking the geometry of each line, using th PyQGIS geometry validator and then checks that each line connects to another and that lines do not cross.
If this check is clear a polygon is created.

# Why

RAÄ must update geometry for many protected sites which have been digitised from marker pen lines drawn on small scale maps.
This was deemed adequate at the time but has become more problematic.
Boundaries should best be defined by well described criteria, such as property boundaries, protection status or physically identifiable features of the landscape.
One boundary may be defined by different criteria along its length.
Each criteria should then be digitised as a line and all lines then combined to one polygon.
The polygon will not/cannot contain descriptions of each part but the original line data kan be archived for reference.