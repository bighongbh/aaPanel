#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具
#-----------------------------

import sys,os
os.chdir('/www/server/panel');
sys.path.append("class/")
if sys.version_info[0] == 2: 
    reload(sys)
    sys.setdefaultencoding('utf-8')
import public,db,time

class backupTools:
    
    def backupSite(self,name,count):
        sql = db.Sql();
        path = sql.table('sites').where('name=?',(name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = public.GetMsg("SITE_NOT_EXIST1",(name,))
            print(u"★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename= backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
        
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        
        if not os.path.exists(filename):
            log = public.GetMsg("SITE_BACK_FILE",(name,))
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',os.path.basename(filename),pid,filename,endDate,os.path.getsize(filename)))
        log = public.GetMsg("SITE_BACKFTP_SUCCESS",(name,str(round(outTime,2))))
        public.WriteLog('TYPE_CRON',log)
        print(u"★["+endDate+"] " + log)
        print(public.GetMsg("KEEP_PART",(count,)))
        print(public.GetMsg("FTP_FILE_NAME")+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=? and filename!=? and filename!=? and filename!=? and filename!=? and filename!=?',('0',pid,'alioss','txcos','upyun','qiniu','ftp')).field('id,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                public.ExecShell("rm -f " + backup['filename']);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(public.GetMsg("FTP_CLEAN_BACK_FILE") + backup['filename'])
                if num < 1: break;
    
    def backupDatabase(self,name,count):
        sql = db.Sql();
        path = sql.table('databases').where('name=?',(name,)).getField('id');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = public.GetMsg("FTP_DB_NOT_EXIST",(name,))
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+".sql.gz"
        
        import re
        mysql_root = sql.table('config').where("id=?",(1,)).getField('mysql_root')
        
        mycnf = public.readFile('/etc/my.cnf');
        rep = "\[mysqldump\]\nuser=root"
        sea = "[mysqldump]\n"
        subStr = sea + "user=root\npassword=" + mysql_root+"\n";
        mycnf = mycnf.replace(sea,subStr)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        public.ExecShell("/www/server/mysql/bin/mysqldump --force --opt " + name + " | gzip > " + filename)
        
        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = public.GetMsg("FTP_DB_BACK",(name,))
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        mycnf = public.readFile('/etc/my.cnf');
        mycnf = mycnf.replace(subStr,sea)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');
        
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,os.path.basename(filename),pid,filename,endDate,os.path.getsize(filename)))
        log = public.GetMsg("FTP_DB_BACK_SUCCESS",(name,str(round(outTime,2))))
        public.WriteLog('TYPE_CRON',log)
        print("★["+endDate+"] " + log)
        print(public.GetMsg("KEEP_PART",(count,)))
        print(public.GetMsg("FTP_FILE_NAME")+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=? and filename!=? and filename!=? and filename!=? and filename!=? and filename!=?',('1',pid,'alioss','txcos','upyun','qiniu','ftp')).field('id,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                public.ExecShell("rm -f " + backup['filename']);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(public.GetMsg("FTP_CLEAN_BACK_FILE") + backup['filename'])
                if num < 1: break;
    
    #备份指定目录
    def backupPath(self,path,count):
        sql = db.Sql();
        startTime = time.time();
        if path[-1:] == '/': path = path[:-1]
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename= backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        os.system("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
                
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = public.GetMsg("FTP_DIR_BACK_FAIL",(path,))
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size',('2',path,'0',filename,endDate,os.path.getsize(filename)))
        log = public.GetMsg("FTP_DIR_BACK_SUCCESS",(path,str(round(outTime,2))))
        public.WriteLog('TYPE_CRON',log)
        print(u"★["+endDate+"] " + log)
        print(public.GetMsg("KEEP_PART",(count,)))
        print(public.GetMsg("FTP_FILE_NAME")+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=? and name=?',('2',0,path)).field('id,filename').select();
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                public.ExecShell("rm -f " + backup['filename']);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(public.GetMsg("FTP_CLEAN_BACK_FILE") + backup['filename'])
                if num < 1: break;
        
    
    def backupSiteAll(self,save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'],save)
        

    def backupDatabaseAll(self,save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'],save)
    
    


if __name__ == "__main__":
    backup = backupTools()
    type = sys.argv[1];
    if type == 'site':
        if sys.argv[2] == 'ALL':
             backup.backupSiteAll( sys.argv[3])
        else:
            backup.backupSite(sys.argv[2], sys.argv[3])
    elif type == 'path':
        backup.backupPath(sys.argv[2],sys.argv[3])
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            backup.backupDatabaseAll(sys.argv[3])
        else:
            backup.backupDatabase(sys.argv[2], sys.argv[3])
    