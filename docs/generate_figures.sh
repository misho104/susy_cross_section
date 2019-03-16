#!/usr/local/bin/zsh

OUTPUT=_static/images

function gen_pdf_1(){ # create tmp.pdf
    echo $@
    DIR=`PWD`
    echo python -m validation $@ -o $DIR/tmp.pdf
    (cd .. && python -m validation $@ -o $DIR/tmp.pdf)
    if [ ! -f tmp.pdf ]; then
        echo "Not generated."
        exit 1
    fi
}

function gen_pdf_2(){ # convert tmp.pdf to named file
    pdfcrop tmp.pdf tmp2.pdf
    yes | gs -dBATCH -sOutputFile=$OUTPUT/$1.pdf -dFirstPage=$2 -dLastPage=$2 -sDEVICE=pdfwrite tmp2.pdf
    convert -density 192 $OUTPUT/$1.pdf $OUTPUT/$1.png
}

function gen_pdf(){ # title, page, args
    gen_pdf_1 ${@:3}
    gen_pdf_2 $1 $2
    rm tmp.pdf tmp2.pdf
}

mkdir -p $OUTPUT

gen_pdf sdcpl-compare-1 1 compare 13TeV.sb10.decoup
gen_pdf slep-compare-1  1 compare 13TeV.slepslep.rr

gen_pdf_1 compare 13TeV.gg
pdfseparate tmp.pdf tmp-%d.pdf
pdfjam tmp-1.pdf tmp-2.pdf --nup 2x1 --landscape --outfile tmp.pdf
gen_pdf_2 gg-compare 1
rm tmp*.pdf
