## Data Analysis on quality control (QC) test results (from the Inner Tracker production database) of the ATLAS Inner Tracker Strip Detector Powerboard. 

**This script takes a single test variable, such as DC/DC Output Voltage, and creates a histogram of that variable across all production Powerboards registered in the ITk database. The horizontal axis range will be based on variable-specific thresholds, which determine whether or not a measured value is acceptable for a production Powerboard. Additionally, the histogram will display the median and standard deviation of the distribution, and a count of how many measured values fell outside of the threshold.**

**In order to use, you must have access to the database through two access codes. The script will prompt you to enter these.**

**This code is meant to produce plots for the following test variables:** 
- Pad ID
- BER
- linPOLV
- DC/DC Output Voltage
- HV In Current
- HV Out Current
- HVret
- OFout
- CALx
- CALy
- Shuntx
- Shunty
- LDx0EN
- LDx1EN
- LDx2EN
- LDy0EN
- LDy1EN
- LDy2EN
- NTCx
- NTCy
- NTCpb
- CTAT
- PTAT
- -13% DC/DC Adjust
- -6% DC/DC Adjust
- +6% DC/DC Adjust
- DC/DC Efficiency
