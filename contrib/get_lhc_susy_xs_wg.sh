#!/bin/sh

SCRAPER=./scraper.py
OUTPUT_DIR="./lhc_susy_xs_wg"

mkdir -p $OUTPUT_DIR

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1wino"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVn2x1wino_envelope_pm.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVn2x1wino_envelope_p.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVn2x1wino_envelope_m.csv
cat tmp | python $SCRAPER --index=4 > $OUTPUT_DIR/13TeVn2x1wino_cteq_pm.csv
cat tmp | python $SCRAPER --index=5 > $OUTPUT_DIR/13TeVn2x1wino_cteq_p.csv
cat tmp | python $SCRAPER --index=6 > $OUTPUT_DIR/13TeVn2x1wino_cteq_m.csv
cat tmp | python $SCRAPER --index=7 > $OUTPUT_DIR/13TeVn2x1wino_mstw_pm.csv
cat tmp | python $SCRAPER --index=8 > $OUTPUT_DIR/13TeVn2x1wino_mstw_p.csv
cat tmp | python $SCRAPER --index=9 > $OUTPUT_DIR/13TeVn2x1wino_mstw_m.csv

rm tmp
