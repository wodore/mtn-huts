#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 21:58:56 2020

@author: tobias
"""

from lxml import etree
import subprocess
import os

def remove(tree, day, percent, suffix="day"):
    """Removes svg objects by ID (generates as follows <suffix><day>-<percent>)."""
    _id = "{}{}-{}".format(suffix, day, percent)
    for obj in ["path", "circle", "ellipse", "g"]:
        try:
            to_remove = tree.xpath("/svg:svg/svg:g/svg:{}[@id=\"{}\"]".format(obj, _id),
                                   namespaces={"svg": "http://www.w3.org/2000/svg"})[0]
        except IndexError:
            continue
        g = to_remove.getparent()
        g.remove(to_remove)
        
        
def keep(tree, day, percent, suffix="day"):
    """Keep element and remove all others (depending on percent)."""
    percents = [-1, 0, 25, 50, 75, 100]
    percents.remove(percent)
    for percent in percents:
        remove(tree, day, percent, suffix)
        
def update_icon(tree, percents, path_without_svg, keep_svg=False):
    if not len(percents) == 4:
        print("ERROR: percents needs to be a list with 4 values.")
    for day in [0, 1, 2, 3]:
        keep(tree, day, percents[day])
    keep(tree, "", percents[0], "hut")
    p = percents
    out_svg = "{}-{}-{}-{}-{}.svg".format(path_without_svg, p[0], p[1], p[2], p[3])
    with open(out_svg, "wb") as o:
        o.write(etree.tostring(tree, pretty_print=True))
        
    p=subprocess.call(['inkscape', out_svg, '--export-png', out_svg.replace(".svg", ".png")])
    
    if not keep_svg:
        os.remove(out_svg)



# RUN SCRIPT (takes some time if all icons are generated)
all_percents = [-1, 25, 50, 75, 100]
names = ["hut-sac","hut-private","biwak-sac","biwak-private"]

for name in names:
    print("Generate '{}' icons.".format(name))
    print(30*"~")
    for ap0 in all_percents:
        for ap1 in all_percents:
            for ap2 in all_percents:
                for ap3 in all_percents:
                    tree = etree.parse(open(name + ".svg"))
                    update_icon(tree,[ap0, ap1, ap2, ap3], "generated/"+name)   
