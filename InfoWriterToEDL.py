#!/usr/bin/env python

from argparse import ArgumentParser
from enum import IntEnum, StrEnum
from io import TextIOWrapper
from pathlib import Path
from sys import exit
import re
import traceback


def secondsToHMS(seconds: int):
    m, sec = divmod(seconds, 60)
    hr, min = divmod(m, 60)
    return "{0:02d}:{1:02d}:{2:02d}".format(hr, min, sec)

def secondsToHMSF(seconds: int, frame: int = 0):
    m, sec = divmod(seconds, 60)
    hr, min = divmod(m, 60)
    return "{0:02d}:{1:02d}:{2:02d}:{3:02d}".format(hr, min, sec, frame)

def HMSToSeconds(timestamp: str):
    m = re.match('^(\\d+):(\\d\\d):(\\d\\d)', timestamp)
    if m == None: raise Exception('Failed to parse timestamp in {0}'.format(timestamp))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


class TimestampColor(StrEnum):
    Unknown = 'UNKNOWN'
    Blue = 'Blue'
    Cyan = 'Cyan'
    Green = 'Green'
    Yellow = 'Yellow'
    Red = 'Red'
    Ping = 'Ping'
    Purple = 'Purple'
    Fuchsia = 'Fuchsia'
    Rose = 'Rose'
    Lavender = 'Lavender'
    Sky = 'Sky'
    Mint = 'Mint'
    Lemon = 'Lemon'
    Sand = 'Sand'
    Cocoa = 'Cocoa'
    Cream = 'Cream'


class Timestamp:
    def __init__(self, name: str = "", timeSeconds: int = 0):
        self.mName = name
        self.mTimeSeconds = timeSeconds
        self.mColor = TimestampColor.Blue

    def setColor(self, c: TimestampColor):
        self.mColor = c

    def setName(self, name: str):
        self.mName = name

    def outputEDL(self, file: TextIOWrapper, eventOrdinal: int):
        timestamp = secondsToHMSF(self.mTimeSeconds, 0)
        timestampPlusOne = secondsToHMSF(self.mTimeSeconds, 1)
        file.writelines([
            "{0:03d}  001      V     C         {1} {2} {1} {2}\n".format(eventOrdinal, timestamp, timestampPlusOne),
            " |C:ResolveColor{0} |M:{1} |D:1\n".format(self.mColor.name, self.mName),
            "\n"
        ])

    def __str__(self):
        return "({0}, {1}) {2}".format(secondsToHMSF(self.mTimeSeconds), self.mColor.name, self.mName)

    def getTimestamp(self):
        return self.mTimeSeconds

    def shiftTimestamp(self, secondsAdd: int):
        self.mTimeSeconds = self.mTimeSeconds + secondsAdd



class InfoWriterReaderState(IntEnum):
    UNKNOWN = 0
    EMPTY_LINE = 1
    EVENT = 2
    HOTKEY = 3
    RECORD_TIME = 4
    STREAM_TIME = 5

class ConverterState(StrEnum):
    MAIN_MENU = '0'
    CONVERT = '1'
    LIST = '2'
    RENAME_SINGLE = '3'
    EDIT_COLOR_SINGLE = '4'
    EDIT_COLOR_NAME_GROUP = '5'
    SHIFT_TIMESTAMPS = '6'
    EXIT = 'Q'

def stateToPrettyString(state: ConverterState):
    match state:
        case ConverterState.CONVERT: return "Convert to EDL"
        case ConverterState.LIST: return "List timestamps"
        case ConverterState.RENAME_SINGLE: return "Rename timestamp"
        case ConverterState.EDIT_COLOR_SINGLE: return "Change single timestamp's color"
        case ConverterState.EDIT_COLOR_NAME_GROUP: return "Change timestamp color by name group"
        case ConverterState.SHIFT_TIMESTAMPS: return "Shift all timestamps' times"
        case ConverterState.EXIT: return "Exit"
        case _: return "UNKNOWN/INVALID/THIS SHOULD NOT BE SEEN"

class TimestampConverter:
    def __init__(self, filePath: str, fromStream: bool = False, includeDateTime: bool = False):
        self.mInputPath = Path(filePath)
        self.mFromStream = fromStream
        self.mIncludeDateTime = includeDateTime
        self.mTimestamps: list[Timestamp] = []
        self.mTimestampNameGroups: dict[str, list[Timestamp]] = {}

    def determineInfoWriterLineType(self, line: str):
        if len(line) == 0: return InfoWriterReaderState.EMPTY_LINE
        if line.startswith('EVENT:'): return InfoWriterReaderState.EVENT
        if line.startswith('HOTKEY:'): return InfoWriterReaderState.HOTKEY

        # it's neither an event nor a hotkey, so it has to be a parseable timestamp and either
        # "Record Time Marker" or "Stream Time Marker". If it's neither, return UNKNOWN
        m = re.match('^\\d:\\d\\d:\\d\\d (.*) Time.*$', line)
        if m == None: return InfoWriterReaderState.UNKNOWN

        if m.group(1) == 'Record': return InfoWriterReaderState.RECORD_TIME
        elif m.group(1) == 'Stream': return InfoWriterReaderState.STREAM_TIME
        else: return InfoWriterReaderState.UNKNOWN

    # atIndex points where to insert the timestamp; negative value appends at the end
    def addTimestamp(self, timestamp: Timestamp, atIndex: int = -1):
        if atIndex < 0:
            self.mTimestamps.append(timestamp)
        else:
            self.mTimestamps.insert(atIndex, timestamp)

        if timestamp.mName not in self.mTimestampNameGroups:
            self.mTimestampNameGroups[timestamp.mName] = list[Timestamp]()
        self.mTimestampNameGroups[timestamp.mName].append(timestamp)
        self.mTimestampNameGroups[timestamp.mName].sort(key=Timestamp.getTimestamp)

    def delTimestamp(self, timestamp: Timestamp):
        self.mTimestamps.remove(timestamp)
        self.mTimestampNameGroups[timestamp.mName].remove(timestamp)
        if len(self.mTimestampNameGroups[timestamp.mName]) == 0:
            self.mTimestampNameGroups.pop(timestamp.mName)

    def queryIndex(self, thing: str, max: int):
        index = 0
        while True:
            o = input("\nPick a {0} to edit by name (1-{1}, Q to cancel): ".format(thing, max))
            if o.capitalize() == 'Q': return 0
            try:
                index = int(o)
                if index < 1 or index > max: raise ValueError("Index invalid")
                break
            except ValueError:
                print("Incorrect option {0}".format(o))

        return index

    def queryColor(self):
        print("\nAvailable colors are:")
        colorLine = ""
        counter = 0
        COLOR_PER_LINE = 4
        for c in TimestampColor:
            if c == TimestampColor.Unknown: continue

            colorLine += c.name
            if counter < len(TimestampColor): colorLine += ', '
            counter += 1
            if divmod(counter, COLOR_PER_LINE)[1] == 0:
                print('  {0}'.format(colorLine))
                colorLine = ""

        color = TimestampColor.Unknown
        while True:
            o = input("\nType a color to add (Q to cancel): ")
            if o.capitalize == 'Q': return TimestampColor.Unknown
            try:
                color = TimestampColor(o)
                break
            except ValueError:
                print("Incorrect option {0}".format(o))

        return color

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
        readerState = InfoWriterReaderState.UNKNOWN
        with open(self.mInputPath, "rt") as inputFile:
            lastReadEventName = ""
            lastReadEventTimestampSeconds = 0
            writtenTimestamps = 0
            for line in inputFile:
                line = line.rstrip()

                # determine what line we read
                readerState = self.determineInfoWriterLineType(line)
                match readerState:
                    case InfoWriterReaderState.EMPTY_LINE:
                        pass
                    case InfoWriterReaderState.EVENT:
                        m = re.search('^EVENT:(.+) @ (.+)$', line)
                        if m == None: raise Exception('Failed to parse EVENT line: {0}'.format(line))
                        lastReadEventName = m.group(1)
                        if self.mIncludeDateTime: lastReadEventName += ' @ ' + m.group(2)
                    case InfoWriterReaderState.HOTKEY:
                        m = re.search('^HOTKEY:(.+) @ (.+)$', line)
                        if m == None: raise Exception('Failed to parse HOTKEY line: {0}'.format(line))
                        lastReadEventName = m.group(1)
                        if self.mIncludeDateTime: lastReadEventName += ' @ ' + m.group(2)
                    case InfoWriterReaderState.RECORD_TIME:
                        if not self.mFromStream:
                            lastReadEventTimestampSeconds = HMSToSeconds(line.split(' ')[0])
                            self.addTimestamp(Timestamp(lastReadEventName, lastReadEventTimestampSeconds))
                            writtenTimestamps += 1
                    case InfoWriterReaderState.STREAM_TIME:
                        if self.mFromStream:
                            lastReadEventTimestampSeconds = HMSToSeconds(line.split(' ')[0])
                            self.addTimestamp(Timestamp(lastReadEventName, lastReadEventTimestampSeconds))
                            writtenTimestamps += 1
                    case _:
                        raise Exception("Invalid line found when reading file ({1} characters): {0}".format(line, len(line)))

    def processSummary(self):
        print("\nTimestamp file has {0} timestamps ({1} different event names)\n".format(len(self.mTimestamps), len(self.mTimestampNameGroups.keys())))
        print("Choose what to do:")
        counter = 1
        for e in ConverterState:
            if e == ConverterState.MAIN_MENU: continue
            if e == ConverterState.EXIT: print("  ========")
            print("  {0}. {1}".format(e.value, stateToPrettyString(e)))

            counter += 1

        while True:
            print("")
            o = input("Option: ")
            try:
                return ConverterState(o.capitalize())
            except ValueError:
                print("Incorrect option {0}".format(o))

    def processConvert(self):
        title = input("Type title to be added on top of file: ")

        outPath = self.mInputPath.with_suffix(".edl")

        if not self.queryConfirmation(preamble="Will convert to file {0}".format(outPath),
                                      prompt="Is that okay?"):
            return ConverterState.MAIN_MENU

        if outPath.exists():
            if not self.queryConfirmation("File {0} already exists, overwrite?".format(outPath)):
                return ConverterState.MAIN_MENU

        with open(outPath, "w+t") as file:
            file.writelines([
                "TITLE: {0}\n".format(title),
                "FCM: NON-DROP FRAME\n",
                "\n"
            ])

            counter = 1
            for t in self.mTimestamps:
                t.outputEDL(file, counter)
                counter += 1

        print("Generated EDL file {0}".format(outPath))
        return ConverterState.MAIN_MENU

    def processRenameSingle(self):
        tIndex = self.queryIndex("timestamp", len(self.mTimestamps))
        if tIndex == 0: return ConverterState.MAIN_MENU

        tIndex -= 1
        timestamp = self.mTimestamps[tIndex]
        print("Will rename timestamp:\n  {0}. {1}".format(tIndex, str(timestamp)))

        newName = ""
        while True:
            newName = input("\nNew name: ")
            confirmation = ""
            while True:
                print("\nWill rename Timestamp to {0}".format(newName))
                confirmation = input("Is this okay? (y - Yes, n - No, Q - cancel): ").capitalize()
                if confirmation == 'Y': break
                elif confirmation == 'Q':
                    print("Aborting rename")
                    return ConverterState.MAIN_MENU
                elif confirmation != 'N':
                    print("Invalid option: {0}".format(confirmation))
            if confirmation == 'Y': break

        self.delTimestamp(timestamp)
        timestamp.setName(newName)
        self.addTimestamp(timestamp, tIndex)

        print("\nRenamed timestamp:\n  {0}. {1}".format(tIndex, str(timestamp)))
        print("Note that timestamp colors are NOT reflected in the input file")

        return ConverterState.MAIN_MENU

    def processEditColorSingle(self):
        tIndex = self.queryIndex("timestamp", len(self.mTimestamps))
        if tIndex == 0: return ConverterState.MAIN_MENU

        tIndex -= 1
        timestamp = self.mTimestamps[tIndex]
        print("Will edit color of timestamp:\n  {0}. {1}".format(tIndex, str(timestamp)))

        color = self.queryColor()
        if color == TimestampColor.Unknown: return ConverterState.MAIN_MENU

        timestamp.setColor(color)
        print("\nTimestamp edited, now is:\n  {0}. {1}".format(tIndex, str(timestamp)))
        print("Note that timestamp colors are NOT reflected in the input file")
        return ConverterState.MAIN_MENU

    def processEditColorNameGroup(self):
        print("\nAvailable name groups:")
        counter = 1
        for group in self.mTimestampNameGroups.keys():
            print("  {0}. {1}".format(counter, group))
            counter += 1

        gIndex = self.queryIndex("group", len(self.mTimestampNameGroups.keys()))
        if gIndex == 0: return ConverterState.MAIN_MENU

        gName = list(self.mTimestampNameGroups.keys())[gIndex - 1]
        timestampList = self.mTimestampNameGroups[gName]

        print("Will batch-edit color of {0} timestamps titled {1}".format(len(timestampList), gName))

        color = self.queryColor()
        if color == TimestampColor.Unknown: return ConverterState.MAIN_MENU

        for t in timestampList:
            t.setColor(color)

        print("Updated {0} timestamps from group {1}".format(len(timestampList), gName))
        print("Note that timestamp colors are NOT reflected in the input file")
        return ConverterState.MAIN_MENU

    def processList(self):
        print("Available Timestamps:")
        counter = 1
        for t in self.mTimestamps:
            print("  {0}. {1}".format(counter, str(t)))
            counter += 1

        return ConverterState.MAIN_MENU

    def processShiftTimestamps(self):
        print("\nThis option will shift all timestamps forward by provided time.")
        timeSeconds = 0
        while True:
            time = input("Provide time shift in \"H:MM:SS\" format (Q to cancel): ")
            if time.capitalize() == 'Q':
                return ConverterState.MAIN_MENU

            try:
                timeSeconds = HMSToSeconds(time)
                break
            except Exception:
                print("Incorrect value provided")

        if not self.queryConfirmation(preamble="\nWill shift all timestamps by {0} ({1} seconds)".format(secondsToHMS(timeSeconds), timeSeconds),
                                      prompt="Is this okay?"):
            return ConverterState.MAIN_MENU

        for t in self.mTimestamps:
            t.shiftTimestamp(timeSeconds)

        print("\nShifted all timestamps by {0}".format(secondsToHMS(timeSeconds)))
        return ConverterState.MAIN_MENU

    def mainLoop(self):
        print("=== InfoWriter log to EDL converter ===")
        if not self.mInputPath.exists():
            print("Provided file path does not exist")
            exit(1)

        self.readInputFile()
        print("Timestamp file {0} parsed successfully.".format(self.mInputPath))

        state = ConverterState.MAIN_MENU
        while state != ConverterState.EXIT:
            match state:
                case ConverterState.MAIN_MENU: state = self.processSummary()
                case ConverterState.CONVERT: state = self.processConvert()
                case ConverterState.LIST: state = self.processList()
                case ConverterState.RENAME_SINGLE: state = self.processRenameSingle()
                case ConverterState.EDIT_COLOR_SINGLE: state = self.processEditColorSingle()
                case ConverterState.EDIT_COLOR_NAME_GROUP: state = self.processEditColorNameGroup()
                case ConverterState.SHIFT_TIMESTAMPS: state = self.processShiftTimestamps()
                case _: pass

        print("\nCheers, enjoy your day\n")


def main():
    try:
        parser = ArgumentParser(
            prog='InfoWriterToEDL',
            description='Program converting InfoWriter log file to DaVinci Resolve-compatible EDL timeline marker list'
        )
        parser.add_argument('filepath', help='Path to InfoWriter log file. Output will be in the same directory under the same name with .edl extension')
        parser.add_argument('-s', '--stream', help='Consider stream markers instead of record markers',
                            action='store_true', default=False)
        parser.add_argument('-f', '--full', help='Read full event name - adds event\'s date and time to timestamp name',
                            action='store_true', default=False)
        args = parser.parse_args()

        TimestampConverter(args.filepath, args.stream).mainLoop()
    except Exception as e:
        print("Exception caught by main: {0}".format(e))
        traceback.print_exception(e)
        exit(1)

if __name__ == "__main__":
    main()
