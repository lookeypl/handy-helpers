#!/usr/bin/env python

from argparse import ArgumentParser
from enum import IntEnum
from io import TextIOWrapper
from pathlib import Path
from sys import exit
import re
import traceback


def secondsToHMS(seconds: int):
    m, sec = divmod(seconds, 60)
    hr, min = divmod(m, 60)
    if hr == 0: return "{0:02d}:{1:02d}".format(min, sec)
    else: return "{0:d}:{1:02d}:{2:02d}".format(hr, min, sec)

def secondsToHMSF(seconds: int, frame: int = 0):
    m, sec = divmod(seconds, 60)
    hr, min = divmod(m, 60)
    return "{0:02d}:{1:02d}:{2:02d}:{3:02d}".format(hr, min, sec, frame)

def HMSToSeconds(timestamp: str):
    m = re.match('^(\\d+):(\\d\\d):(\\d\\d)', timestamp)
    if m == None: raise Exception('Failed to parse timestamp in {0}'.format(timestamp))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))

def HMSFToSeconds(timestamp: str):
    m = re.match('^(\\d+):(\\d\\d):(\\d\\d):(\\d\\d)', timestamp)
    if m == None: raise Exception('Failed to parse timestamp in {0}'.format(timestamp))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))



class Timestamp:
    def __init__(self, name: str = "", timeSeconds: int = 0):
        self.mName = name
        self.mTimeSeconds = timeSeconds

    def setName(self, name: str):
        self.mName = name

    def outputYTT(self, file: TextIOWrapper):
        file.writelines([
            "{0} {1}\n".format(secondsToHMS(self.mTimeSeconds), self.mName),
        ])

    def __str__(self):
        return "({0}) {1}".format(secondsToHMS(self.mTimeSeconds), self.mName)

    def getTimestamp(self):
        return self.mTimeSeconds


class EDLReaderState(IntEnum):
    UNKNOWN = 0
    EMPTY_LINE = 1
    TITLE = 2
    FCM = 3
    TIMESTAMP = 4
    DETAILS = 5

class EDLTimestampConverter:
    EDL_TIMESTAMP_REGEX = '^(\\d+)\\s+(\\d+)[\\sVC]+([\\d:]+) ([\\d:]+) ([\\d:]+) ([\\d:]+)\\s*$'
    EDL_DETAILS_REGEX = '^\\s*\\|C:([A-Za-z]+)\\s*\\|M:([\\w\\s\\-\'"!@#$%^&*()]+)\\s*\\|D:(\\d+)*\\s*$'

    def __init__(self, filePath: str):
        self.mInputPath = Path(filePath)
        self.mTimestamps: list[Timestamp] = []

    def determineEDLLineType(self, line: str):
        if len(line) == 0: return EDLReaderState.EMPTY_LINE
        if line.startswith('TITLE:'): return EDLReaderState.TITLE
        if line.startswith('FCM:'): return EDLReaderState.FCM

        m = re.match(self.EDL_TIMESTAMP_REGEX, line)
        if m != None: return EDLReaderState.TIMESTAMP

        m = re.match(self.EDL_DETAILS_REGEX, line)
        if m != None: return EDLReaderState.DETAILS

        return EDLReaderState.UNKNOWN

    # atIndex points where to insert the timestamp; negative value appends at the end
    def addTimestamp(self, timestamp: Timestamp, atIndex: int = -1):
        if atIndex < 0:
            self.mTimestamps.append(timestamp)
        else:
            self.mTimestamps.insert(atIndex, timestamp)

    def queryConfirmation(self, prompt: str, preamble: str = ""):
        while True:
            if len(preamble) > 0:
                print(preamble)

            a = input("{0} (y/n): ".format(prompt))
            if a.capitalize() == 'N': return False
            elif a.capitalize() == 'Y': return True
            else:
                print("Incorrect answer: {0}".format(a))

    def readInputFile(self):
        self.mTimestamps.clear()
        readerState = EDLReaderState.UNKNOWN
        lastReadEventTimestampSeconds = -1
        with open(self.mInputPath, "rt") as inputFile:
            for line in inputFile:
                line = line.rstrip()

                # determine what line we read
                readerState = self.determineEDLLineType(line)
                match readerState:
                    case EDLReaderState.EMPTY_LINE:
                        pass
                    case EDLReaderState.TITLE:
                        pass
                    case EDLReaderState.FCM:
                        pass
                    case EDLReaderState.TIMESTAMP:
                        m = re.search(self.EDL_TIMESTAMP_REGEX, line)
                        if m == None: raise Exception('Failed to parse TIMESTAMP line: {0}'.format(line))
                        lastReadEventTimestampSeconds = HMSToSeconds(m.group(3))
                    case EDLReaderState.DETAILS:
                        m = re.search(self.EDL_DETAILS_REGEX, line)
                        if m == None: raise Exception('Failed to parse DETAILS line: {0}'.format(line))
                        if lastReadEventTimestampSeconds == -1: raise Exception('Reading DETAILS line without first reading TIMESTAMP line: {0}'.format(line))
                        self.addTimestamp(Timestamp(m.group(2), lastReadEventTimestampSeconds))
                        lastReadEventTimestampSeconds = -1
                    case _:
                        raise Exception("Invalid line found when reading file ({0} state): {1}".format(readerState, line))

    def processSummary(self):
        print("\nTimestamp file has {0} timestamps\n".format(len(self.mTimestamps)))
        print("Available Timestamps:")
        counter = 1
        for t in self.mTimestamps:
            print("  {0}. {1}".format(counter, str(t)))
            counter += 1

    def processConvert(self):
        outPath = self.mInputPath.with_suffix(".txt")

        if not self.queryConfirmation(preamble="Will convert to file {0}".format(outPath),
                                      prompt="Is that okay?"):
            raise Exception('Conversion aborted')

        if outPath.exists():
            if not self.queryConfirmation("File {0} already exists, overwrite?".format(outPath)):
                raise Exception('Conversion aborted')

        with open(outPath, "w+t") as file:
            for t in self.mTimestamps:
                t.outputYTT(file)

        print("Generated YouTube Timestamp file {0}".format(outPath))

    def mainLoop(self):
        print("=== InfoWriter log to EDL converter ===")
        if not self.mInputPath.exists():
            print("Provided file path does not exist")
            exit(1)

        self.readInputFile()
        print("Timestamp file {0} parsed successfully.".format(self.mInputPath))

        self.processSummary()
        self.processConvert()

        print("\nCheers, enjoy your day\n")



def main():
    try:
        parser = ArgumentParser(
            prog='EDLToYouTubeTimestamp',
            description='Program converting InfoWriter log file to DaVinci Resolve-compatible EDL timeline marker list'
        )
        parser.add_argument('filepath', help='Path to InfoWriter log file. Output will be in the same directory under the same name with .edl extension')
        args = parser.parse_args()

        EDLTimestampConverter(args.filepath).mainLoop()
    except Exception as e:
        print("Exception caught by main: {0}".format(e))
        traceback.print_exception(e)
        exit(1)

if __name__ == "__main__":
    main()
