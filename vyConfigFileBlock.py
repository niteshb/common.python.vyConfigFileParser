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
        keys = iMarkers.keys()
        matches = { None: 0, 'NotNone': 0 }
        if type(iMarkers) == dict:
            if None in keys:
                matches[None] += 1
            notNoneKeys = set(keys) - {None}
            for key in notNoneKeys:
                pattern = r'(%s)\s*:\s*(%s)' % tuple(key.split(':'))
                matchObj = re.match(pattern, line.txt)
                if matchObj:
                    matches['NotNone'] += 1
        elif type(iMarkers) == list:
            for iMarker in iMarkers:
                submatches = iMarker().peekmatch(line.txt)
                matches[None] += submatches[None]
                matches['NotNone'] += submatches['NotNone']
        assert(matches[None] <= 1)
        assert(matches['NotNone'] <= 1)
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
                keys = iMarkers.keys()
                notNoneKeys = set(keys) - {None}
                # try matching notNoneKeys
                matchObj = None
                for key in notNoneKeys:
                    pattern = r'(%s)\s*:\s*(%s)' % tuple(key.split(':'))
                    matchObj = re.match(pattern, line.txt)
                    if matchObj:
                        if 'target' in iMarkers[key] and iMarkers[key]['target'] == None:
                            break
                        attr = matchObj.group(1)
                        val = matchObj.group(2)
                        if 'mode' in iMarkers[key] and iMarkers[key]['mode'] == 'append':
                            if attr not in self.attribs:
                                self.attribs[attr] = []
                            self.attribs[attr].append(val)
                        else:
                            self.attribs[attr] = val
                        break
                # if no match and if None is a key
                if not matchObj:
                    if None in keys:
                        attr = iMarkers[None]['target']
                        val = line.txt
                        key = None
                        if 'mode' in iMarkers[key] and iMarkers[key]['mode'] == 'append':
                            if attr not in self.attribs:
                                self.attribs[attr] = []
                            self.attribs[attr].append(val)
                        else:
                            self.attribs[attr] = val
                    else:
                        raise Exception('No matching case found at line %d' % (line.idx + 1))
            elif type(iMarkers) == list:
                if len(iMarkers) == 0:
                    raise Exception('List found empty. Put some subblock classes here')
                matches = { None: [], 'NotNone': []}
                for iMarker in iMarkers:
                    submatches = iMarker().peekmatch(line)
                    if submatches[None]:
                        matches[None].append(iMarker)
                    if submatches['NotNone']:
                        matches['NotNone'].append(iMarker)
                assert(len(matches[None]) <= 1)
                assert(len(matches['NotNone']) <= 1)
                matched = None
                if matches['NotNone']:
                    matched = matches['NotNone'][0]
                elif matches[None]:
                    matched = matches[None][0]
                if matched == None:
                    raise Exception("Line doesn't match any possibility")
                subblock = matched()
                subblock.indentLevel = line.indentLevel
                idx = subblock.parse(lines, startIdx=idx) - 1 # because we had added +1 in the while loop
                self.subblocks.append(subblock)
            else:
                raise Exception("FATAL ERROR: Unexpected type. 'dict' or 'list' type was expected.")
        return idx # this is the length processed

