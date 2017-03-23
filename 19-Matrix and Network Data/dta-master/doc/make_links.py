#
# this is hacky but I couldn't find an easy way to do it
#

import re, shutil

if __name__ == '__main__':

    # filenames -> [ (regex1, substr1), (regex2, substr2), ...]
    subsitutions = {r"_build\html\script_importFullSanFranciscoNetworkDataset.html":
                    [(re.compile(r"[\\]scripts[\\](\w+).py"), '\scripts\<a href="script_\g<1>.html">\g<1>.py</a>')],
                    r"_build\html\script_createSFNetworkFromCubeNetwork.html":
                    [(re.compile(r'(<span class="n">sanfranciscoScenario</span><span class="o">.</span><span class="n">)(\w+)(</span>)'),
                      '<a href="_generated/dta.DynameqScenario.html#dta.DynameqScenario.\g<2>">\g<1>\g<2>\g<3></a>'),
                     (re.compile(r'(<span class="n">sanfranciscoDynameqNet</span><span class="o">.</span><span class="n">)(\w+)(</span>)'),
                      '<a href="_generated/dta.Network.html#dta.Network.\g<2>">\g<1>\g<2>\g<3></a>')],
                    r"_build\html\index.html":
                    [(re.compile(r'<img alt="SFCTA usage of DTA Anyway" src="_images/DtaAnywayFlow_470w\d*.png" />'),
                      '<a id="link1" href="script_createSFNetworkFromCubeNetwork.html"></a>\n' +
                      '<a id="link2" href="script_importTPPlusTransitRoutes.html"></a>\n' +
                      '<a id="link3" href="script_importExcelSignals.html"></a>\n' +
                      '<a id="link4" href="script_importUnsignalizedIntersections.html"></a>\n' +
                      '<a id="link5" href="script_importCubeDemand.html"></a>\n' +
                      '<a id="link6" href="script_attachCountsFromCountDracula.html"></a>\n')]
                    }     
    
    for infilename in subsitutions.keys():
        
        outfile = open("output.html", "w")
        for line in open(infilename, "r"):

            for (regex, substr) in subsitutions[infilename]:
                oldline = line
                (line, count) = regex.subn(substr, line)
                if count>0:
                    print "make_links: %s" % infilename
                    print "  was: ", oldline
                    print "  new: ", line
        
            outfile.write(line)
        outfile.close()
    
        shutil.move("output.html", infilename)