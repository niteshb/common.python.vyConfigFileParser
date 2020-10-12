import re
from typing import List
from . import VyConfigFileLine

class VyConfigFile():
    def __init__(self, configFilePath: str):
        self.indent = None
        self.configFilePath = configFilePath
        self.preProcess()

    def parse(self, TopLevelBlockClass):
        topBlock = TopLevelBlockClass()
        topBlock._VyTreeLevelNode__level = -1
        topBlock.parse(self.lines)
        return topBlock

    def preProcess(self):
        lines = open(self.configFilePath, 'r').readlines()
        lines = self.lines = [VyConfigFileLine(line, idx) for idx, line in enumerate(lines)]

        for line in lines:
            line.txt = line.txt.rstrip()

        # discovering indent
        for line in lines:
            matchObj = re.match(r'^(\s+).*', line.txt)
            indented = True if matchObj else False
            if not indented:
                continue
            indent = matchObj.group(1)
            if indent == '\t':
                pass
            elif indent[0] == ' ':
                if indent != ' ' * len(indent):
                    raise Exception('Mixed character indent. First char is a space. It should be a tab or 4 spaces.')
                if len(indent) < 4:
                    raise Exception('Too less indent. It should be 4 spaces instead of %d.' % len(indent))
                elif len(indent) < 4:
                    raise Exception('Too much indent. It should be 4 spaces instead of %d.' % len(indent))
            else:
                raise Exception('Unsupported indent. It should be a tab or 4 spaces.')
            self.indent = indent
            break
        del indented, indent

        # checking consistent indents
        for line in lines:
            matchObj = re.match(r'^(\s*)(.*)', line.txt)
            line.indent = matchObj.group(1)
            line.rtxt = line.txt
            line.txt = matchObj.group(2)
            if line.indent != self.indent[0] * len(line.indent):
                raise Exception('Mixed characters indent at line number %d' % (line.idx + 1))
            if len(line.indent) % len(self.indent) != 0:
                raise Exception('Bad indent at line number %d' % (line.idx + 1))
            line.indentLevel = len(line.indent) // len(self.indent)
