##############################################################################################################################################
# SCRIPT NAME : syno_purge_older.py                                                                                                         #
# DESCRIPTION : Purge older files                                                                                                            #
# USE CASE    : Video surveillance                                                                                                           #
# AUTHOR      : https://github.com/paronnax                                                                                                  #
# DATE        : June, 2022                                                                                                                   #
# VERSION     : 1.0                                                                                                                          #
# OS / Python : DSM 7.0.1-42218 / Python 3.8.8                                                                                               #
##############################################################################################################################################

#--------------------------------------------------------MANDATORY LIBRAIRIES----------------------------------------------------------------#
import os
import sys

from argparse import ArgumentParser, Action


#----------------------------------------------------------------CLASSES----------------------------------------------------------------------#
# CLASS : Limit occurence of arguments
class UniqueStore(Action):
    def __call__(self, parser, namespace, values, option_string):
        if getattr(namespace, self.dest, self.default) is not self.default:
            parser.error(f"Argument '{option_string}' appears several times. Please use argument only once.")
        setattr(namespace, self.dest, values)     

# CLASS : Unit size
class SIZE_UNIT():
   BYTES = 1
   KB = 1*1024
   MB = 1*1024*1024
   GB = 1*1024*1024*1024


#---------------------------------------------------------------FUNCTIONS---------------------------------------------------------------------#

# Total size of the path
def get_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def get_files(folder,list_ignore):
    print("Obtaining files")
    list_files = []
    for dirname, dirnames, filenames in os.walk(folder):
        bool_ignore = False
        if list_ignore[0] != "":
            for dir_ignore in list_ignore:
                if dir_ignore in dirname:
                    bool_ignore = True
                    break
        if bool_ignore: continue
        else:
            for filename in filenames:
                list_files.append({
                    "filename" : filename,
                    "full_path": os.path.join(dirname, filename),
                    "size"     : os.stat(os.path.join(dirname, filename)).st_size,
                    "mtime"    : os.stat(os.path.join(dirname, filename)).st_mtime,
                })
    return list_files


def get_older_with_size_limite(list_files, size_to_delete):
    print("Sorts by size down to volume to delete")
    list_to_be_delete = []
    size = 0
    for item in sorted(list_files, key=lambda d: d['mtime']):
        size += item["size"]
        list_to_be_delete.append(item)
        if size > size_to_delete:
            return list_to_be_delete
    print("WARMING - All files will be deleted")
    return list_to_be_delete

def delete(list_files):
    size_deleted = 0
    print("List of deleted files : ")
    for i in list_files:
        size_deleted += i["size"]
        print("\t"+i["filename"])
        os.remove(i["full_path"]) 
    print()
    print("Volume cleaned : "+str(size_deleted/SIZE_UNIT.GB)[:5]+" GB")

def main():
    parser = ArgumentParser()
    parser.add_argument("-d", "--directory", help="Define which directory to purge", required=True, action=UniqueStore)
    parser.add_argument("-l", "--limit", help="Size limit before cleaning", required=True, action=UniqueStore, type=int)
    parser.add_argument("-s", "--size", help="Size to clean", action=UniqueStore, type=int, default=1)
    parser.add_argument("-i", "--ignore", help="Files to ignore", action=UniqueStore, default='')
    # parser.add_argument("-u", "--unit", help="Unit of measurement", action=UniqueStore, choices=['BYTES','KB','MB','GB'], default='GB')
  
    # Handling of missing arguments
    if len(sys.argv) <= 1:
        parser.print_help()
        print("""
    Examples :
    > Purge 5GB in /var/log if size superior than 30GB
    purge_older.py -d /var/log -l 50 -s 5
    > As previous with ignoring .git and store
    purge_older.py -d /var/log -l 50 -s 5 -i '.git;store'
        """)
        sys.exit(0)
    
    # Saving arguments into the variable args
    else: args = parser.parse_args()

    path            = args.directory
    list_dir_ignore = args.ignore.split(";")
    size_limit      = args.limit*SIZE_UNIT.GB
    size_delete     = args.size*SIZE_UNIT.GB

    print("")
    print("---- SUMMARY----")
    print("FOLDER : "+path)
    print("Ignore : "+ str(list_dir_ignore))
    print("Size max : "+str(size_limit/SIZE_UNIT.MB)+" MB")
    print("Size to delete : "+str(size_delete/SIZE_UNIT.MB)+" MB")
    print("---- ----")
    print("")

    if size_limit < get_size(path):
        print("-- STARTING EXECUTION")

        list_files = get_files(path,list_dir_ignore)
        list_files_to_delete = get_older_with_size_limite(list_files, size_delete)

        if len(list_files_to_delete) == 0:
            print("No files to delete")
        else:
            delete(list_files_to_delete)
            pass
    else:
        print("Volume not reached")

    print("")
    print("---- END EXECUTION ----")

if __name__ == "__main__":
    main()