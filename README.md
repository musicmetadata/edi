# Music Metadata - EDI

[![Build Status](https://travis-ci.com/musicmetadata/edi.svg?branch=master)](https://travis-ci.com/musicmetadata/edi)
[![Coverage Status](https://coveralls.io/repos/github/musicmetadata/edi/badge.svg?branch=master)](https://coveralls.io/github/musicmetadata/edi?branch=master)
![GitHub](https://img.shields.io/github/license/musicmetadata/edi)
![PyPI](https://img.shields.io/pypi/v/music-metadata-edi)

Music Metadata - EDI is a base library for several EDI-based formats by CISAC, most 
notably Common Works Registration (CWR) and Common Royalty Distribution (CRD).

This library features common (abstract) functionality. Libraries for concrete
formats are under development.

Here is an example of a CWR 2.1 file (all values are randomly generated):

    HDRPB000000199MUSIC PUB CARTOONS                           01.102019032810341420190328               
    GRHNWR0000102.100000000000  
    NWR0000000000000000EMILIA AND ANNIE                                              EM0002        T100600002600000000            UNC000715Y      ORI                                                   N00000000000                                                    
    SPU000000000000000101096200297SMITH REDDY PUBLISHING                        E 00000000009620029710              10102500   05000   05000 N                                             
    SPT0000000000000002096200297      025000500005000I2136N001
    SPU000000000000000302092900117LUNA LEWIS PUBLISHING                         E 00000000009290011721              02102500   05000   05000 N                                             
    SPT0000000000000004092900117      025000500005000I2136N001
    SWR0000000000000005096800355CAMACHO                                      SHERRY                         CA0000000000968003558110102500   00000   00000 N                            
    SWT0000000000000006096800355025000000000000I2136N001
    PWR0000000000000007096200297SMITH REDDY PUBLISHING                                                   096800355
    SWR0000000000000008091700626SCOTT                                        ELIZABETH                      CA0000000000917006262202102500   00000   00000 N                            
    SWT0000000000000009091700626025000000000000I2136N001
    PWR0000000000000010092900117LUNA LEWIS PUBLISHING                                                    091700626
    ALT0000000000000011WHEN EMILIA AND ANNIE                                       AT  
    PER0000000000000012PRATT                                        SHARI                         00000000000             
    PER0000000000000013FAGG                                         DANIEL                        00000000000             
    REC000000000000001400000000                                                            000715                                                                                                                                               0000000000000JMK401175550     
    GRT000010000000100000017   0000000000
    TRL000010000000100000019

