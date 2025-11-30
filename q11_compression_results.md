# Q8
(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser benjamine_jean_aicard.txt bja.huff    
[DEBUG] N=484734 first_occ=109 code_bits=3658224 utf8_bytes_written=145 payload_bits=3659384 payload_bps=7.549 file_bytes=457431 header_bytes=8 approx_payload_bytes=457423

- benjamine_jean_aicard.txt;bja.huff;508445;457431;0.89967;3582

(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser de_pontoise_edmond_about.txt dpea.huff
[DEBUG] N=305535 first_occ=112 code_bits=2481608 utf8_bytes_written=151 payload_bits=2482816 payload_bps=8.126 file_bytes=310360 header_bytes=8 approx_payload_bytes=310352

- de_pontoise_edmond_about.txt;dpea.huff;319310;310360;0.97197;2509

# Q9
(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser hard_uniform.txt hard_uniform.huff
[DEBUG] N=100000 first_occ=26 code_bits=712495 utf8_bytes_written=26 payload_bits=712703 payload_bps=7.127 file_bytes=89096 header_bytes=8 approx_payload_bytes=89088

- aha.py hard_uniform.txt;hard_uniform.huff;100000;74011;0.74011;5662
- aha_fgk.py hard_uniform.txt;hard_uniform.huff;100000;89096;0.89096;705


(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser medium_zipf.txt medium_zipf.huff    
[DEBUG] N=100000 first_occ=26 code_bits=658617 utf8_bytes_written=26 payload_bits=658825 payload_bps=6.588 file_bytes=82362 header_bytes=8 approx_payload_bytes=82354

- aha.py medium_zipf.txt;medium_zipf.huff;100000;57250;0.57250;4575
- aha_fgk_oh.py medium_zipf.txt;medium_zipf.huff;100000;82362;0.82362;564

(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser easy_weighted.txt easy_weighted.huff
[DEBUG] N=100000 first_occ=8 code_bits=263290 utf8_bytes_written=8 payload_bits=263354 payload_bps=2.634 file_bytes=32928 header_bytes=8 approx_payload_bytes=32920

- aha.py easy_weighted.txt;easy_weighted.huff;100000;29836;0.29836;1280
- aha_fgk_oh.py easy_weighted.txt;easy_weighted.huff;100000;32928;0.32928;277

# Q10
(.venv) bogy@Bogdans-MacBook-Pro-2 projet_algav % ./compresser ilp.txt ilp.huff                      
[DEBUG] N=33238 first_occ=100 code_bits=219722 utf8_bytes_written=101 payload_bits=220530 payload_bps=6.635 file_bytes=27575 header_bytes=8 approx_payload_bytes=27567

-  ilp.txt;ilp.huff;33240;27575;0.82957;236