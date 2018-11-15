from silx.gui import qt
from silx.gui.plot import Plot1D, Plot2D
import numpy as np
import pandas as pd
import glob
import multiprocessing as mp
import tifffile as tif
import natsort
import os, sys, re
from ui_PPXUV import Ui_MainWindow

qapp = qt.QApplication([])

class MainWindow(qt.QMainWindow):
    #wSignal = qtSignal()
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        self.u = Ui_MainWindow()
        self.u.setupUi(self)

        self.datDir = "/Users/uemura/OneDrive/UU/Urbana-Champaign/20181112 Ti-doped Fe2O3 (10%)/"
        self.trimRange = [200, 300]
        self.TopPP = glob.glob(self.datDir + '/' + 'GCR1_10%TiO2inFe2O3_1.3mW400nm_600ms1f_20181112-1_r*_s*Top_PP.txt')
        self.TopPr = glob.glob(self.datDir + '/' + 'GCR1_10%TiO2inFe2O3_1.3mW400nm_600ms1f_20181112-1_r*_s*Top_Pr.txt')
        self.BotPP = glob.glob(self.datDir + '/' + 'GCR1_10%TiO2inFe2O3_1.3mW400nm_600ms1f_20181112-1_r*_s*Bot_PP.txt')
        self.BotPr = glob.glob(self.datDir + '/' + 'GCR1_10%TiO2inFe2O3_1.3mW400nm_600ms1f_20181112-1_r*_s*Bot_Pr.txt')
        self.runNum = -1
        self.scanNum = -1
        self.thrhld = 0.004
        self.fcommon = 'GCR1_10%TiO2inFe2O3_1.3mW400nm_600ms1f_20181112-1'
        self.I = 0
        self.timer = qt.QBasicTimer()
        
        self.plot = Plot2D()
        self.plot.show()
        self.show()

        def openDirectory():
            self.datDir = self.u.tB_Directory.toPlainText()
            dat_dir = os.environ["HOME"]
            if self.datDir != "" and os.path.isdir(self.datDir):
                dat_dir = self.datDir
            FO_dialog = qt.QFileDialog()
            directory = FO_dialog.getExistingDirectory(None,
                                                       caption="Select a directory",
                                                       directory=dat_dir)
            if directory:
                self.u.tB_Directory.clear()
                self.u.tB_Directory.append(directory)

        # def convert():
            # print (self.u.tE_header.toPlainText())

        self.u.pB_open.clicked.connect(openDirectory)
        self.u.pB_convert.clicked.connect(self.DoAction)

    def closeEvent(self, event):
        print ("Closing")
        self.plot.destroy()
        self.destroy()
        qapp.quit()

    def DoAction(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.datDir = self.u.tB_Directory.toPlainText()
            self.trimRange = [self.u.sB_low.value(), self.u.sB_high.value()]
            if os.path.isdir(self.datDir) and self.u.tE_header.toPlainText():
                self.u.progressBar.setMinimum(self.u.sB_start.value())
                self.u.progressBar.setValue(self.u.sB_start.value())
                # self.u.progressBar.setValue(self.u.sB_start)
                self.N = self.u.progressBar.value()
                self.u.progressBar.setMaximum(self.u.sB_End.value())
                self.timer.start(1, self)
            else:
                msg = qt.QMessageBox()
                msg.setText('Something wrong happened...')
                msg.setWindowTitle("!Error!")
                msg.setDetailedText('The directory or/and File header is/are empty!')
                msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.exec_()
            # print (TopPPs)

    def timerEvent(self, e):
        if self.N <= self.u.progressBar.maximum():
            # print ("Hello")
            self.fcommon = self.u.tE_header.toPlainText()
            TopPPs = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ self.fcommon + '*_' + 'r*_s*Top_PP.txt')
            if re.match(r'.+r(\d+)_s(\d+).+', os.path.basename(natsort.natsorted(TopPPs)[-1])):
                self.scanNum = int(re.match(r'.+r(\d+)_s(\d+).+', os.path.basename(natsort.natsorted(TopPPs)[-1])).group(2))
                self.runNum = int(re.match(r'.+r(\d+)_s(\d+).+', os.path.basename(natsort.natsorted(TopPPs)[-1])).group(1))
                # self.i=self.u.progressBar.value()

                T = {}
                for j in range(1, self.scanNum + 1):
                    T['scan' + str(j)] = []
                for i in range(1, self.runNum + 1):
                    # print (i)
                    self.I = i
                    A = []
                    for j in range(1, self.scanNum + 1):
                        # print(j)
                        A.append(self.trimData(j))
                    # A = p.map(trimData,range(1,glb.scanNum+1))
                    # if all(A):
                    #     pass
                    # else:
                    #     print ('The data does not have good statistics:'+str(i))
                    for j in range(1, self.scanNum + 1):
                        if A[j - 1]:
                            print (j)
                            T['scan' + str(j)].append(self.calcAbs(self.I, j))
                        else:
                            # print(j)
                            pass
                Img = []
                for j in range(1, self.scanNum + 1):
                    Img.append(np.average(T['scan' + str(j)], axis=0))
                tif.imsave(self.datDir +'/'+ 'Run' + str(self.N) + '_tt.tif', np.array(Img))
            self.N +=1
            self.u.progressBar.setValue(self.u.progressBar.value()+1)

    def calcAbs(self,i, J):
        # print (J)
        fs = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ \
                       self.fcommon +'-'+str(self.N)  + '_' + \
                       'r' + str(i) + '_' + 's' + str(J) + '*Top_PP.txt')
        toppp = pd.read_csv(fs[0], names=['I'])['I'].values
        fs = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ \
                       self.fcommon +'-'+str(self.N)  + '_' + \
                       'r' + str(i) + '_' + 's' + str(J) + '*Top_Pr.txt')
        toppr = pd.read_csv(fs[0], names=['I'])['I'].values
        fs = glob.glob(self.datDir + '/'+'Run '+str(self.u.progressBar.value())+'/'+ \
                       self.fcommon +'-'+str(self.N)  + '_' + \
                       'r' + str(i) + '_' + 's' + str(J) + '*Bot_PP.txt')
        botpp = pd.read_csv(fs[0], names=['I'])['I'].values
        fs = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ \
                       self.fcommon +'-'+str(self.N)  + '_' + \
                       'r' + str(i) + '_' + 's' + str(J) + '*Bot_Pr.txt')
        botpr = pd.read_csv(fs[0], names=['I'])['I'].values
        return (-1) * np.log10((toppp - botpp) / (toppr - botpr))

    def trimData(self, J):
        # print (J)
        pret0 = 8
        trimEdge = [300, 420]
        Ftoppp = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ \
                           self.fcommon +'-' + str(self.N) + '_' + 'r' + str(self.I) + '_' + 's' + str(J) + '*Top_PP.txt')
        Ftoppr = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ self.fcommon +'-' +\
                           str(self.N) + '_' + 'r' + str(self.I) + '_' + 's' + str(J) + '*Top_Pr.txt')
        Fboppp = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ self.fcommon +'-' +\
                           str(self.N) + '_' + 'r' + str(self.I) + '_' + 's' + str(J) + '*Bot_PP.txt')
        Fboppr = glob.glob(self.datDir + '/' +'Run '+str(self.u.progressBar.value())+'/'+ self.fcommon +'-' +\
                           str(self.N) + '_' + 'r' + str(self.I) + '_' + 's' + str(J) + '*Bot_Pr.txt')
        if all([len(Ftoppp) > 0, len(Ftoppr) > 0,
                len(Fboppp) > 0, len(Fboppr) > 0]):
            if all([os.stat(Ftoppp[0]).st_size > 1000, os.stat(Ftoppr[0]).st_size > 1000,
                    os.stat(Fboppp[0]).st_size > 1000, os.stat(Fboppr[0]).st_size > 1000]):
                fs = glob.glob(self.datDir + '/' +'Run '+str(self.N)+'/'+ self.fcommon + '-' +str(self.N) + '_' + \
                               'r' + str(self.I) + '_' + 's' + str(J) + '*Top_PP.txt')
                toppp = pd.read_csv(fs[0], names=['I'])['I'].values
                fs = glob.glob(self.datDir + '/' +'Run '+str(self.N)+'/'+ self.fcommon + '-' +str(self.N) + '_' + \
                               'r' + str(self.I) + '_' + 's' + str(J) + '*Top_Pr.txt')
                toppr = pd.read_csv(fs[0], names=['I'])['I'].values
                fs = glob.glob(self.datDir + '/' +'Run '+str(self.N)+'/'+ self.fcommon + '-' +str(self.N) + '_' + \
                               'r' + str(self.I) + '_' + 's' + str(J) + '*Bot_PP.txt')
                botpp = pd.read_csv(fs[0], names=['I'])['I'].values
                fs = glob.glob(self.datDir + '/' +'Run '+str(self.N)+'/'+ self.fcommon + '-' +str(self.N) + '_' + \
                               'r' + str(self.I) + '_' + 's' + str(J) + '*Bot_Pr.txt')
                botpr = pd.read_csv(fs[0], names=['I'])['I'].values
                diff = (-1) * np.log10((toppp - botpp) / (toppr - botpr))
                stdev = np.std(diff[self.trimRange[0]:self.trimRange[1]])
                # print ("stdev:" + str(stdev))
                if J > pret0:
                    if stdev < self.thrhld:
                        return True
                    else:
                        return False
                elif J <= pret0:
                    stdev_edge = np.std(diff[trimEdge[0]:trimEdge[1]])
                    avgEdge = np.average(diff[trimEdge[0]:trimEdge[1]])
                    if stdev < self.thrhld and stdev_edge < self.thrhld and abs(avgEdge) < self.thrhld:
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False

if __name__ == '__main__':
    #plot = Plot1D()  # Create the plot widget

    wid = MainWindow()

    #plot.show()  # Make the plot widget visible
    qapp.exec_()



