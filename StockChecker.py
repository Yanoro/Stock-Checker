import getopt,sys,os,subprocess,re,datetime,pandas
from bs4 import BeautifulSoup
import urllib.request

from html.parser import HTMLParser

start = datetime.date(2016,2,18)
end = datetime.date(2019,9,18)

#Place Output in text file in this format: Date:Stock Code:Current_Price
#Colocar o valor atual do stock em uma coluna da tabela da spreadsheet

def Usage():
    print("StockChecker.py usage \n -r, --read | Print local Directory's pdf Files \n -d, --directory | Change default directory(Default is the current Directory")

def Get_PDFText(Lines, Spreadsheet_Columns):
    Spreadsheet = []
    columnum = 0
    for Column in Spreadsheet_Columns:
        match = [Line for Line in Lines if Column in Line]
        index = Lines.index(match[0])
        itemnum = 0
        tempList = []
        try:
            while Lines[index + itemnum] != "\n":
                tempList.insert(itemnum, Lines[index + itemnum])
                itemnum += 1
        except:
            print("Couldn't find the Column, exiting...")
            exit(1)
        Spreadsheet.insert(columnum, tempList)
        columnum += 1
        del index

    return Spreadsheet

def lengths(x):
    if isinstance(x,list):
        yield len(x)
        for y in x:
            yield from lengths(y)

def Resize_SpreadSheet(SpreadSheet):
    Biggest_ListSize = max(lengths(SpreadSheet))
    for Row in SpreadSheet:
        while len(Row) < Biggest_ListSize:
            Row.insert(len(Row), "")

def Print_Info(SpreadSheet, Date):
    #print ("Date:", Date)
    DataFrame = {}
    for Column in SpreadSheet:
        DataFrame.update({Column[0].rstrip() : map(str.rstrip, Column[1:])})
    #Can probaly do this in one line, but i think its more readable this way
    Panda = pandas.DataFrame(data=DataFrame)
    print (Panda)
    print ()


def Write_Output(Stock_Prices, Date, Stock_Symbols, Filename):
    OutputFile = open(Filename, 'a')
    for Symbol, Price in zip(Stock_Symbols, Stock_Prices):
        OutputFile.write("{}:{}:{}\n".format(Date, Symbol, Price))
    OutputFile.close()

def Title_ToStockSymbol(Spreadsheet):
    Stock_Symbol = []

    for Column in Spreadsheet:
        if "Especificação do título" in Column[0] :
            Stock_Symbol = [None] * len(Column)
            for Stock, Index in zip(Column, range(-1, len(Column))):
                Stock_Names = open("Stock_Names", 'r')    #remember to check if i can remove this
                for Line in Stock_Names:
                    if Stock in Line:
                        Stock_Symbol[Index] = ""
                        for Letter in Line:
                            if Letter == ":":
                                break;
                            else:
                                Stock_Symbol[Index] += Letter

    for Stock in Stock_Symbol:
        if Stock is None:
            Stock_Symbol.remove(Stock)
    return Stock_Symbol

def Get_CurrentPrice(Symbols):
    Stock_Prices = []
    for Symbol, Index in zip(Symbols,range(0,len(Symbols))):
            if Symbol is None:
                continue
            Stock_html = urllib.request.urlopen("https://www.marketwatch.com/investing/stock/" + Symbol + "?countrycode=br").read()
            soup = BeautifulSoup(Stock_html, 'html.parser')
            Stock_Prices.insert(Index, soup.find("meta", {"name": "price"})['content'])

    Stock_Prices.insert(0, "Current Prices")
    return Stock_Prices



def Print_StockPrices(Stock_Symbols, Stock_Prices):
    for Symbol,Price in zip(Stock_Symbols, Stock_Prices):
        try:
            if Price is None:
                print ("Couldn't find it, maybe something wrong with the Stocks_Name File?")
                continue
            print("The Current Price of", Symbol, "is" , Price)
        except:
            print ("Something went wrong searching for this Symbol")

try:
    opts, args = getopt.getopt(sys.argv[1:],"ro:d:c:f:p",["read","output", "directory","Columns", "File","pdf"])
except getopt.GetoptError as err:
    print ("Something went wrong while trying to parse your input")
    exit(1)

Directory = "./"
Read = False
File = False
Output = False


Columns = ["Q Negociação","C/V","Tipo Mercado", "Prazo", "Especificação do título", "Obs. Quantidade", "Preço/Ajuste","Valor/Ajuste", "D/C"]
#Columns = ["Especificação do título"]

for o,a in opts:
    if o in ("-r", "--read-pdf"):
        Read = True
    if o in ("-f", "--file"):
        File = a
    if o in ("-o", "--output"): #Remember to add option to choose file name
        Output = True
        Output_FileName = a
    if o in ("-d", "--directory"):
        Directory = a
        os.chdir(Directory)
    if o in ("-c", "--Columns"):
        Columns = a
    if o in ("-m", "--manual-upload"):
        Manual = True

if Read:

    files = os.listdir(Directory)
    print (files)
    for file in files:
        if (file[-3:] == "pdf"):
            subprocess.call(['pdftotext', file])
            FileName = file[:-3] + "txt"
            UpdateFile = open(FileName, 'r')
            print ("Opening:", FileName)
            Lines = list(UpdateFile)
            Date = re.search("\d{2}/\d{2}/\d{4}", str(Lines))
            date = datetime.datetime.strptime(Date.group(), '%d/%m/%Y').date() #Remember to initialize those values only once, such as price, date, etc
            SpreadSheet = (Get_PDFText(Lines,Columns))
            Symbols = Title_ToStockSymbol(SpreadSheet)
            Stock_Prices = Get_CurrentPrice(Symbols)
            SpreadSheet.insert(-1, Stock_Prices)
            #Print_StockPrices(Symbols, Stock_Prices)
            Resize_SpreadSheet(SpreadSheet)
            if Output:
                Write_Output(Stock_Prices, Date.group(), Symbols, Output_FileName)

            Print_Info(SpreadSheet, Date.group())      #Remember that i had to change orders from preadsheet and get Stock Prices
            UpdateFile.close()
            subprocess.call(['rm', file[:-3] + "txt"])

    exit(0)

Usage()
