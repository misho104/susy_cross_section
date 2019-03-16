#!/bin/sh

X=python
C=run_nllfast.py

DIR=./nllfast-cache
README=README
ARCHIVE=nllfast-cache.tar.gz

mkdir -p $DIR

E=7TeV
P=gdcpl; $X $C $E $P mstw  205:2000:2                | cut -f1,4   | tee $DIR/$E.gg.decoup.cache
P=sdcpl; $X $C $E $P mstw  105:2000:2                | cut -f1,4   | tee $DIR/$E.sb10.decoup.cache
P=st;    $X $C $E $P mstw  105:1000:2                | cut -f1,4   | tee $DIR/$E.${P}.cache
P=sb;    $X $C $E $P mstw  205:2000:18 205:2000:18   | cut -f1,2,5 | tee $DIR/$E.sb10.cache
P=ss;    $X $C $E $P mstw  205:2000:18 205:2000:18   | cut -f1,2,5 | tee $DIR/$E.ss10.cache
P=gg;    $X $C $E $P mstw  205:2000:18 205:2000:18   | cut -f1,2,5 | tee $DIR/$E.${P}.cache
P=sg;    $X $C $E $P mstw  205:2000:18 205:2000:18   | cut -f1,2,5 | tee $DIR/$E.${P}.cache
P=gg;    $X $C $E $P mstw 2105:4500:18 205:1500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.high.cache
P=sg;    $X $C $E $P mstw 2105:3500:18 205:1500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.high.cache

E=8TeV
P=gdcpl; $X $C $E $P mstw  205:2500:2                | cut -f1,4   | tee $DIR/$E.gg.decoup.cache
P=sdcpl; $X $C $E $P mstw  205:2500:2                | cut -f1,4   | tee $DIR/$E.sb10.decoup.cache
P=st;    $X $C $E $P mstw  105:2000:2                | cut -f1,4   | tee $DIR/$E.${P}.cache
P=sb;    $X $C $E $P mstw  205:2500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.sb10.cache
P=ss;    $X $C $E $P mstw  205:2500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.ss10.cache
P=gg;    $X $C $E $P mstw  205:2500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.cache
P=sg;    $X $C $E $P mstw  205:2500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.cache
P=gg;    $X $C $E $P mstw 2605:4500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.high.cache
P=sg;    $X $C $E $P mstw 2605:4500:18 205:2500:18   | cut -f1,2,5 | tee $DIR/$E.${P}.high.cache


E=13TeV
P=gdcpl; $X $C $E $P 505:3000:2                | cut -f1,3   | tee $DIR/$E.gg.decoup.cache
P=sdcpl; $X $C $E $P 505:3000:2                | cut -f1,3   | tee $DIR/$E.sb10.decoup.cache
P=st;    $X $C $E $P 105:3000:18 505:5000:18   | cut -f1,2,4 | tee $DIR/$E.${P}.cache
P=sb;    $X $C $E $P 505:3000:18 505:3000:18   | cut -f1,2,4 | tee $DIR/$E.sb10.cache
P=ss;    $X $C $E $P 505:3000:18 505:3000:18   | cut -f1,2,4 | tee $DIR/$E.ss10.cache
P=gg;    $X $C $E $P 505:3000:18 505:3000:18   | cut -f1,2,4 | tee $DIR/$E.${P}.cache
P=sg;    $X $C $E $P 505:3000:18 505:3000:18   | cut -f1,2,4 | tee $DIR/$E.${P}.cache

echo Cache files generated on `date` | tee $DIR/$README
echo >> $DIR/$README
md5sum *.f $DIR/*.cache >> $DIR/$README

tar jcvf $ARCHIVE $DIR/$README $DIR/*.cache
