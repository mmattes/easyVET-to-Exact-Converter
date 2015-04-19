import configobj

default_cfg = """
[GENERAL]
split_bookings_into = 1000

[DIRS]
inputdir = ./INPUT/
outputdir = ./OUTPUT/

[ACCOUNTS]
cash = 1000,1001,1002,1003
bank = 1200,1201,1202,1203
interim = 1360
interimjounal_code = 90
debtors = 12000
salesjournald = 1300
salesjournal_code = 70

[VATIDS]
vat_low = 1,6
vat_high = 2,21
vat_zero = 0,0
vat_ineu = 7,0
vat_outeu = 6,0

[COUNTERS]
bookingid = 1
"""


def createConfig(path):
    cfg_file = open(path,"w")
    cfg_file.write(default_cfg)
    cfg_file.close()

def readConfig(path):
    return configobj.ConfigObj(path)

if __name__ == '__main__':
    createConfig("config.ini")
