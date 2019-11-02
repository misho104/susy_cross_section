#!/bin/sh

SCRAPER=./scraper.py
OUTPUT_DIR="../susy_cross_section/data/lhc_susy_xs_wg"

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

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVx1x1wino"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVx1x1wino_envelope.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVx1x1wino_cteq.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVx1x1wino_mstw.csv

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVslepslep"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVslepslep_pdf4lhc15_ll.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVslepslep_pdf4lhc15_rr.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVslepslep_pdf4lhc15_llrr.csv
cat tmp | python $SCRAPER --index=4 > $OUTPUT_DIR/13TeVslepslep_ct10_ll.csv
cat tmp | python $SCRAPER --index=5 > $OUTPUT_DIR/13TeVslepslep_ct10_rr.csv
cat tmp | python $SCRAPER --index=6 > $OUTPUT_DIR/13TeVslepslep_ct10_maxmix.csv

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn1n2hino"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVn1n2hino_deg_envelope.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVn1n2hino_deg_cteq.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVn1n2hino_deg_mstw.csv

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1hino"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVn2x1hino_deg_envelope_pm.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVn2x1hino_deg_cteq_pm.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVn2x1hino_deg_cteq_p.csv
cat tmp | python $SCRAPER --index=4 > $OUTPUT_DIR/13TeVn2x1hino_deg_cteq_m.csv
cat tmp | python $SCRAPER --index=5 > $OUTPUT_DIR/13TeVn2x1hino_deg_mstw_pm.csv
cat tmp | python $SCRAPER --index=6 > $OUTPUT_DIR/13TeVn2x1hino_deg_mstw_p.csv
cat tmp | python $SCRAPER --index=7 > $OUTPUT_DIR/13TeVn2x1hino_deg_mstw_m.csv

curl -o tmp "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVx1x1hino"
cat tmp | python $SCRAPER --index=1 > $OUTPUT_DIR/13TeVx1x1hino_deg_envelope.csv
cat tmp | python $SCRAPER --index=2 > $OUTPUT_DIR/13TeVx1x1hino_deg_cteq.csv
cat tmp | python $SCRAPER --index=3 > $OUTPUT_DIR/13TeVx1x1hino_deg_mstw.csv

rm tmp
