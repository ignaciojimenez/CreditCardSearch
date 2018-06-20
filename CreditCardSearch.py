import re
import time
import sys
import getopt
import os
import zipfile
import shutil
import io
# Installed modules
import xlrd
from PyPDF2 import PdfFileReader


def checksum(string):
    '''
    Check the Luhn algorithm on the given string
    Returns True/False
    '''
    odd_sum = sum(list(map(int, string))[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in list(map(int, string))[-2::-2]])
    return ((odd_sum + even_sum) % 10 == 0)


def searchInLine(textLine, line_position, cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given plain text line
    Prints the credit card match if it occurs
    Retuns 1 if a CC is found 0 if not
    '''
    # TODO Search for multiple matches within single line
    counter = 0
    for regEx in regex_list:
        m = re.search(r"%s" % regEx[1].rstrip(), textLine)
        if m:
            if checksum(m.group(0)):
                if mask:
                    print(cc_path + "\t" + line_position + "\t" + regEx[0].rstrip() + "\t" +
                          m.group(0)[:6] + "******" + m.group(0)[-4:])
                else:
                    print(cc_path + "\t" + line_position + "\t" +
                          regEx[0].rstrip() + "\t" + m.group(0))
                counter += 1
    return counter


def textFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given plain text file
    Retuns int total of credit cards found
    '''
    counter = 0
    line_counter = 1
    with open(cc_path, 'r', encoding="latin-1") as cc_file_data:
        for cc_file_line in cc_file_data:
            counter += searchInLine(cc_file_line, "Line_" +
                                    str(line_counter), cc_path, regex_list, mask)
            line_counter += 1
    return counter


def pdfFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given Excel File
    Retuns int total of credit cards found
    '''
    pdfCounter = 0  # Stores total CC numbers found in pdf
    pdfPageCount = 0  # Page iterator counter
    text = ""  # Contains all the extracted text

    pdfReader = PdfFileReader(open(cc_path, 'rb'))
    # While loop will read each page
    while pdfPageCount < pdfReader.numPages:
        pageObj = pdfReader.getPage(pdfPageCount)
        pdfPageCount += 1
        text += pageObj.extractText()
        buf = io.StringIO(pageObj.extractText())
        linecount = 0
        for line in buf:
            linecount += 1
            pdfCounter += searchInLine(line, "Page" + str(pdfPageCount) +
                                       "_Line" + str(linecount), cc_path, regex_list, mask)
    # If everything included in the PDF is scanned (PyPDF cannot extract text from images).
    if text == "":
        print(cc_path + " --> PDF file contains no text")
    return pdfCounter


def excelFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given Excel File
    Retuns int total of credit cards found
    '''
    counter = 0
    with xlrd.open_workbook(cc_path) as wb:
        for sheet in wb.sheets():
            for row in range(sheet.nrows):
                counter += searchInLine(','.join(sheet.row_values(row)),
                                        str(sheet.name) + "_row" + str(row), cc_path, regex_list, mask)
    return counter


def zipFSearch(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given zip File
    Retuns int total of credit cards found
    '''
    # TODO Print relative paths not absolute
    zipCount = 0
    with zipfile.ZipFile(cc_path, 'r') as zfile:
        print("-- Opening ZIP FILE --> " + cc_path)
        for finfo in zfile.infolist():
            fileCount = 0
            fileCount += searchInFile(zfile.extract(finfo), regex_list, mask)
            fileCount = (0 if fileCount < 0 else fileCount)
            print(os.path.join(cc_path, finfo.filename) + " --> " +
                  str(fileCount) + " credit cards in file - Inside ZIP file")
            zipCount += fileCount
            if "/" in finfo.filename:
                shutil.rmtree(finfo.filename.split("/")[0])
            else:
                os.remove(finfo.filename)
    print("-- End of ZIP FILE --> " + cc_path)
    return zipCount


def searchInFile(cc_path, regex_list, mask):
    '''
    Looks for credit cards within a given file
    Retuns int total of credit cards found, -1 if file is not supported
    '''
    if any(cc_path[-3:].lower() in s for s in unsupported_files):
        print(cc_path + " --> Unsupported file")
        return -1
    elif any(cc_path[-3:].lower() in s for s in ['xls', 'xlsx']):
        return excelFSearch(cc_path, regex_list, mask)
    elif any(cc_path[-3:].lower() in s for s in ['pdf']):
        return pdfFSearch(cc_path, regex_list, mask)
    elif zipfile.is_zipfile(cc_path):
        return zipFSearch(cc_path, regex_list, mask)
    else:
        # TODO Auto-find out if file can be read as plain text
        return textFSearch(cc_path, regex_list, mask)


def searchInDir(cc_path, regex_list, mask):
    '''
    Searchs for credit cards in files contained within a given path
    Returns tuple containing Files read, Files analyzed, Files including credit cards, Total credit cards found
    '''
    count_cc_total = 0  # Total credit cards found in files
    count_nocc_files = 0  # Files containing no credit cards
    count_discarded_files = 0  # Files discarded because they are not supported
    count_cc_files = 0  # Files containing credit cards

    # Loop over the given path
    for root, dirs, files in os.walk(cc_path):
        for filename in files:
            count_fichero = searchInFile(
                os.path.join(root, filename), regex_list, mask)
            # If CC found
            if count_fichero > 0:
                count_cc_files += 1
                print(os.path.join(root, filename) + " --> " +
                      str(count_fichero) + " credit cards in file")
            # If no CC found
            elif count_fichero == 0:
                print(os.path.join(root, filename) + " --> " +
                      str(count_fichero) + " credit cards in file")
                count_nocc_files += 1
            # If file was discarded
            elif count_fichero < 0:
                count_discarded_files += 1
                count_fichero = 0
            # Add total CC found during execution
            count_cc_total += count_fichero
    return count_cc_files + count_discarded_files + count_nocc_files, count_cc_files + count_nocc_files, count_cc_files, count_cc_total


if __name__ == '__main__':
    # reading input options
    inputfile = ''
    inputdir = ''
    masking = True
    # TODO Output file
    # TODO Useful Command Help text
    # TODO quiet option 1 --> Hide credit card details
    # TODO quiet option 2 --> Hide every file detail (only total execution)
    # TODO Change separator in stdout from \t to ',' for CSV ready processing
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:d:m")
    except getopt.GetoptError:
        # TODO Read current dir files as the default option
        print('Syntax: CreditCardSearch.py -i <inputfile> -d <inputdirectory> [-m] ')
        sys.exit(2)
    if not opts:
        print('Syntax: CreditCardSearch.py -i <inputfile> -d <inputdirectory> [-m] ')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage CreditCardSearch.py -i <inputfile> -d <inputdirectory> -o <outputfile> -m')
            sys.exit()
        elif opt in ("-i"):
            inputfile = arg
        elif opt in ("-d"):
            inputdir = arg
        elif opt in ("-m"):
            masking = False

    # File extension support variables
    # TODO PDF, docx, pptx, etc.
    tested_files = ['txt', 'csv', 'xls', 'xlsx', 'rtf', 'xml', 'html', 'json', 'zip', 'pdf']
    unsupported_files = ['doc', 'docx', 'pptx', 'jpg', 'gif',
                         'png', 'mp3', 'mp4', 'wav', 'aiff', 'mkv', 'avi', 'exe', 'dll']

    # Print memo when the script starts
    print("[" + time.ctime() + "] CreditCardSearch started")

    # Read CSV regex file to be tested
    regex_path = 'regexcard.csv'
    regex_list = []
    with open(regex_path, 'r') as regex_file:
        for line in regex_file:
            line_list = line.rstrip().split(',')
            regex_list.append(line_list)

    # If the script has received a directory to search
    if inputdir:
        dirResult = searchInDir(inputdir, regex_list, masking)
        print("--- Execution Summary ---")
        print(str(dirResult[0]) + "\tFiles read")
        print(str(dirResult[1]) + "\tFiles analyzed")
        print(str(dirResult[2]) + "\tFiles including credit cards")
        print(str(dirResult[3]) + "\tTotal credit cards found")

    # If the script received a single file to analyze
    elif inputfile:
        print(inputfile + " --> " + str(searchInFile(inputfile,
                                                     regex_list, masking)) + " credit cards in file\n")

    print("\n--- Disclaimer ---")
    print("CreditCardSearch tries to read data included in any file and excludes known unsuppoted files")
    print("Tested files include: %s" % ','.join(tested_files))
    print("Unsupported files include: %s" % ','.join(unsupported_files))
