#-------------------------------------------------------------------------------
# Name:        javapkg2srcdir
# Purpose:     move java source to dirs according to package definition
#
# Author:      malong
#
# Created:     16/03/2015
# Copyright:   (c) malong 2015
# Licence:     Free for all
#-------------------------------------------------------------------------------

import os
import re
from optparse import OptionParser
from shutil import ignore_patterns
from shutil import copy2

java_pkg_pattern = re.compile('')

def get_dst_dir_from_java_src(dst, java_src):
    #print dst,java_src
    pkgdirs = ''
    try:
        with open(java_src,'r') as f:
            #print dst,java_src
            for line in f:
                ll = line.strip()
                if ll.startswith('package'):
                    pkgdirs = ll[8:ll.find(';')].strip().replace('.',os.sep)
                    #pkgdirs = ll.strip(';').replace('package','').strip().replace('.',os.sep)
                    #print pkgdirs
                    break
    except:
        pkgdirs = ''
    return os.path.join(dst, pkgdirs)

def copysrcdir(src, dst_top, source=None, ignore=None):
    names = os.listdir(src)

    if source is not None:
        source_names = source(src, names)
    else:
        source_names = set()

    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        try:
            if name in source_names:
                print "read",srcname
                dstdir = get_dst_dir_from_java_src(dst_top, srcname)
                if not os.path.exists(dstdir):
                    os.makedirs(dstdir)
                dstname = os.path.join(dstdir, name)
                print "copy to", dstname
                copy2(srcname, dstname)
            elif os.path.isdir(srcname):
                copysrcdir(srcname, dst_top, source, ignore)
        except Exception as err:
            print '[Error]',err

def copysrcdir2(src, dst_top, source=None, ignore=None, verbose=True):
    f1 = f2 = f3 = 0
    for top, dirs, files in os.walk(src):
        for file in files:
            f1 += 1
            if file.endswith(('.java','.JAVA')):
                f2 += 1
                j_src = os.path.join(top, file)
                if verbose:
                    print "read",j_src
                try:
                    j_dst_dir = get_dst_dir_from_java_src(dst_top, j_src)
                    if not os.path.exists(j_dst_dir):
                        os.makedirs(j_dst_dir)
                    j_dst = os.path.join(j_dst_dir,file)
                    if verbose:
                        print "copy to",j_dst
                    copy2(j_src, j_dst)
                    f3 += 1
                except Exception as err:
                    print '[ERROR]',file,err

    print "src=%s, dst=%s"%(src,dst_top)
    print "Files: Toal=%d, Java=%d, Copied=%d"%(f1,f2,f3)

def main():
    usage = "usage: %prog [options] src_dir dst_dir"
    parser = OptionParser(usage)
    #parser.add_option("-g", "--ignore", dest="ignore", help="Specify ignore file pattern (eg. *.tmp or tmp*)")
    parser.add_option("-q", "--quiet", default = True, action="store_false", dest="verbose", help="Don't print status message to stdout")
    #parser.add_option("-r", "--recursive", default = False, action="store_true", dest="recursive", help="recursively read files in src_dir")

    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")

    #print options
    #copysrcdir(args[0],args[1], source=ignore_patterns('*.java'), ignore=None)
    copysrcdir2(args[0],args[1], source=ignore_patterns('*.java'), ignore=None, verbose=options.verbose)

if __name__ == '__main__':
    main()
