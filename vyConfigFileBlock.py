import re
from vyTree import VyTreeLevelNode

class VyConfigFileBlock(VyTreeLevelNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indentLevel = 0
        self.attribs = {}

    @property
    def subBlocks(self):
        return self.childNodes

    def appendChildBlock(self, childBlock):
        self.appendChildNode(childBlock)

    def insertChildBlock(self, idx, childBlock):
        self.insertChildNode(idx, childBlock)

    def __contains__(self, key):
        return key in self.attribs

    def __getitem__(self, key):
        return self.attribs[key]

    def __setitem__(self, key, value):
        self.attribs[key] = value

    def __repr__(self):
        return repr((self.attribs, self.subBlocks))

    def getKeyMatchPattern(self, line, key, iMarkers):
        attr = key[0]
        if attr is None:
            pattern = r'^(?P<val>%s)$' % key[1]
            attrLabel = 'attr=None'
        else:
            pattern = r'^(?P<attr>%s)\s*:\s*(?P<val>%s)$' % key
            attrLabel = 'attr!=None'
        matchObj = re.match(pattern, line.txt)
        if matchObj:
            if attr is None:
                attr = iMarkers[key]['target']
            else:
                attr = matchObj.group('attr')
            val = matchObj.group('val')
        else:
            val = None
        return (matchObj, attr, val, attrLabel)

    def peekmatch(self, line):
        iMarkers = self.indentLevelMarkers[0]
        matches = { 'attr=None': 0, 'attr!=None': 0 }
        if type(iMarkers) == dict:
            for key in iMarkers.keys():
                matchObj, attr, val, attrLabel = self.getKeyMatchPattern(line, key, iMarkers)
                matches[attrLabel] += 1 if matchObj else 0
        elif type(iMarkers) == list:
            for iMarker in iMarkers:
                submatches = iMarker().peekmatch(line.txt)
                matches['attr=None'] += submatches['attr=None']
                matches['attr!=None'] += submatches['attr!=None']
        assert(matches['attr=None'] <= 1)
        assert(matches['attr!=None'] <= 1)
        return matches

    def parse(self, lines, startIdx=0):
        ilm = self.indentLevelMarkers
        topLevelConsumed = False
        idx = startIdx - 1
        while True:
            idx += 1
            if idx >= len(lines): break
            line = lines[idx]
            if not line.txt: continue # empty line
            relativeLineIndentLevel = line.indentLevel - self.indentLevel
            if relativeLineIndentLevel < 0: break # found higher order
            if relativeLineIndentLevel == 0 and type(ilm[0]) == dict and topLevelConsumed:
                break # found same indent level
            if re.match(r'^##.*', line.txt):
                continue # comment
            if idx == startIdx:
                if relativeLineIndentLevel != 0:
                    raise Exception('First line expected at top indent level')
                topLevelConsumed = True
            if relativeLineIndentLevel not in ilm:
                raise Exception(f"Unsupported indent level '{relativeLineIndentLevel}'. Expected indent levels: {ilm.keys()}")
            iMarkers = ilm[relativeLineIndentLevel]
            if type(iMarkers) == dict:
                # attr!=None gets priority
                keys = sorted(iMarkers.keys(), key=lambda key: 1 if key[0] == None else 0)
                for key in keys:
                    matchObj, attr, val, attrLabel = self.getKeyMatchPattern(line, key, iMarkers)
                    if not matchObj:
                        continue
                    if 'target' in iMarkers[key] and iMarkers[key]['target'] == None:
                        break
                    if 'mode' in iMarkers[key] and iMarkers[key]['mode'] == 'append':
                        if attr not in self.attribs:
                            self.attribs[attr] = []
                        self.attribs[attr].append(val)
                    else:
                        self.attribs[attr] = val
                    break
                # if no match and if None is a key
                if not matchObj:
                    raise Exception('No matching case found at line %d' % (line.idx + 1))
            elif type(iMarkers) == list:
                if len(iMarkers) == 0:
                    raise Exception('List found empty. Put some subBlock classes here')
                matchClasses = { 'attr=None': [], 'attr!=None': []}
                for iMarker in iMarkers:
                    submatches = iMarker().peekmatch(line)
                    for attrLabel in ['attr=None', 'attr!=None']:
                        if submatches[attrLabel]:
                            matchClasses[attrLabel].append(iMarker)
                matchedClass = None
                assert(len(matchClasses['attr=None']) <= 1)
                assert(len(matchClasses['attr!=None']) <= 1)

                if matchClasses['attr!=None']:
                    matchedClass = matchClasses['attr!=None'][0]
                elif matchClasses['attr=None']:
                    matchedClass = matchClasses['attr=None'][0]
                if matchedClass == None:
                    raise Exception("Line doesn't match any possibility")
                subBlock = matchedClass() # subBlock is object of matchedClass
                self.appendChildBlock(subBlock)
                subBlock.indentLevel = line.indentLevel
                idx = subBlock.parse(lines, startIdx=idx) - 1 # because we had added +1 in the while loop
            else:
                raise Exception("FATAL ERROR: Unexpected type. 'dict' or 'list' type was expected.")
        return idx # this is the length processed

