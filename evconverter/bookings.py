# !/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time
import os
import sys
import shutil
import pkg_resources  # part of setuptools

from lxml.builder import E
from lxml import etree

version = pkg_resources.require("evconverter")[0].version


class Account(object):
    """ Class to hold the Account objects like Exact needs it, this is a minimum setup"""
    def __init__(self, code, name, searchcode):
        self.code = code
        self.name = name
        self.searchcode = searchcode

    def __getitem__(self, index):
        return self.code[index]

    def __setitem__(self, index, value):
        self.code[index] = value

    def __str__(self):
        return "{0}, {1}".format(self.code, self.name)


class GLTransaction(object):
    """ Class to hold the GLTransaction objects like Exact needs it, this is a minimum setup"""
    def __init__(self, booking, journal, date):
        self.booking = booking
        self.journal = journal
        self.date = date
        self.GLTransactionLines = []


class GLTransactionLine(object):
    """ Class to hold the GLTransactionLine objects, a sub of GLTransactions like Exact needs it,
    this is a minimum setup"""
    def __init__(self, glaccount, description, relation, amount, vatcode, transactiontype):
        self.glaccount = glaccount
        self.description = description
        self.relation = relation
        self.amount = amount
        self.vatcode = vatcode
        self.transactiontype = transactiontype


class Booking(object):
    """ Class Booking, helper class to read the Booking lines from the export of easyVET
    """
    def __init__(self, amount, currency, vatcode, creditaccount, description, date, debitaccount,
                 remark):
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
            return ""
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
            print "ERROR: UNKOWN VATCODE \" {0} \" IN FILES TO CONVERT".format(vatcode)
            sys.exit(1)

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
            return ""

    def getCreditVatCode(self):
        if not self.creditaccount == SALESJOURNAL:
            return self.vatcode
        else:
            return ""

    def getJournalCode(self):
        for account in ACCOUNTS:
            if self.debitaccount == account or self.creditaccount == account:
                return account
                break

        if self.debitaccount == INTERIM_ACCOUNT or self.creditaccount == INTERIM_ACCOUNT:
            return INTERIMJOURNAL_CODE
        elif self.debitaccount == SALESJOURNAL or self.creditaccount == SALESJOURNAL:
            return SALESJOURNAL_CODE

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
        if not self.vatcode == "":
            for VATCODE in ALL_VAT_CODES:
                if self.vatcode == VATCODE[0]:
                    return str(round(float(self.amount) / (100 + int(VATCODE[1])) * 100, 2))
                    break
        else:
            return self.amount

    def getISODate(self):
        return datetime.date(int(self.date[6:]), int(self.date[3:-5]),
                             int(self.date[:-8])).isoformat()


def genGLTransactions(Bookings, startID):
    """
    Generates out of the Bookings created from the TXT file the propper Exact Bookings in XML
    Format
    """
    GLTransactions = []
    a = ""

    for booking in Bookings:
        a = GLTransaction(
            str(startID), booking.getJournalCode(), booking.getISODate())
        a.GLTransactionLines.append(GLTransactionLine(booking.debitaccount, booking.description +
                                    " " + booking.remark, booking.relation, booking.debitamount,
                                    booking.debitvatcode, booking.transactiontype))

        a.GLTransactionLines.append(GLTransactionLine(booking.creditaccount, booking.description +
                                    " " + booking.remark, booking.relation, booking.creditamount,
                                    booking.creditvatcode, booking.transactiontype))

        GLTransactions.append(a)
        a = ""
        startID += 1

    result = []
    for a in GLTransactions:
        result.append(E.GLTransaction(E.Journal("", code=a.journal), E.Date(
            a.date), *appendGLTransactionLines(a), entry=a.booking))
    return result


def appendGLTransactionLines(GLTransaction):
    """
    Subfunction to genGLTransactions(), creates the booking lines of the Exact Format
    """
    a = GLTransaction

    result = []
    for line in a.GLTransactionLines:
        if line.relation == "":
            result.append(E.GLTransactionLine(E.Date(a.date),
                          E.GLAccount("", code=line.glaccount),
                          E.Description(line.description.decode('utf-8', 'ignore')),
                          E.Amount(E.Currency("", code="EUR"),
                          E.Value(line.amount),
                          E.VAT("", code=line.vatcode)), type=line.transactiontype, line="1"))
        else:
            result.append(E.GLTransactionLine(E.Date(a.date),
                          E.GLAccount("", code=line.glaccount),
                          E.Description(line.description.decode('utf-8', 'ignore')),
                          E.Account("", code=line.relation),
                          E.Amount(E.Currency("", code="EUR"),
                          E.Value(line.amount),
                          E.VAT("", code=line.vatcode)), type=line.transactiontype, line="1"))
    return result


def genAccounts(file, output, config):
    try:
        fobj = open(file, "r")
    except Exception, e:
        print e
        sys.exit(1)

    acctocreate = open(output + "AccountsToCreate.txt", "w")
    Accounts = []
    AccountsToCreate = []

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

        if code != "" and int(code) >= config["ACCOUNTS"]["debtors"]:
            Accounts.append(Account(code.decode("utf-8", "ignore"), name.decode("utf-8", "ignore"),
                                    searchcode.decode("utf-8", "ignore")))
        elif code != "" and int(code) < config["ACCOUNTS"]["debtors"]:
            AccountsToCreate.append(Account(code.decode("utf-8", "ignore"),
                                    name.decode("utf-8", "ignore"),
                                    searchcode.decode("utf-8", "ignore")))

    fobj.close()

    for account in sorted(AccountsToCreate, key=lambda account: account[0]):
        acctocreate.write(str("{0}\r\n".format(account)))

    acctocreate.close()

    result = []
    for a in Accounts:
        result.append(E.Account(E.Name(a.name), E.IsSupplier("False"),
                      code=a.code, searchcode=a.searchcode, status="C"))
    return result


def makeXMLTransactions(file, output, config):
    currentBookingID = config["COUNTERS"]["bookingid"]
    maxBookingsPerFile = config["GENERAL"]["split_bookings_into"]

    try:
        fobj = open(file, "r")
    except Exception, e:
        print e
        sys.exit(1)

    fobj.readline()

    Bookings = []

    for line in fobj:
        data = line.split("\t")
        Bookings.append(
            Booking(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]))

    files = len(Bookings) / maxBookingsPerFile

    for x in range(0, files + 1):
        print "Creating Files for Bookings from "+str(x * maxBookingsPerFile)

        xml = E.GLTransactions(*genGLTransactions(
            Bookings[x * maxBookingsPerFile:(x + 1) * maxBookingsPerFile], currentBookingID))
        fobj = open(output + "GLTransactions" + str(x) + ".xml", "w")
        fobj.write("<eExact>\n")
        fobj.write(etree.tostring(xml, pretty_print=True))
        fobj.write("</eExact>")
        fobj.close()
        currentBookingID += maxBookingsPerFile

    return currentBookingID + len(Bookings)


def makeXMLAccounts(file, output, config):
    xml = E.Accounts(*genAccounts(file, output, config))

    fobj = open(output + "Relaties.xml", "w")
    fobj.write("<eExact>")
    fobj.write(etree.tostring(xml, pretty_print=True))
    fobj.write("</eExact>")
    fobj.close()


"""
HELPER FUNCTIONS
"""


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    return ''


def ensure_dir(folder):
    dir = os.path.dirname(folder)
    if not os.path.exists(dir):
        os.makedirs(dir)


if __name__ == "__main__" :

    timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")

    ensure_dir(INPUTDIR)
    ensure_dir(OUTPUTDIR)
    ensure_dir(OUTPUTDIR_BACKUP)

    cls()

    print "# BOOKKEEPING CONVERTER {0}".format(version)
    print "# converts .txt files from easyVET to .xml files for exact"
    print '##########################################################################\n'
    print "Please place the BuchungF1.txt and DebitorF1.txt export file from easyVET in the {0} " \
          "Folder and press any key to continue".format(INPUTDIR)

    raw_input()

    cls()

    print "Files will be converted....\n\n"

    print "\n\nConversion finished!\n\n"
    print "WARNING! Files to import have been created in the {0} Folder. Please make sure that " \
          "all accounts which are listed in the file AccountsToCreate.txt are created UP FRONT " \
          "in exact\n\n".format(OUTPUTDIR)

    i = str(raw_input("""Please import files now to EXACT. Was the import sucessfull confirm it
                         with y otherwise enter n """))

    if i == "y":
        Config = ConfigParser()
        Config.read(CONFIGFILE)
        Config.set('COUNTERS', 'BOOKINGID', str(newbookingid))
        cfgfile = open("./config.ini", "w")
        Config.write(cfgfile)
        cfgfile.close()

        cls()

        print "Export and Import was sucessfull files will be now backuped to {0} " \
              "folder".format(OUTPUTDIR)

        filelist = [f for f in os.listdir(OUTPUTDIR)]
        for f in filelist:
            shutil.copy(OUTPUTDIR+f, OUTPUTDIR_BACKUP+timestamp+"_"+f[:-4]+".xml")

    raw_input("Press any key to close the converter")


# TODO: Export fuer mehrere firmen
# TODO: User Interface
# TODO: XML API: https://developers.exactonline.com/#XMLIntro.html
# TODO: Per API pruefen ob alle Konten angelegt
