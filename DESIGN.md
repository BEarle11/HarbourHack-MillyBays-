# Objective

Given an image, determine the object in the image, create an effective
description of that object, determine its value, and produce a transcript for a
short 10-15 second Billy Mays style advertisement.

# Architecture

A **classifier** reads an image and then produces an item name and an item
description.

A **pricer** then examines the item name, description and image. It produces a
recommended price of the object based on the current time, geographical location,
and potentially, the history and current costs of this item.

A **writer** takes the item, name, description, image, and produces a transcript
for a Billy Mays style advertisement.

The **studio** takes the item name, description, image and transcript and
produces a short, 10 second Billy Mays style advertisement.








