#!/bin/ksh

PALPATH=./Broica.dp
KITTHEME=./test.conf
NCOLORS=8

# convert 12-digit hex color to 6-digit
function tts {
    str=$1
    str="${str:1}"
    echo "#${str:0:2}${str:4:2}${str:8:2}"
}

python nscde-kitty-integ.py $PALPATH ~/.garble/conf.conf $NCOLORS --silent

