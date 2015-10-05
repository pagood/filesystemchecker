import time
freeBlockList = [0] * 10000
def getFreeList():
    path = '/FS/fusedata.'
    freeList = []
    for i in range(1,26):
        f = open(path + str(i))
        s = f.read()
        f.close()
        freeList += s.split(',')
    return freeList

def getSupDic(s):
    dic = {}
    s = s[1:len(s) - 1]
    s = s.replace(' ','')
    l = s.split(',')
    for i in l:
        temp = i.split(':')
        dic[temp[0]] = int(temp[1])
    return dic

#problem no coma between indirect and location
def getFileDic(s):
    dic = {}
    s = s[1:len(s) - 1]
    s = s.replace(' ','')
    l = s.split(',')
    for i in l:
        temp = i.split(':')
        dic[temp[0]] = int(temp[1])
    return dic

def getFileDic2(s):
    dic = {}
    s = s[1:len(s) - 1]
    s = s.replace(' ','',8)
    l = s.split(',',8)
    for i in range(len(l) - 1):
        temp = l[i].split(':')
        dic[temp[0]] = int(temp[1])
    t = l[len(l) - 1].split(' ')
    for i in t:
        temp = i.split(':')
        dic[temp[0]] = int(temp[1])
    return dic

def getDirDic(s):
    dic = {}
    dic['dic_file'] = {}
    dic['dic_dir'] = {}
    s = s[1:len(s) - 1]
    s = s.replace(' ','')
    l = s.split(',',8)
    for i in range(len(l) - 1):
        temp = l[i] .split(':')
        dic[temp[0]] = int(temp[1])
    ftid = l[len(l) - 1]
    ftid = ftid.replace('filename_to_inode_dict:','')
    ftid = ftid[1:len(ftid) - 1]
    l_ftid = ftid.split(',')
    for i in l_ftid:
        temp = i.split(':')
        if temp[0] == 'f':
            dic['dic_file'][temp[1]] = int(temp[2])
        else:
            dic['dic_dir'][temp[1]] = int(temp[2])
    return dic
def correctHelper(inode):
    dd = inode.pop('dic_dir')
    df = inode.pop('dic_file')
    ftid = {}
    ftid['filename_to_inode_dict'] = {}
    for k in dd:
        ftid['filename_to_inode_dict']['d:' + k] = dd[k]
    for k in df:
        ftid['filename_to_inode_dict']['f:' + k] = df[k]
    newFtid = str(ftid)
    newFtid = newFtid.replace("'",'')
    newInode = str(inode)
    newInode = newInode.replace("'",'')
    newInode = newInode[0:len(newInode) - 1]
    newInode += ','
    newFtid = newFtid[1:len(newFtid) - 1]
    newInode += newFtid
    newInode += '}'
    return newInode

def newFreeList(l):
    res = []
    for i in l:
	##i/400 is the block num
	while (int(int(i) / 400)) + 1 > len(res):
		temp = []
		res.append(temp)
	res[int(int(i)/400)].append(int(i))
    return res

def checkDir(block,parent):
    global freeBlockList
    valid = True
    path = '/FS/fusedata.'
    f = open(path + str(block))
    s = f.read()
    f.close()
    inode = getDirDic(s)
    #check time
    if inode['atime'] > time.time() or inode['ctime'] > time.time() or inode['mtime'] > time.time():
        print('the time of Directory in block %d is not correct'%block)
        valid = False
        #correct in file
        if inode['atime'] > time.time():
            inode['atime'] = int(time.time())
        if inode['mtime'] > time.time():
            inode['mtime'] = int(time.time())
        if inode['ctime'] > time.time():
            inode['ctime'] = int(time.time())
    #link count is correct
    if inode['linkcount'] != len(inode['dic_dir']) + len(inode['dic_file']) :
        print('the linkcount of Directory in block %d is not correct'%block)
        valid = False
        #correct in file
        inode['linkcout'] = len(inode['dic_dir']) + len(inode['dic_file'])
    #check current and parent
    if '.' not in inode['dic_dir'] or '..' not in inode['dic_dir']:
        print('Directory in block %d does not contain . or ..'%block)
        valid = False
        #correct in file
        if '.' not in inode['dic_dir']:
            inode['dic_dir']['.'] = block
        if '..' not in inode['dic_dir']:
            inode['dic_dir']['..'] = parent
    else:
        if inode['dic_dir']['.'] != block or inode['dic_dir']['..'] != parent:
            print('number of . or .. of Directory in block %d is not correct'%block)
            valid = False
            #correct in file
            inode['dic_dir']['.'] = block
            inode['dic_dir']['..'] = parent
    #recursive check file and dir
    for file in inode['dic_file']:
        freeBlockList[inode['dic_file'][file]] = 1
        checkFile(inode['dic_file'][file])
    for directory in inode['dic_dir']:
        if directory != '.' and directory != '..':
            freeBlockList[inode['dic_dir'][directory]] = 1
            checkDir(inode['dic_dir'][directory],block)
    ###correct into file
    if not valid:
        newInode = correctHelper(inode)
        path = '/FS/fusedata.'
        f = open(path + str(block),'wb')
        f.write(newInode)
        f.close()
    
def checkFile(block):
    pointer = True
    global freeBlockList
    #use to check size
    valid = True
    path = '/FS/fusedata.'
    f = open(path + str(block))
    s = f.read()
    f.close()
    if len(s.split(',')) == 9:
        inode = getFileDic2(s)
    else:
        inode = getFileDic(s)
    #check time
    if inode['atime'] > time.time() or inode['ctime'] > time.time() or inode['mtime'] > time.time():
        print('the time of file in block %d is not correct'%block)
        if inode['atime'] > time.time():
            inode['atime'] = int(time.time())
        if inode['ctime'] > time.time():
            inode['ctime'] = int(time.time())
        if inode['mtime'] > time.time():
            inode['mtime'] = int(time.time())
    location = inode['location']
    freeBlockList[location] = 1
    f = open(path + str(location))
    c = f.read()
    f.close()
    temp = c.split(',')
    try:
        for i in temp:
            freeBlockList[int(i)] = 1
        if len(temp) > 1:
            if inode['indirect'] != 1:
                inode['indirect'] = 1
                print('indirect of file in block %d is not correct'%block)
    except ValueError:
        pointer = False
    #check the size is valid
    if inode['indirect'] == 0:
    #only one block
        if inode['size'] > 4096:
            valid = False
            print('the size of file in block %d is not correct,its indirect should be 1'%block)
    else:
    #more than one block
        if inode['size'] < 4096 * len(temp) - 1:
            if inode['size'] < 4096:
                inode['indirect'] = 0
            valid = False
            print('the size of file in block %d is not correct,the number of blocks it used is too big'%block)
        if inode['size'] > 4096 * len(temp):
            valid = False
            print('the size of file in block %d is not correct,the number of blocks it used is too small'%block)
    if not valid:
    #correct in file
        path = '/FS/fusedata.'
        f = open(path + str(block),'wb')
        f.write(str(inode).replace("'",''))
        f.close()
def writeHelper():
    global freeBlockList
    res = []
    for i in range(len(freeBlockList)):
        if freeBlockList[i] == 0:
            res.append(i)
    return res

def check():
    #use to check free list
    print('begin to check,the error message is :')
    global freeBlockList
    a = True
    b = True
    path = '/FS/fusedata.'
    f = open(path + str(0))
    superBlock = f.read()
    f.close()
    supInode = getSupDic(superBlock)
    if supInode['devId'] != 20:
        print('the device ID is not correct,the checker would exit')
    else:    
        #check time here a m c
        if supInode['creationTime'] > time.time():
            print('the creationTime of file system is not correct')
            supInode['creationTime'] = int(time.time())
        if supInode['devId'] != 20:
            print('the device ID is not correct')
            supInode['devId'] = 20
        #correct superblock
        f = open(path + str(0),'wb')
        f.write(str(supInode).replace("'",''))
        f.close()
        for i in range(26):
            freeBlockList[i] = 1
        freeList = getFreeList()
        freeBlockList[26] = 1
        checkDir(26,26)
        tempFreeList = []
        for i in range(len(freeBlockList)):
            if freeBlockList[i] == 1:
                if ' ' + str(i) in freeList:
                    #used block in freelist
                    b = False
            else:
                tempFreeList.append(i)
                if ' ' + str(i) not in freeList:
                    #free block not in list
                    a = False
        if not a:
            print('free block list does not contain ALL of the free blocks')
        if not b:
            print('there are files/directories stored on items listed in the free block list')
        new_freeList = newFreeList(tempFreeList)
        #write new free list into file
        for i in range(len(new_freeList)):
            f = open(path + str(i + 1),'wb')
            content = str(new_freeList[i])[1:len(str(new_freeList[i])) - 1]
            f.write(' ' + content)
            f.close()
        
if __name__ == '__main__':
    check()
