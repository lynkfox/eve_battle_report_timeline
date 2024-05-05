import json
from time import sleep
from br.parser2 import parse_br2
from br.util import skip_if_cached
from plot_builder.output import build_scatter
import pickle
import os

br_links = [
    "https://br.evetools.org/related/31002464/202403260000",
    "https://br.evetools.org/related/31002426/202403270000",
    "https://br.evetools.org/related/31002021/202403280000",
    "https://br.evetools.org/related/31002374/202403270100",
    "https://br.evetools.org/br/6611f1daddb48200112d75b7",
    "https://br.evetools.org/related/31002375/202403270300",
    "https://br.evetools.org/related/31002271/202403270400",
    "https://br.evetools.org/related/31002456/202403270400",
    "https://br.evetools.org/related/31002099/202403271900",
    "https://br.evetools.org/related/31002467/202403272100",
    "https://br.evetools.org/related/31002501/202403272100",
    "https://br.evetools.org/related/31001746/202403272200",
    "https://br.evetools.org/related/31002054/202403280300",
    "https://br.evetools.org/related/31002065/202403280300",
    "https://br.evetools.org/related/31002092/202403280500",
    "https://br.evetools.org/related/31002378/202403282100",
    "https://br.evetools.org/related/31002469/202403290000",
    "https://br.evetools.org/related/31002438/202403290200",
    "https://br.evetools.org/related/31002155/202403290300",
    "https://br.evetools.org/br/6613fe94ddb48200112d7822",
    "https://br.evetools.org/related/31002370/202403290300",
    "https://br.evetools.org/related/31002484/202403290300",
    "https://br.evetools.org/related/31002124/202403290400",
    "https://br.evetools.org/related/31002453/202403290500",
    "https://br.evetools.org/br/6606f3a1953bc4001246b7de",
    "https://br.evetools.org/related/31002323/202403291700",
    "https://br.evetools.org/related/31002092/202403292300",
    "https://br.evetools.org/related/31002378/202403300000",
    "https://br.evetools.org/related/31002470/202403300100",
    "https://br.evetools.org/related/31002454/202403300300",
    "https://br.evetools.org/related/31002416/202403300300",
    "https://br.evetools.org/related/31001969/202403300400",
    "https://br.evetools.org/related/31001906/202403300400",
    "https://br.evetools.org/related/31002413/202403301800",
    # "https://br.evetools.org/related/31002210/202403302000", #-- Sides on this one are weird, feels like random encounter
    "https://br.evetools.org/related/31002012/202403302200",
    "https://br.evetools.org/br/661fd418953bc4001246d317",
    "https://br.evetools.org/br/661fd44e953bc4001246d318",
    "https://br.evetools.org/related/31002488/202403310000",
    "https://br.evetools.org/br/660a0cfa4541b60012c1babc",
    "https://br.evetools.org/related/31002470/202403310100",
    "https://br.evetools.org/related/31002062/202403310300",
    "https://br.evetools.org/br/66140f75953bc4001246c84b",
    "https://br.evetools.org/related/31002413/202403310400",
    "https://br.evetools.org/related/31002370/202403310500",
    "https://br.evetools.org/br/660a07f4953bc4001246bb85",
    "https://br.evetools.org/related/31002468/202403311600",
    "https://br.evetools.org/related/31002018/202403311700",
    "https://br.evetools.org/related/31002266/202403311800",
    "https://br.evetools.org/related/31000413/202403312100",
    "https://br.evetools.org/related/31002487/202403312100",
    "https://br.evetools.org/related/31002464/202404010000",
    "https://br.evetools.org/related/31002277/202404010200",
    "https://br.evetools.org/br/66141712ddb48200112d7840",
    "https://br.evetools.org/related/31001942/202404010300",
    "https://br.evetools.org/related/31002165/202404010400",
    "https://br.evetools.org/related/31002163/202404010500",
    "https://br.evetools.org/related/31002053/202404010500",
    "https://br.evetools.org/related/31001917/202404011700",
    "https://br.evetools.org/related/31002482/202404012100",
    "https://br.evetools.org/related/31001946/202404020000",
    "https://br.evetools.org/related/31002375/202404020100",
    "https://br.evetools.org/related/31002438/202404020100",
    "https://br.evetools.org/related/31002372/202404020400",
    "https://br.evetools.org/related/31002415/202404020400",
    "https://br.evetools.org/related/31002204/202404020500",
    "https://br.evetools.org/related/31002378/202404021000",
    "https://br.evetools.org/related/31002421/202404021700",
    "https://br.evetools.org/br/6636ebb650adf10012f31a57",
    "https://br.evetools.org/related/31000529/202404030200",
    "https://br.evetools.org/br/660df64cddb48200112d6fbf",
    "https://br.evetools.org/related/31000754/202404030800",
    "https://br.evetools.org/related/31002484/202404031200",
    "https://br.evetools.org/related/31001959/202404031700",
    "https://br.evetools.org/br/661988d5953bc4001246cd16",
    "https://br.evetools.org/br/661988f2953bc4001246cd17",
    "https://br.evetools.org/related/31001964/202404032200",
    "https://br.evetools.org/br/66141ee6ddb48200112d7848",
    "https://br.evetools.org/related/31002374/202404040100",
    "https://br.evetools.org/related/31002375/202404040100",
    "https://br.evetools.org/related/31002418/202404040200",
    "https://br.evetools.org/related/31002084/202404040200",
    "https://br.evetools.org/related/31002165/202404040200",
    "https://br.evetools.org/br/660f3f55953bc4001246c18a",
    "https://br.evetools.org/related/31000413/202404040400",
    "https://br.evetools.org/related/31002465/202404041600",
    "https://br.evetools.org/related/31002438/202404041800",
    "https://br.evetools.org/related/31002374/202404041900",
    "https://br.evetools.org/related/31002374/202404042200",
    "https://br.evetools.org/related/31001957/202404042100",
    "https://br.evetools.org/related/31002300/202404050100",
    "https://br.evetools.org/related/31002411/202404050200",
    "https://br.evetools.org/br/6610a544953bc4001246c335",
    "https://br.evetools.org/related/31002300/202404050500",
    "https://br.evetools.org/related/31002072/202404050400",
    "https://br.evetools.org/related/31002470/202404050500",
    "https://br.evetools.org/related/31002438/202404050600",
    "https://br.evetools.org/related/31002053/202404050600",
    "https://br.evetools.org/related/31001937/202404051700",
    "https://br.evetools.org/related/31002374/202404052000",
    "https://br.evetools.org/related/31002501/202404052200",
    "https://br.evetools.org/br/6611f174ddb48200112d75b6",
    "https://br.evetools.org/br/6611f019ddb48200112d75b3",
    "https://br.evetools.org/br/6611f309ddb48200112d75b8",
    "https://br.evetools.org/br/6611f0b0ddb48200112d75b4",
    "https://br.evetools.org/br/6611f048953bc4001246c598",
    "https://br.evetools.org/br/6611f2df953bc4001246c59c",
    "https://br.evetools.org/br/6611f0fcddb48200112d75b5",
    "https://br.evetools.org/br/6611f2aa953bc4001246c59b",
    "https://br.evetools.org/related/31002383/202404070300",
    "https://br.evetools.org/related/31002434/202404070300",
    "https://br.evetools.org/related/31001703/202404071200",
    "https://br.evetools.org/related/31001482/202404071300",
    "https://br.evetools.org/related/31002374/202404071500",
    "https://br.evetools.org/related/31002379/202404071800",
    "https://br.evetools.org/related/31002418/202404071800",
    "https://br.evetools.org/related/31002466/202404071900",
    "https://br.evetools.org/related/31002428/202404080100",
    "https://br.evetools.org/related/31002100/202404080200",
    "https://br.evetools.org/related/31000743/202404080200",
    "https://br.evetools.org/related/31002424/202404080300",
    "https://br.evetools.org/related/31002456/202404080300",
    "https://br.evetools.org/related/31002274/202404080400",
    "https://br.evetools.org/related/31001964/202404080300",
    "https://br.evetools.org/related/31001447/202404080500",
    "https://br.evetools.org/related/31001728/202404081300",
    "https://br.evetools.org/related/31001817/202404081700",
    "https://br.evetools.org/related/31002076/202404081900",
    "https://br.evetools.org/related/31002457/202404082200",
    "https://br.evetools.org/related/31001703/202404082300",
    "https://br.evetools.org/related/31002452/202404090200",
    "https://br.evetools.org/related/31002403/202404090300",
    "https://br.evetools.org/related/31002012/202404090200",
    "https://br.evetools.org/related/31002463/202404090300",
    "https://br.evetools.org/related/31002386/202404090600",
    "https://br.evetools.org/related/31002457/202404091100",
    "https://br.evetools.org/related/31001964/202404091400",
    "https://br.evetools.org/related/31002374/202404091800",
    "https://br.evetools.org/br/6619871bddb48200112d7d11",
    "https://br.evetools.org/br/6619874bddb48200112d7d12",
    "https://br.evetools.org/br/66198739953bc4001246cd11",
    "https://br.evetools.org/br/66198767ddb48200112d7d13",
    "https://br.evetools.org/related/31002283/202404092200",
    "https://br.evetools.org/related/31002398/202404100000",
    "https://br.evetools.org/related/31002424/202404100000",
    "https://br.evetools.org/related/31002457/202404100000",
    "https://br.evetools.org/related/31002412/202404100100",
    "https://br.evetools.org/related/31001964/202404100100",
    "https://br.evetools.org/related/31002452/202404100300",
    "https://br.evetools.org/related/31002412/202404100400",
    "https://br.evetools.org/related/31002374/202404100400",
    "https://br.evetools.org/related/31002162/202404101300",
    "https://br.evetools.org/related/31002495/202404101900",
    "https://br.evetools.org/related/31002105/202404101900",
    "https://br.evetools.org/related/31002372/202404102100",
    "https://br.evetools.org/br/661876fe953bc4001246cc2c",
    "https://br.evetools.org/related/31002398/202404110100",
    "https://br.evetools.org/related/31002468/202404110200",
    "https://br.evetools.org/related/31002465/202404110200",
    "https://br.evetools.org/related/31002432/202404111200",
    "https://br.evetools.org/related/31002404/202404111200",
    "https://br.evetools.org/related/31001703/202404111300",
    "https://br.evetools.org/related/31002466/202404111500",
    "https://br.evetools.org/related/31002300/202404111800",
    "https://br.evetools.org/related/31002416/202404112000",
    "https://br.evetools.org/related/31001703/202404120100",
    "https://br.evetools.org/related/31002465/202404120100",
    "https://br.evetools.org/related/31002207/202404120200",
    "https://br.evetools.org/related/31002398/202404120300",
    "https://br.evetools.org/related/31002031/202404120500",
    "https://br.evetools.org/related/31002448/202404120900",
    "https://br.evetools.org/related/31002283/202404121300",
    "https://br.evetools.org/related/31002406/202404121500",
    "https://br.evetools.org/related/31002448/202404121500",
    "https://br.evetools.org/related/31002423/202404122100",
    "https://br.evetools.org/related/31002379/202404130000",
    "https://br.evetools.org/br/661b277eddb48200112d7f1b",
    "https://br.evetools.org/related/31000744/202404130100",
    "https://br.evetools.org/related/31002379/202404130500",
    "https://br.evetools.org/related/31002380/202404131300",
    "https://br.evetools.org/related/31002447/202404131700",
    "https://br.evetools.org/related/31001703/202404131800",
    "https://br.evetools.org/related/31002411/202404131900",
    "https://br.evetools.org/related/31002410/202404131900",
    "https://br.evetools.org/related/31001850/202404131900",
    "https://br.evetools.org/related/31001703/202404132000",
    "https://br.evetools.org/related/31002374/202404132000",
    "https://br.evetools.org/related/31002154/202404132100",
    "https://br.evetools.org/related/31002379/202404132200",
    "https://br.evetools.org/related/31002374/202404140000",
    "https://br.evetools.org/related/31002411/202404140000",
    "https://br.evetools.org/related/31002320/202404140100",
    "https://br.evetools.org/related/31002448/202404140100",
    "https://br.evetools.org/related/31001911/202404140200",
    "https://br.evetools.org/br/661c7fd8ddb48200112d80b6",
    "https://br.evetools.org/related/31002108/202404141300",
    "https://br.evetools.org/related/31002453/202404141600",
    "https://br.evetools.org/br/661c1773953bc4001246d02e",
    "https://br.evetools.org/related/31002328/202404141900",
    "https://br.evetools.org/br/661c742e953bc4001246d0c1",
    "https://br.evetools.org/related/31002251/202404142100",
    "https://br.evetools.org/related/31002351/202404150000",
    "https://br.evetools.org/related/31002426/202404150000",
    "https://br.evetools.org/br/661dc7c5ddb48200112d81b4",
    "https://br.evetools.org/related/31002264/202404150300",
    "https://br.evetools.org/related/31002353/202404150300",
    "https://br.evetools.org/related/31002130/202404150400",
    "https://br.evetools.org/related/31001990/202404151400",
    "https://br.evetools.org/related/31002403/202404151400",
    "https://br.evetools.org/related/31002374/202404151800",
    "https://br.evetools.org/related/31002313/202404151800",
    "https://br.evetools.org/related/31002412/202404151800",
    "https://br.evetools.org/related/31002403/202404152000",
    "https://br.evetools.org/related/31001893/202404152300",
    "https://br.evetools.org/related/31001907/202404160200",
    "https://br.evetools.org/related/31002108/202404160300",
    "https://br.evetools.org/related/31002403/202404160500",
    "https://br.evetools.org/related/31002374/202404160400",
    "https://br.evetools.org/related/31000744/202404160400",
    "https://br.evetools.org/related/31002386/202404161000",
    "https://br.evetools.org/related/31001937/202404161500",
    "https://br.evetools.org/related/31002374/202404161600",
    "https://br.evetools.org/related/31001766/202404161700",
    "https://br.evetools.org/br/661f2a2eddb48200112d82c5",
    "https://br.evetools.org/related/31002378/202404170000",
    "https://br.evetools.org/related/31002384/202404170100",
    "https://br.evetools.org/related/31001957/202404170300",
    "https://br.evetools.org/related/31002272/202404170300",
    "https://br.evetools.org/related/31002108/202404170400",
    "https://br.evetools.org/related/31002375/202404170600",
    "https://br.evetools.org/related/31002106/202404171400",
    "https://br.evetools.org/related/31002113/202404171700",
    "https://br.evetools.org/related/31002280/202404172000",
    "https://br.evetools.org/related/31002108/202404172300",
    "https://br.evetools.org/related/31001252/202404180100",
    "https://br.evetools.org/related/31002453/202404180200",
    "https://br.evetools.org/related/31002384/202404180200",
    "https://br.evetools.org/br/66366ee38ee77d0011c15cfb",
    "https://br.evetools.org/related/31002365/202404181100",
    "https://br.evetools.org/related/31002422/202404180300",
    "https://br.evetools.org/related/31002185/202404180800",
    "https://br.evetools.org/related/31002444/202404180900",
    "https://br.evetools.org/related/31002365/202404181100",
    "https://br.evetools.org/related/31001988/202404181600",
    "https://br.evetools.org/related/31001928/202404181900",
    "https://br.evetools.org/related/31002408/202404182100",
    "https://br.evetools.org/related/31001880/202404190000",
    "https://br.evetools.org/related/31000656/202404190200",
    "https://br.evetools.org/related/31002293/202404190300",
    "https://br.evetools.org/related/31002384/202404190300",
    "https://br.evetools.org/related/31002388/202404190300",
    "https://br.evetools.org/related/31002386/202404191000",
    "https://br.evetools.org/related/31002230/202404191400",
    "https://br.evetools.org/related/31002374/202404191700",
    "https://br.evetools.org/related/31002427/202404191900",
    "https://br.evetools.org/related/31001990/202404191900",
    "https://br.evetools.org/related/31001990/202404192200",
    "https://br.evetools.org/related/31002374/202404192200",
    "https://br.evetools.org/related/31002457/202404200000",
    "https://br.evetools.org/related/31002374/202404200000",
    "https://br.evetools.org/related/31002217/202404200200",
    "https://br.evetools.org/related/31002065/202404200200",
    "https://br.evetools.org/related/31002422/202404200300",
    "https://br.evetools.org/related/31000834/202404200300",
    "https://br.evetools.org/related/31001430/202404200500",
    "https://br.evetools.org/related/31002408/202404201100",
    "https://br.evetools.org/related/31001937/202404201200",
    "https://br.evetools.org/related/31002374/202404201200",
    "https://br.evetools.org/related/31001990/202404201200",
    "https://br.evetools.org/related/31002363/202404201700",
    "https://br.evetools.org/related/31002374/202404201700",
    "https://br.evetools.org/related/31002017/202404201900",
    "https://br.evetools.org/br/662458e9ddb48200112d88ab",
    "https://br.evetools.org/related/31002374/202404202100",
    "https://br.evetools.org/related/31002118/202404202100",
    "https://br.evetools.org/related/31002444/202404202200",
    "https://br.evetools.org/related/31002494/202404202200",
    "https://br.evetools.org/related/31002185/202404202300",
    "https://br.evetools.org/related/31002185/202404210100",
    "https://br.evetools.org/related/31002413/202404211000",
    "https://br.evetools.org/related/31002426/202404211600",
    "https://br.evetools.org/related/31001918/202404211700",
    "https://br.evetools.org/related/31002374/202404212100",
    "https://br.evetools.org/related/31002065/202404212300",
    "https://br.evetools.org/related/31002379/202404220000",
    "https://br.evetools.org/related/31001685/202404220100",
    "https://br.evetools.org/related/31002379/202404220200",
    "https://br.evetools.org/related/31001291/202404220100",
    "https://br.evetools.org/related/31000941/202404220100",
    "https://br.evetools.org/related/31002378/202404220200",
    "https://br.evetools.org/related/31002426/202404220300",
    "https://br.evetools.org/related/31002374/202404220500",
    "https://br.evetools.org/related/31002384/202404221400",
    "https://br.evetools.org/br/662702ed5e161e001248d35b",
    "https://br.evetools.org/related/31002374/202404222100",
    "https://br.evetools.org/br/6627003c0262b5001221cd65",
    "https://br.evetools.org/related/31001850/202404222200",
    "https://br.evetools.org/related/31002375/202404222300",
    "https://br.evetools.org/related/31002374/202404230300",
    "https://br.evetools.org/related/31002382/202404230200",
    "https://br.evetools.org/related/31002449/202404230300",
    "https://br.evetools.org/related/31002437/202404231000",
    "https://br.evetools.org/related/31002037/202404231200",
    "https://br.evetools.org/related/31001019/202404231800",
    "https://br.evetools.org/related/31000740/202404240300",
    "https://br.evetools.org/related/31002403/202404240700",
    "https://br.evetools.org/related/31000707/202404241600",
    "https://br.evetools.org/related/31002448/202404242000",
    "https://br.evetools.org/related/31002127/202404242200",
    "https://br.evetools.org/related/31002463/202404242300",
    "https://br.evetools.org/related/31002382/202404250400",
    "https://br.evetools.org/related/31002376/202404250900",
    "https://br.evetools.org/related/31002413/202404251000",
    "https://br.evetools.org/related/31002107/202404260000",
    "https://br.evetools.org/related/31001120/202404260300",
    "https://br.evetools.org/br/662c474a3c2f0300123520f8",
    "https://br.evetools.org/related/31002391/202404261000",
    "https://br.evetools.org/br/662c44ed3c2f0300123520f5",
    "https://br.evetools.org/related/31002290/202404262000",
    "https://br.evetools.org/related/31002374/202404262300",
    "https://br.evetools.org/related/31000413/202404270000",
    "https://br.evetools.org/related/31002100/202404270000",
    "https://br.evetools.org/related/31002078/202404270000",
    "https://br.evetools.org/related/31002079/202404270400",
    "https://br.evetools.org/related/31002103/202404270500",
    "https://br.evetools.org/related/31002413/202404271000",
    "https://br.evetools.org/related/31001740/202404271500",
    "https://br.evetools.org/related/31002466/202404271900",
    "https://br.evetools.org/related/31002437/202404272100",
    "https://br.evetools.org/related/31000324/202404280000",
    "https://br.evetools.org/related/31002466/202404280100",
    "https://br.evetools.org/related/31002374/202404280100",
    "https://br.evetools.org/related/31002438/202404280100",
    "https://br.evetools.org/related/31002107/202404280400",
    "https://br.evetools.org/br/662ee871bea462001299ccab",
    "https://br.evetools.org/related/31002107/202404281100",
    "https://br.evetools.org/related/31002437/202404281500",
    "https://br.evetools.org/related/31001953/202404281900",
    "https://br.evetools.org/related/31002466/202404281900",
    "https://br.evetools.org/related/31002078/202404282200",
    "https://br.evetools.org/related/31002342/202404290300",
    "https://br.evetools.org/related/31002241/202404290300",
    "https://br.evetools.org/related/31002466/202404290300",
    "https://br.evetools.org/related/31002391/202404290300",
    "https://br.evetools.org/related/31002386/202404290900",
    "https://br.evetools.org/br/663031613c2f0300123524d5",
    "https://br.evetools.org/related/31000707/202404291500",
    "https://br.evetools.org/related/31001896/202404291900",
    "https://br.evetools.org/related/31001461/202404292000",
    "https://br.evetools.org/related/31001672/202404300200",
    "https://br.evetools.org/related/31000413/202404300000",
    "https://br.evetools.org/related/31002448/202404301000",
    "https://br.evetools.org/related/31002073/202404300100",
    "https://br.evetools.org/related/31002128/202404300200",
    "https://br.evetools.org/related/31002391/202404300500",
    "https://br.evetools.org/related/31002396/202404300500",
    "https://br.evetools.org/related/31002440/202404300100",
    "https://br.evetools.org/related/31002078/202404300000",
    "https://br.evetools.org/br/6632e2162da6080012646b93",
    "https://br.evetools.org/related/31002065/202405010300",
    "https://br.evetools.org/related/31002459/202405010400",
    "https://br.evetools.org/br/6632e08a2da6080012646b90",
    "https://br.evetools.org/related/31002402/202405010500",
    "https://br.evetools.org/related/31002073/202405010500",
    "https://br.evetools.org/br/6632e54b132a2a0012c77de7",
    "https://br.evetools.org/related/31002413/202405010600",
    "https://br.evetools.org/related/31002443/202405011000",
    "https://br.evetools.org/related/31002123/202405011600",
    "https://br.evetools.org/related/31001406/202405011900",
    "https://br.evetools.org/related/31001672/202405012000",
    "https://br.evetools.org/related/31002247/202405012100",
    "https://br.evetools.org/br/6632e31a132a2a0012c77de2",
    "https://br.evetools.org/related/31001712/202405020000",
    "https://br.evetools.org/related/31002429/202405020100",
    "https://br.evetools.org/related/31002078/202405020300",
    "https://br.evetools.org/related/31002396/202405020300",
    "https://br.evetools.org/br/6634306a132a2a0012c77f09",
    "https://br.evetools.org/br/663430a4132a2a0012c77f0b",
    "https://br.evetools.org/related/31002241/202405020600",
    "https://br.evetools.org/related/31002427/202405020600",
    "https://br.evetools.org/br/663430802da6080012646cb4",
    "https://br.evetools.org/related/31002454/202405021300",
    "https://br.evetools.org/br/663432422da6080012646cc7",
    "https://br.evetools.org/related/31002123/202405021700",
    "https://br.evetools.org/related/31002153/202405021900",
    "https://br.evetools.org/related/31001970/202405021900",
    "https://br.evetools.org/related/31001778/202405022100",
    "https://br.evetools.org/related/31002132/202405022200",
    "https://br.evetools.org/related/31002205/202405022200",
    "https://br.evetools.org/related/31001778/202405030000",
    "https://br.evetools.org/related/31002031/202405030000",
    "https://br.evetools.org/br/66357eccd50e950012f69d4c",
    "https://br.evetools.org/br/66357996d50e950012f69d42",
    "https://br.evetools.org/related/31002412/202405030300",
    "https://br.evetools.org/related/31002429/202405030400",
    "https://br.evetools.org/related/31002420/202405030400",
    "https://br.evetools.org/related/31001018/202405030500",
    "https://br.evetools.org/br/66357f44c0d9e00011aad7e9",
    "https://br.evetools.org/related/31002162/202405031700",
    "https://br.evetools.org/related/31002412/202405031900",
    "https://br.evetools.org/related/31002163/202405032000",
    "https://br.evetools.org/related/31002171/202405040100",
    "https://br.evetools.org/related/31002092/202405040400",
    "https://br.evetools.org/related/31002425/202405040300",
    "https://br.evetools.org/related/31002405/202405040300",
    "https://br.evetools.org/related/31001014/202405040400",
    "https://br.evetools.org/related/31002272/202405041800",
    "https://br.evetools.org/related/31002153/202405041900",
]

new = []


def parse_battles2(br_links):
    PROCESS_LIST = br_links  # new

    first = True
    battle_data = None
    for idx, br in enumerate(PROCESS_LIST):
        if first:
            battle_data = parse_br2(br, battle_data)
            first = False
        else:
            if not skip_if_cached(br):
                sleep(3)
            print(f"Retrieving and parsing {br}...")
            parse_br2(br, battle_data)
            print(f"...Done (Completed {idx} of {len(PROCESS_LIST)-1}) \n")

    return battle_data


if __name__ == "__main__":
    # parse_br("https://br.evetools.org/related/31002275/202404160300")

    pickled_data_file = "output/war_to_date.pickle"
    print("Checking cached computed data")
    existing_battles = None
    # if os.path.exists(pickled_data_file):
    #     try:
    #         with open(pickled_data_file, "rb") as f:
    #             existing_battles = pickle.load(f)
    #     except:
    #         print("can't load existing pickle, ignoring")

    if existing_battles is None or len(existing_battles.battles) > len(br_links):
        battles = parse_battles2(br_links)
        print("Saving data...\n")

        with open("output/structure_owners.json", "w") as f:
            json.dump(battles.get_station_owners(), f, indent=4)

        # with open(pickled_data_file, "wb") as f:
        #     pickle.dump(battles, f)
        # with open("output/war_to_date.json", "w") as f:
        #     json.dump(battles.convert(), f, indent=4)
    else:
        print("No new BR links found, loading cache")
        battles = existing_battles

    # print("Generating calculations...\n")
    # alliances, systems, holding_corps, probable_friends, ships, probably_just_trash = calculate_lists(battles)

    # content = {
    #     "probably_just_trash": probably_just_trash,
    #     "trash_list": [k for k in probably_just_trash.keys()],
    #     "probable_friends": probable_friends,
    #     "known_alliances": alliances,
    #     "known_systems": systems,
    #     "known_holding_corps": holding_corps,
    #     "known_ships": ships,
    # }
    # with open("output/war_lists.json", "w") as f:
    #     json.dump(content, f, indent=4)

    print("creating timeline plot")

    fig = build_scatter(battles)
