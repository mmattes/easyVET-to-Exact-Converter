from lxml.builder import E
from lxml import etree
import datetime
import time
import os
from ConfigParser import *
import shutil


#
# CLASS Accounts
# Aufbau wie es Exact benoetigt
##########################################################################
class Account(object):

    def __init__(self, code, name, searchcode):
        self.code = code
        self.name = name
        self.searchcode = searchcode


#
# CLASS GLTransactions
# Aufbau wie es Exact benoetigt
##########################################################################
class GLTransaction(object):

    def __init__(self, booking, journal, date):
        self.booking = booking
        self.journal = journal
        self.date = date
        self.GLTransactionLines = []

#
# CLASS GLTransactionLine
# Aufbau wie es Exact benoetigt
##########################################################################


class GLTransactionLine(object):

    def __init__(self, glaccount, description, relation, ammount, vatcode, transactiontype):
        self.glaccount = glaccount
        self.description = description
        self.relation = relation
        self.ammount = ammount
        self.vatcode = vatcode
        self.transactiontype = transactiontype


#
# CLASS Booking
# Notwendig um zeile fuer Zeile aus den Buchungen die easyVET Exportiert
# einzulesen und dann zu verarbeiten
##########################################################################
class Booking(object):

    def __init__(self, amount, currency, vatcode, creditaccount, description, date, debitaccount, remark):
        self.amount = amount.replace(".", "").replace(",", ".")
        self.vatcode = self.getVATCode(vatcode)
        self.currency = currency
        self.creditaccount = self.getAccountSerialized(creditaccount)
        self.description = description
        self.date = date
        self.debitaccount = self.getAccountSerialized(debitaccount)
        self.remark = remark
        self.debitamount = self.getDebitAmount()
        self.creditamount = self.getCreditAmount()
        self.debitvatcode = self.getDebitVatCode()
        self.creditvatcode = self.getCreditVatCode()
        self.debitRelation = self.getDebitRelation(debitaccount)
        self.creditRelation = self.getCreditRelation(creditaccount)
        self.relation = self.getRelation(debitaccount, creditaccount)
        self.transactiontype = self.getTransactionType()

    def getVATCode(self, vatcode):
        if vatcode == "":
            return VAT_ZERO[0]
        elif vatcode == "1":
            return VAT_LOW[0]
        elif vatcode == "2":
            return VAT_HIGH[0]
        elif vatcode == "101":
            return VAT_INEU[0]
        elif vatcode == "102":
            return VAT_INEU[0]
        elif vatcode == "201":
            return VAT_OUTEU[0]
        elif vatcode == "202":
            return VAT_OUTEU[0]
        else:
            print "ERROR: UNKOWN VATCODE"
            return ""

    def getRelation(self, debitaccount, creditaccount):
        if int(debitaccount) >= DEBTORS_ACCOUNTS:
            return debitaccount
        elif int(creditaccount) >= DEBTORS_ACCOUNTS:
            return creditaccount
        else:
            return ""

    def getDebitRelation(self, debitaccount):
        if int(debitaccount) >= DEBTORS_ACCOUNTS:
            return debitaccount
        else:
            return ""

    def getCreditRelation(self, creditaccount):
        if int(creditaccount) >= DEBTORS_ACCOUNTS:
            return creditaccount
        else:
            return ""

    def getAccountSerialized(self, account):
        if int(account) >= DEBTORS_ACCOUNTS:
            return SALESJOURNAL
        else:
            return account

    def getDebitAmount(self):
        if self.debitaccount == SALESJOURNAL:
            return self.amount
        else:
            return self.getAmountExVat()

    def getCreditAmount(self):
        if self.creditaccount == SALESJOURNAL:
            return str(float(self.amount) * -1)
        else:
            return str(float(self.getAmountExVat()) * -1)

    def getDebitVatCode(self):
        if not self.debitaccount == SALESJOURNAL:
            return self.vatcode
        else:
            return VAT_ZERO[0]

    def getCreditVatCode(self):
        if not self.creditaccount == SALESJOURNAL:
            return self.vatcode
        else:
            return VAT_ZERO[0]

    def getJournalCode(self):
        for account in ACCOUNTS:
            if self.debitaccount == account or self.creditaccount == account:
                return account
                break

        if self.debitaccount == INTERIM_ACCOUNT or self.creditaccount == INTERIM_ACCOUNT:
            return "90"
        elif self.debitaccount == SALESJOURNAL or self.creditaccount == SALESJOURNAL:
            return "70"

    def getTransactionType(self):

        # 20=Sales entry
        # 40=cash flow
        # 90=other
        for account in ACCOUNTS:
            if self.debitaccount == account or self.creditaccount == account:
                return "40"
                break

        if self.debitaccount == INTERIM_ACCOUNT or self.creditaccount == INTERIM_ACCOUNT:
            return "90"
        elif self.debitaccount == SALESJOURNAL or self.creditaccount == SALESJOURNAL:
            return "20"

    def getAmountExVat(self):
        for VATCODE in ALL_VAT_CODES:
            if self.vatcode == VATCODE[0]:
                return str(float(self.amount) / (100 + int(VATCODE[1])) * 100)
                break

#        if self.vatcode == "":
#            return self.amount
#        elif int(self.vatcode) == 1:
#            return str(float(self.amount) / 106 * 100)
#        elif int(self.vatcode) == 2:
#            return str(float(self.amount) / 121 * 100)
#        else:
#            return self.amount

    def getISODate(self):
        return datetime.date(int(self.date[6:]), int(self.date[3:-5]), int(self.date[:-8])).isoformat()


#
# Generiert aus den buchungen die eigentlichen Exact Konformen
# Transaktionen und verarbeitet diese dann
##########################################################################


def genGLTransactions(Bookings, startID):

    GLTransactions = []
    a = ""

    for booking in Bookings:
        a = GLTransaction(
            str(startID), booking.getJournalCode(), booking.getISODate())
        a.GLTransactionLines.append(GLTransactionLine(booking.debitaccount, booking.description +
                                                      " " + booking.remark, booking.relation, booking.debitamount, booking.debitvatcode, booking.transactiontype))
        a.GLTransactionLines.append(GLTransactionLine(booking.creditaccount, booking.description +
                                                      " " + booking.remark, booking.relation, booking.creditamount, booking.creditvatcode, booking.transactiontype))

        GLTransactions.append(a)
        a = ""
        startID += 1

    result = []
    for a in GLTransactions:
        result.append(E.GLTransaction(E.Journal("", code=a.journal), E.Date(
            a.date), *appendGLTransactionLines(a), entry=a.booking))
    return result

#
# Unterfunktion zu genGLTransactions() da diese Funktion die eigentlichen
# Buchungszeilen ins Exact konforme XML Format bringt
##########################################################################


def appendGLTransactionLines(GLTransaction):
    a = GLTransaction

    result = []
    for line in a.GLTransactionLines:
        result.append(E.GLTransactionLine(E.Date(a.date), E.GLAccount("", code=line.glaccount), E.Description(line.description.decode('utf-8', 'ignore')), E.Account(
            "", code=line.relation), E.Amount(E.Currency("", code="EUR"), E.Value(line.ammount), E.VAT("", code=line.vatcode)), type=line.transactiontype, line="1"))
    return result


def genAccounts():
    fobj = open(INPUTDIR + "DebitorF1.txt", "r")

    acctocreate = open(OUTPUTDIR + "AccountsToCreate.txt", "w")
    Accounts = []

    fobj.readline()
    for line in fobj:
        data = line.split("\t")
        if len(data) == 2:
            code = data[0]
            name = data[1]
            name = name[:-2]
        else:
            code = ""
            name = ""

        client = name.split()

        searchcode = ""
        if len(client) == 3:
            searchcode = client[0] + " " + client[1]
        elif len(client) == 2:
            searchcode = client[0]
        else:
            searchcode = ""

        if code != "" and int(code) >= DEBTORS_ACCOUNTS:
            Accounts.append(Account(code.decode(
                "utf-8", "ignore"), name.decode("utf-8", "ignore"), searchcode.decode("utf-8", "ignore")))
        elif code != "" and int(code) < DEBTORS_ACCOUNTS:
            acctocreate.write(line)

    fobj.close()
    acctocreate.close

    result = []
    for a in Accounts:
        # print a.name
        result.append(
            E.Account(E.Name(a.name), code=a.code, searchcode=a.searchcode, status="C"))
    return result


def makeXMLTransactions():
    currentbookingid = BOOKINGID

    fobj = open(INPUTDIR + "BuchungF1.txt", "r")
    fobj.readline()

    Bookings = []

    for line in fobj:
        data = line.split("\t")
        Bookings.append(
            Booking(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]))

    files = len(Bookings) / maxBookingsPerFile

    for x in range(0, files + 1):
        print x * maxBookingsPerFile

        xml = E.GLTransactions(
            *genGLTransactions(Bookings[x * maxBookingsPerFile:(x + 1) * maxBookingsPerFile], currentbookingid))
        fobj = open(OUTPUTDIR + "GLTransactions" + str(x) + ".xml", "w")        
        fobj.write("<eExact>\n")
        fobj.write(etree.tostring(xml, pretty_print=True))
        fobj.write("</eExact>")
        fobj.close()
        currentbookingid += maxBookingsPerFile


def makeXMLAccounts():
    xml = E.Accounts(*genAccounts())

    fobj = open(OUTPUTDIR + "Relaties.xml", "w")
    fobj.write("<eExact>")
    fobj.write(etree.tostring(xml, pretty_print=True))
    fobj.write("</eExact>")
    fobj.close()


def ensure_dir(folder):
    dir = os.path.dirname(folder)
    if not os.path.exists(dir):
        os.makedirs(dir)


def ConfigSectionMap(section):
    Config = ConfigParser()
    Config.read(CONFIGFILE)
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


#
# MAIN SECTION
# Zuerst die Konfiguration dann der aufruf der einzelnen Programme
##########################################################################

CONFIGFILE = "./config.ini"

if not os.path.exists(CONFIGFILE):
    cfgfile = open("./config.ini", "w")
    Config = ConfigParser()

    Config.add_section('GENERAL')
    Config.set('GENERAL', 'SPLIT_BOOKINGS_INTO', '1000')

    Config.add_section('DIRS')
    Config.set('DIRS', 'INPUTDIR', './INPUT/')
    Config.set('DIRS', 'OUTPUTDIR', './OUTPUT/')
    Config.set('DIRS', 'OUTPUTDIR_BACKUP', './OUTPUT_BACKUP/')

    Config.add_section('ACCOUNTS')
    Config.set('ACCOUNTS', 'CASH', '1000,1001,1002,1003')
    Config.set('ACCOUNTS', 'BANK', '1200,1201,1202,1203')
    Config.set('ACCOUNTS', 'INTERIM', '1360')
    Config.set('ACCOUNTS', 'DEBTORS', '12000')
    Config.set('ACCOUNTS', 'SALESJOURNAL', '1300')

    Config.add_section('VATIDS')
    Config.set('VATIDS', 'VAT_LOW', '1,6')
    Config.set('VATIDS', 'VAT_HIGH', '2,21')
    Config.set('VATIDS', 'VAT_ZERO', '0,0')
    Config.set('VATIDS', 'VAT_INEU', '7,0')
    Config.set('VATIDS', 'VAT_OUTEU', '6,0')

    Config.add_section('COUNTERS')
    Config.set('COUNTERS', 'BOOKINGID', '1')

    Config.write(cfgfile)
    cfgfile.close()

maxBookingsPerFile = int(ConfigSectionMap("GENERAL")['split_bookings_into'])

INPUTDIR = ConfigSectionMap("DIRS")['inputdir']
OUTPUTDIR = ConfigSectionMap("DIRS")['outputdir']
OUTPUTDIR_BACKUP = ConfigSectionMap("DIRS")['outputdir_backup']

CASH_ACCOUNTS = ConfigSectionMap("ACCOUNTS")['cash'].split(',')
BANK_ACCOUNTS = ConfigSectionMap("ACCOUNTS")['bank'].split(',')
INTERIM_ACCOUNT = ConfigSectionMap("ACCOUNTS")['interim']
DEBTORS_ACCOUNTS = int(ConfigSectionMap("ACCOUNTS")['debtors'])
SALESJOURNAL = ConfigSectionMap("ACCOUNTS")['salesjournal']

ACCOUNTS = CASH_ACCOUNTS + BANK_ACCOUNTS

VAT_LOW = ConfigSectionMap("VATIDS")['vat_low'].split(',')
VAT_HIGH = ConfigSectionMap("VATIDS")['vat_high'].split(',')
VAT_ZERO = ConfigSectionMap("VATIDS")['vat_zero'].split(',')
VAT_INEU = ConfigSectionMap("VATIDS")['vat_ineu'].split(',')
VAT_OUTEU = ConfigSectionMap("VATIDS")['vat_outeu'].split(',')

ALL_VAT_CODES = (VAT_LOW, VAT_HIGH, VAT_ZERO, VAT_INEU, VAT_OUTEU)


BOOKINGID = int(ConfigSectionMap("COUNTERS")['bookingid'])

# Zuerst alle alten Daten im OUTPUT Verzeichniss loeschen
filelist = [ f for f in os.listdir(OUTPUTDIR)]
for f in filelist:
    os.remove(OUTPUTDIR+f)

timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")

ensure_dir(INPUTDIR)
ensure_dir(OUTPUTDIR)
ensure_dir(OUTPUTDIR_BACKUP)

makeXMLTransactions()
makeXMLAccounts()

filelist = [ f for f in os.listdir(OUTPUTDIR)]
for f in filelist:
    shutil.copy(OUTPUTDIR+f,OUTPUTDIR_BACKUP+timestamp+"_"+f[:-4]+".xml")

# TODO: Export fuer mehrere firmen
# TODO: Geht die Booking ID Alphanumerisch
# TODO: User Interface
# TODO: Booking Counter korrekt setzten
# TODO: ACCOUNTS TO CREATE SORTIEREN