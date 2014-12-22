from lxml.builder import E
from lxml import etree
import datetime
import os
from ConfigParser import *


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
        self.vatcode = vatcode
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

    def getRelation(self, debitaccount, creditaccount):
        if int(debitaccount) >= 12000:
            return debitaccount
        elif int(creditaccount) >= 12000:
            return creditaccount
        else:
            return ""

    def getDebitRelation(self, debitaccount):
        if int(debitaccount) >= 12000:
            return debitaccount
        else:
            return ""

    def getCreditRelation(self, creditaccount):
        if int(creditaccount) >= 12000:
            return creditaccount
        else:
            return ""

    def getAccountSerialized(self, account):
        if int(account) >= 12000:
            return "1300"
        else:
            return account

    def getDebitAmount(self):
        if self.debitaccount == "1300":
            return self.amount
        else:
            return self.getAmountExVat()

    def getCreditAmount(self):
        if self.creditaccount == "1300":
            return str(float(self.amount) * -1)
        else:
            return str(float(self.getAmountExVat()) * -1)

    def getDebitVatCode(self):
        if not self.debitaccount == "1300":
            return self.vatcode
        else:
            return ""

    def getCreditVatCode(self):
        if not self.creditaccount == "1300":
            return self.vatcode
        else:
            return ""

    def getJournalCode(self):

        # 1300 = Verkauf daher 70
        # 2061 = Geldtransfer daher 90
        # 1003 u 1004 = Kasse daher 10
        # 1010 u 1104 = Bank daher 20
        if int(self.debitaccount) == 1010 or int(self.creditaccount) == 1010:
            return "1010"
        if int(self.debitaccount) == 1104 or int(self.creditaccount) == 1104:
            return "1104"
        elif int(self.debitaccount) == 2061 or int(self.creditaccount) == 2061:
            return "90"
        elif int(self.debitaccount) == 1003 or int(self.creditaccount) == 1003:
            return "1003"
        elif int(self.debitaccount) == 1004 or int(self.creditaccount) == 1004:
            return "1004"
        elif int(self.debitaccount) == 1300 or int(self.creditaccount) == 1300:
            return "70"

    def getTransactionType(self):

        # 20=Sales entry
        # 40=cash flow
        # 90=other
        if int(self.debitaccount) == 1010 or int(self.creditaccount) == 1010:
            return "40"
        if int(self.debitaccount) == 1104 or int(self.creditaccount) == 1104:
            return "40"
        elif int(self.debitaccount) == 2061 or int(self.creditaccount) == 2061:
            return "90"
        elif int(self.debitaccount) == 1003 or int(self.creditaccount) == 1003:
            return "40"
        elif int(self.debitaccount) == 1004 or int(self.creditaccount) == 1004:
            return "40"
        elif int(self.debitaccount) == 1300 or int(self.creditaccount) == 1300:
            return "20"

    def getAmountExVat(self):
        if self.vatcode == "":
            return self.amount
        elif int(self.vatcode) == 1:
            return str(float(self.amount) / 106 * 100)
        elif int(self.vatcode) == 2:
            return str(float(self.amount) / 121 * 100)
        else:
            return self.amount

    def getISODate(self):
        return datetime.date(int(self.date[6:]), int(self.date[3:-5]), int(self.date[:-8])).isoformat()

    def isSameBooking(self, Booking):
        if self.date == Booking.date and self.description == Booking.description and self.getJournalCode() == Booking.getJournalCode():
            return True
        else:
            return False

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

        if code != "" and int(code) >= 12000:
            Accounts.append(Account(code.decode(
                "utf-8", "ignore"), name.decode("utf-8", "ignore"), searchcode.decode("utf-8", "ignore")))
        elif code != "" and int(code) < 12000:
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
    currentbookingid = 100001
    maxBookingsPerFile = 1000

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
    cfgfile = open("./config.ini","w")
    Config = ConfigParser()

    Config.add_section('DIRS')
    Config.set('DIRS','INPUTDIR','./INPUT/')
    Config.set('DIRS','OUTPUTDIR','./OUTPUT/')

    Config.add_section('ACCOUNTS')
    Config.set('ACCOUNTS','CASH','1000,1001,1002,1003')
    Config.set('ACCOUNTS','BANK','1200,1201,1202,1203')
    Config.set('ACCOUNTS','INTERIM','1360')
    Config.set('ACCOUNTS','DEBTORS','12000')
    Config.set('ACCOUNTS','SALESJOURNAL','1300')

    Config.add_section('COUNTERS')
    Config.set('COUNTERS','BOOKINGID','1')


    Config.write(cfgfile)
    cfgfile.close()

INPUTDIR = ConfigSectionMap("DIRS")['inputdir']
OUTPUTDIR = ConfigSectionMap("DIRS")['outputdir']

ensure_dir(INPUTDIR)
ensure_dir(OUTPUTDIR)

makeXMLTransactions()
makeXMLAccounts()

# TODO: Configfile
# TODO: Export für mehrere firmen
# TODO: Geht die Booking ID Alphanumerisch
# TODO: User Interface
# TODO: Booking Counter korrekt setzten
# TODO: Backup von Export Daten mit Timestamp
# TODO: Steuersaetze ausland und andere abweichende steuersaetze
# TODO: Backup von Export Daten mit Timestamp
# TODO: ACCOUNTS TO CREATE SORTIEREN
