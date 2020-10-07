import re

class VyConfigFileBlock():
    def __init__(self):
        self.subblocks = []
        self.indentLevel = 0
        self.attribs = {}

    def __repr__(self):
        return repr((self.attribs, self.subblocks))

    def peekmatch(self, line):
        iMarkers = self.indentLevelMarkers[0]
        matches = { 'attr=None': 0, 'attr!=None': 0 }
        if type(iMarkers) == dict:
            for key in iMarkers.keys():
                attr = key[0]
                if attr == None:
                    pattern = r'(%s)' % key[1]
                    attrLabel = 'attr=None'
                else:
                    pattern = r'(%s)\s*:\s*(%s)' % key
                    attrLabel = 'attr!=None'
                matchObj = re.match(pattern, line.txt)
                if matchObj:
                    matches[attrLabel] += 1
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
        attrLabels = ['attr=None', 'attr!=None']
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
                keys = iMarkers.keys()
                attrNoneKeys = []
                matchObj = None
                for key in keys:
                    if key[0] == None:
                        attrNoneKeys.append(key)
                        continue
                    pattern = r'(?P<attr>%s)\s*:\s*(?P<val>%s)' % key
                    matchObj = re.match(pattern, line.txt)
                    if matchObj:
                        if 'target' in iMarkers[key] and iMarkers[key]['target'] == None:
                            break
                        attr = matchObj.group('attr')
                        val = matchObj.group('val')
                        if 'mode' in iMarkers[key] and iMarkers[key]['mode'] == 'append':
                            if attr not in self.attribs:
                                self.attribs[attr] = []
                            self.attribs[attr].append(val)
                        else:
                            self.attribs[attr] = val
                        break
                # if no match and if None is a key
                if not matchObj:
                    for key in attrNoneKeys: 
                        attr = iMarkers[key]['target']
                        pattern = r'(?P<val>%s)' % key[1]
                        matchObj = re.match(pattern, line.txt)
                        if matchObj:
                            val = line.txt
                            if 'mode' in iMarkers[key] and iMarkers[key]['mode'] == 'append':
                                if attr not in self.attribs:
                                    self.attribs[attr] = []
                                self.attribs[attr].append(val)
                            else:
                                self.attribs[attr] = val
                            break
                    if not matchObj:
                        raise Exception('No matching case found at line %d' % (line.idx + 1))
            elif type(iMarkers) == list:
                if len(iMarkers) == 0:
                    raise Exception('List found empty. Put some subblock classes here')
                matchClasses = { 'attr=None': [], 'attr!=None': []}
                for iMarker in iMarkers:
                    submatches = iMarker().peekmatch(line)
                    for attrLabel in attrLabels:
                        if submatches[attrLabel]:
                            matchClasses[attrLabel].append(iMarker)
                matchedClass = None
                for attrLabel in attrLabels:
                    assert(len(matchClasses[attrLabel]) <= 1)

                if matchClasses['attr!=None']:
                    matchedClass = matchClasses['attr!=None'][0]
                elif matchClasses['attr=None']:
                    matchedClass = matchClasses['attr=None'][0]
                if matchedClass == None:
                    raise Exception("Line doesn't match any possibility")
                subblock = matchedClass() # subblock is object of matchedClass
                subblock.indentLevel = line.indentLevel
                idx = subblock.parse(lines, startIdx=idx) - 1 # because we had added +1 in the while loop
                self.subblocks.append(subblock)
            else:
                raise Exception("FATAL ERROR: Unexpected type. 'dict' or 'list' type was expected.")
        return idx # this is the length processed

