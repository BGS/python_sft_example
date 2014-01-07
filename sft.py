# -*- coding: utf-8 -*-

"""
Author: Blaga Gabriel
Lang: Python

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import ConfigParser
import time
import os
import paramiko
import sys
import shutil

from PyQt4 import QtCore
from PyQt4 import QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class SFTProtocol(QtCore.QThread):
    sigConnected = QtCore.pyqtSignal(int)

    def __init__(self, host, username, password, parent=None):
        super(SFTProtocol, self).__init__(parent)
        
        self.host = host
        self.username = username
        self.password = password
        self.client = None
        
    def run(self):
        transport = paramiko.Transport((self.host,22))
        transport.connect(username = self.username, password = self.password)
        self.proto = paramiko.SFTPClient.from_transport(transport)
        self.sigConnected.emit(0)
        
    def get_proto(self):
        return self.proto

    def close_con(self):
        self.proto.close()

class SFTPushFile(QtCore.QThread):
    sigArchive = QtCore.pyqtSignal()
    sigProgress = QtCore.pyqtSignal(int, int)
    sigFinished = QtCore.pyqtSignal(int)

    def __init__(self, localpath, remotepath, proto, parent=None):
        super(SFTPushFile, self).__init__(parent)
        
        self.localpath = localpath
        self.remotepath = remotepath
        self.proto = proto

    def run(self):
        try:
            if type(self.localpath).__name__=='list':
                for i in self.localpath:
                    if os.path.isdir(i) and os.path.exists(i):
                        dirname = os.path.dirname('%s/'%i)
                        self.sigArchive.emit()
                        arch = shutil.make_archive(os.path.join('%s/' % os.path.dirname(sys.argv[0]), dirname), "zip", i)     
                        self.proto.put(arch,  '/%s/%s' % (self.remotepath, os.path.basename(arch)), self.sigProgress.emit)
                        os.remove(arch)
                        self.sigFinished.emit(0)
                
                    elif os.path.exists(i):
                        fname = os.path.basename(i)
                        self.proto.put(i, '/%s/%s' % (self.remotepath, fname), self.sigProgress.emit)
                        self.sigFinished.emit(0)
            
            else:
                if os.path.isdir(self.localpath) and os.path.exists(self.localpath):
                    dirname = os.path.dirname('%s/'%self.localpath)
                    arch = shutil.make_archive(os.path.join('%s/' % os.path.dirname(sys.argv[0]), dirname), "zip", self.localpath)     
                    self.proto.put(arch,  '/%s/%s' % (self.remotepath, os.path.basename(arch)), self.sigProgress.emit)
                    self.sigFinished.emit(0)
                
                elif os.path.exists(self.localpath):
                    fname = os.path.basename(self.localpath)
                    self.proto.put(self.localpath, '/%s/%s' % (self.remotepath, fname), self.sigProgress.emit)
                    self.sigFinished.emit(0)

        except Exception, e:
            print e
            self.sigFinished.emit(1)

class SFTGetFile(QtCore.QThread):
    sigProgress = QtCore.pyqtSignal(int, int)
    sigFinished = QtCore.pyqtSignal(int)

    def __init__(self, localpath, remotepath, proto, parent=None):
        super(SFTGetFile, self).__init__(parent)

        self.localpath = localpath
        self.remotepath = remotepath
        self.proto = proto

    def run(self):
        try:
            if type(self.localpath).__name__=='list':
                for i in self.localpath:
                    
                    self.proto.get(i, "%s/%s" % (os.path.dirname(sys.argv[0]), os.path.basename(i)), self.sigProgress.emit)
                    self.sigFinished.emit(0)
            else:
                self.proto.get(self.remotepath, self.localpath, self.sigProgress.emit)
                self.sigFinished.emit(0)
        except Exception, e:
            print e
            self.sigFinished.emit(1)

class SFTListDir(QtCore.QThread):
    sigFinished = QtCore.pyqtSignal(int)

    def __init__(self, path, proto, parent=None):
        super(SFTListDir, self).__init__(parent)

        self.path = path
        self.proto = proto
        self.dir_content = []

    def run(self):
        try:
            list_dir = self.proto.listdir(self.path)
        except IOError:
            self.proto.mkdir(self.path, 511)
               
                
        for f in list_dir:
            self.dir_content.append('%s/%s' % (self.path , f))

        self.sigFinished.emit(0)
        
    def get_dir_content(self):
        return self.dir_content


class SFTRm(QtCore.QThread):
    sigFinished = QtCore.pyqtSignal(int)

    def __init__(self, path, proto, parent=None):
        super(SFTRm, self).__init__(parent)

        self.proto = proto
        self.path = path

    def run(self):
        try:
            if type(self.path).__name__=='list':
                for p in self.path:
                    self.proto.remove("%s" %p)
                self.sigFinished.emit(0)
            else:
                self.proto.remove("%s" %self.path)
                self.sigFinished.emit(2)
        except Exception, e :
            print e
            self.sigFinished.emit(1)
        
class CustomListWidget(QtGui.QListWidget):
  def __init__(self, parent):
    super(CustomListWidget, self).__init__(parent)
    self.upload_list = []
    self.setAcceptDrops(True)
    self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
 
  def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
      event.acceptProposedAction()
    else:
      super(CustomListWidget, self).dragEnterEvent(event)
 
  def dragMoveEvent(self, event):
    super(CustomListWidget, self).dragMoveEvent(event)
 
  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      for url in event.mimeData().urls():
          item = str(url.path())
          item = item.strip()
          item = item.split('/')
          item = '/'.join(item[1:])
          self.addItem(item)
          self.upload_list.append(item)
      event.acceptProposedAction()
    else:
      super(CustomListWidget,self).dropEvent(event)

  def remove_file_from_list(self, index):
      self.upload_list.pop(index)

  def clear_list(self):
      self.upload_list = []
        
  def get_upload_list(self):
     return self.upload_list
      
class Ui_MainWindow(QtGui.QMainWindow):
    def setupUi(self, MainWindow):
        QtGui.QMainWindow.__init__(self)
        self.auth_data = {}
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(475, 300)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName(_fromUtf8("centralWidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(self.centralWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.centralWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.listWidget = CustomListWidget(self.centralWidget)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.listWidget, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.on_context_menu)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.gridLayout.addWidget(self.listWidget, 1, 0, 1, 1)
        self.listWidget_2 = QtGui.QListWidget(self.centralWidget)
        self.listWidget_2.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.listWidget_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.listWidget_2, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.on_context_menu2)
        self.listWidget_2.setObjectName(_fromUtf8("listWidget_2"))
        self.gridLayout.addWidget(self.listWidget_2, 1, 1, 1, 1)
        self.pushButton_2 = QtGui.QPushButton(self.centralWidget)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.gridLayout.addWidget(self.pushButton_2, 2, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(self.centralWidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 2, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 475, 21))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        self.menuConfig = QtGui.QMenu(self.menuBar)
        self.menuConfig.setObjectName(_fromUtf8("menuConfig"))
        self.menuUsername = QtGui.QMenu(self.menuBar)
        self.menuUsername.setObjectName(_fromUtf8("menuUsername"))
        self.menuPassword = QtGui.QMenu(self.menuBar)
        self.menuPassword.setObjectName(_fromUtf8("menuPassword"))
        self.menuConnect = QtGui.QMenu(self.menuBar)
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        MainWindow.setStatusBar(self.statusBar)
        self.connect_actions()
     
        self.contMenu1 = QtGui.QMenu(self)
        
        self.upload_selected = QtGui.QAction('Upload Selected File(s)', self)
        self.clear_action = QtGui.QAction('Clear List', self)
        self.clear_selected = QtGui.QAction('Clear Selected File(s) from List', self)
        
        self.contMenu1.addAction(self.upload_selected)
        self.contMenu1.addAction(self.clear_selected)
        self.contMenu1.addAction(self.clear_action)
       
        
        self.clear_action.triggered.connect(self.clear_upload_list)
        self.upload_selected.triggered.connect(self.uploadSelectedItems)
        self.clear_selected.triggered.connect(self.clearSelectedItems)
        
        self.contMenu2 = QtGui.QMenu(self)
        self.download_selected_action = QtGui.QAction('Download Selected File(s)', self)
        self.bulk_action = QtGui.QAction('Download all Files', self)
        self.remove_selected_action = QtGui.QAction("Remove Selected File(s)", self)
        self.bulk_remove = QtGui.QAction('Remove all Files from Storage', self)

        self.contMenu2.addAction(self.download_selected_action)
        self.contMenu2.addAction(self.bulk_action)
        self.contMenu2.addAction(self.remove_selected_action)
        self.contMenu2.addAction(self.bulk_remove)

        self.bulk_remove.triggered.connect(self.bulk_remove_files_from_server)
        self.bulk_action.triggered.connect(self.bulk_download_from_server)
        self.download_selected_action.triggered.connect(self.downloadSelectedItems)
        self.remove_selected_action.triggered.connect(self.removeSelectedItems)
                                           
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
                                           
        self.ini_parse()
        self.init_server_conn()
    
    def uploadSelectedItems(self):
        file_list = self.listWidget.get_upload_list()
        upload_list = []
        items = self.listWidget.count()
        self.rangedList = range(items)
        self.rangedList.reverse()
        for i in self.rangedList:
            if self.listWidget.isItemSelected(self.listWidget.item(i))==True:
                upload_list.append(file_list[i])

        self.push_worker = SFTPushFile(upload_list, self.remote_dir, self.proto)

        self.push_worker.sigArchive.connect(self.archive_notice)
        self.push_worker.sigProgress[int, int].connect(self.upload_callback)
        self.push_worker.sigFinished[int].connect(self.finishedCallback)

        if not self.push_worker.isRunning():
            self.push_worker.start()
    
    def downloadSelectedItems(self):
        download_list = []
        items = self.listWidget_2.count()
        self.rangedList = range(items)
        self.rangedList.reverse()
        for i in self.rangedList:
            if self.listWidget_2.isItemSelected(self.listWidget_2.item(i))==True:
                download_list.append(str(self.listWidget_2.item(i).text()))
        
        self.get_worker = SFTGetFile(download_list, None, self.proto)
        self.get_worker.sigProgress[int,int].connect(self.download_callback)
        self.get_worker.sigFinished[int].connect(self.download_finished_callback)
        if not self.get_worker.isRunning():
            self.get_worker.start()


    def removeSelectedItems(self):
        remove_list_text = []
        items = self.listWidget_2.count()
        self.rangedList = range(items)
        self.rangedList.reverse()
        for i in self.rangedList:
            if self.listWidget_2.isItemSelected(self.listWidget_2.item(i))==True:
                remove_list_text.append(str(self.listWidget_2.item(i).text()))
                self.listWidget_2.takeItem(i)
        self.remove_worker = SFTRm(remove_list_text, self.proto)
        self.remove_worker.sigFinished[int].connect(self.server_remove_callback)

        if not self.remove_worker.isRunning():
            self.remove_worker.start()


    def clearSelectedItems(self):
        items = self.listWidget.count()
        rangedList = range(items)
        rangedList.reverse()
        for i in rangedList:
            if self.listWidget.isItemSelected(self.listWidget.item(i))==True:
                self.listWidget.takeItem(i)
                self.listWidget.remove_file_from_list(i)
        
        
    def ini_parse(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('sft.ini')

        self.host = self.config.get('SFT', 'host')
        self.username = self.config.get('SFT', 'username')
        self.password = self.config.get('SFT', 'password')
        self.remote_dir = self.config.get('SFT', 'remote_dir')
        
    def init_server_conn(self):
        self.conn_worker = SFTProtocol(self.host, self.username, self.password)
        self.conn_worker.sigConnected[int].connect(self.connection_callback)
        if not self.conn_worker.isRunning():
            self.conn_worker.start()
            
    def connection_callback(self, rtrn):
        if rtrn == 0:
            self.statusBar.showMessage("Connected to remote server !", 0)
            self.proto = self.conn_worker.get_proto()
        else:
            self.statusBar.showMessage("Connection with remote server failed !", 0)
        
    def on_context_menu(self, point):
        self.point = point
        self.contMenu1.exec_(self.listWidget.mapToGlobal(point))
        
    def on_context_menu2(self, point):
        self.point = point
        self.contMenu2.exec_(self.listWidget_2.mapToGlobal(point))
                                         
    def connect_actions(self):
        self.pushButton_2.clicked.connect(self.bulk_upload_files)
        self.pushButton.clicked.connect(self.get_remote_files)
        self.menuConfig = QtGui.QAction('Host', self.menuBar)
        self.menuUsername = QtGui.QAction('Username', self.menuBar)
        self.menuPassword = QtGui.QAction('Password', self.menuBar)
        self.menuConnect = QtGui.QAction('Connect', self.menuBar)

        self.menuBar.addAction(self.menuConfig)
        self.menuBar.addAction(self.menuUsername)
        self.menuBar.addAction(self.menuPassword)
        self.menuBar.addAction(self.menuConnect)
        
        self.menuConfig.triggered.connect(self.sethost)
        self.menuUsername.triggered.connect(self.setusername)
        self.menuPassword.triggered.connect(self.setpassword)
        self.menuConnect.triggered.connect(self.reconnect)

    def reconnect(self):
        self.ini_parse()
        self.init_server_conn()

    def clear_upload_list(self):
        self.listWidget.clear()
        self.listWidget.clear_list()

    def server_remove_callback(self, rtrn):
        if rtrn == 2:
            self.statusBar.showMessage("File(s) Deleted from Storage!", 0)
        elif rtrn == 0:
            self.statusBar.showMessage("File(s) Deleted from Storage!", 0)
        
    def download_callback(self, size, fsize):
        self.statusBar.showMessage("Downloaded blocks: %s : %s" % (size, fsize),0 )
        
    def upload_callback(self, size, fsize):
        self.statusBar.showMessage("Uploaded blocks: %s : %s" % (size, fsize),0 )

    def bulk_upload_files(self):
        file_list = self.listWidget.get_upload_list()
        
        self.push_worker = SFTPushFile(file_list, self.remote_dir, self.proto)
        
        self.push_worker.sigArchive.connect(self.archive_notice)
        self.push_worker.sigProgress[int,int].connect(self.upload_callback)
        self.push_worker.sigFinished[int].connect(self.finishedCallback)
        
        if not self.push_worker.isRunning():
            self.push_worker.start()


    def archive_notice(self):
        self.statusBar.showMessage("Folder detected, compressing before send!", 0)

    def finishedCallback(self, rtrn):
        if rtrn == 0:
            self.statusBar.showMessage("Files sent to storage!", 0)
        else:
            self.statusBar.showMessage("An Error Occured!",0)
            
        
    def get_remote_files(self):

        self.dir_worker = SFTListDir(self.remote_dir, self.proto)

        self.dir_worker.sigFinished[int].connect(self.listDirCallback)

        if not self.dir_worker.isRunning():
            self.dir_worker.start()
            

    def listDirCallback(self, rtrn):
        if rtrn == 0:
            self.statusBar.showMessage("All Good fetching Storage Data!")
            self.remote_list = self.dir_worker.get_dir_content()
            self.listWidget_2.clear()
            self.remote_file_list = []
            for d in self.remote_list:
                self.remote_file_list.append(d)
                self.listWidget_2.addItem(d)
            
        else:
            self.statusBar.showMessage("Something went wrong ...")
            
        
        
    def bulk_download_from_server(self):
        self.get_worker = SFTGetFile(self.remote_file_list, None, self.proto)
        self.get_worker.sigProgress[int,int].connect(self.download_callback)
        self.get_worker.sigFinished[int].connect(self.download_finished_callback)
        if not self.get_worker.isRunning():
            self.get_worker.start()


        
    def download_finished_callback(self, rtrn):
        if rtrn == 0:
            self.statusBar.showMessage("Download completed!",0)
        else:
            self.statusBar.showMessage("Oops something went wrong!", 0)
            

    def bulk_remove_files_from_server(self):
        self.remove_worker = SFTRm(self.remote_file_list, self.proto)
        self.remove_worker.sigFinished[int].connect(self.bulk_remove_callback)

        if not self.remove_worker.isRunning():
            self.remove_worker.start()
                                           
    def bulk_remove_callback(self, rtrn):
        if rtrn == 0:
            self.statusBar.showMessage('Purged all Files from Storage!')
            self.remote_file_list = []
            self.listWidget_2.clear()
        else:
            self.statusBar.showMessage('Oops Something went wrong!')

                
    def sethost(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Config', 'Hostname:')
        if ok:
            self.auth_data['host'] = text
            self.config.set('SFT', 'host', text)
            with open('sft.ini', 'wb') as cfg:
                self.config.write(cfg)
            
            
    def setusername(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Config', 'Username:')
        if ok:
            self.auth_data['username'] = text
            self.config.set('SFT', 'username', text)
            with open('sft.ini', 'wb') as cfg:
                self.config.write(cfg)

            
    def setpassword(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Config','Password:')
        if ok:
            self.auth_data['password'] = text
            self.config.set('SFT', 'password', text)
            with open('sft.ini', 'wb') as cfg:
                self.config.write(cfg)
                
    def close_server_con(self):
        self.proto.close()
        
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("SFTP", "SFT", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Local File Paths", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Remote File List", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("MainWindow", "Upload Local Paths", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("MainWindow", "Get Remote File List", None, QtGui.QApplication.UnicodeUTF8))

def cfg_checkup():
    config = ConfigParser.ConfigParser()
    if not os.path.exists('sft.ini'):
        config.add_section('SFT')
        config.set('SFT', 'host', 'xx.xx.xx.xx')
        config.set('SFT', 'username', 'root')
        config.set('SFT', 'password', 'password')
        config.set('SFT', 'remote_dir', '/root/sft_storage')

        with open('sft.ini', 'wb') as cfg:
            config.write(cfg)
            
          
    
class MainWindow(QtGui.QMainWindow):
    def __init__(self, ui, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = ui
        
    def closeEvent(self, event):
        self.ui.close_server_con()
        QtGui.QMainWindow.closeEvent(self, event)
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    cfg_checkup()
    ui = Ui_MainWindow()
    MainWindow = MainWindow(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

